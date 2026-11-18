#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bot en papel: compra y vende DE MENTIRA con tus reglas y te dice cuánto habrías ganado o perdido.
No toca dinero, no tiene billetera, no puede comprar nada de verdad.
Canal de YouTube: Profesor Diógenes · sección "Bots de Solana", vídeo 17.

    python3 papel.py

Cómo se usa, desde tu bot:
  - Le pegas un contrato                -> "compra" en papel con tu plan (por defecto 0,2 SOL)
  - /plan 0.2 2 50                      -> cada entrada 0,2 SOL · vender al doble (x2) · cortar si cae un 50 %
  - /cartera                            -> lo que tienes abierto y cómo va
  - /balance                            -> todas las operaciones cerradas y el resultado total
  - /cierra <contrato>                  -> vender a mano (en papel) al precio de ahora

Cómo funciona por dentro:
  - Al "comprar" apunta el precio de ese momento (DexScreener, gratis y sin clave) y le suma la comisión.
  - Cada 30 segundos mira el precio de todo lo abierto. Si toca el objetivo, vende; si toca el corte, vende.
    Entre mirada y mirada el precio puede saltarse tu corte: se vende al precio que haya, no al que querías.
  - En cada compra y cada venta descuenta COMISION (3 % por defecto: comisiones, propinas y deslizamiento).
  - Todo queda apuntado en "operaciones.csv".
Esto NO es consejo financiero. Es una herramienta para mirar.
"""
import os, re, csv, json, time, threading
import requests


def cargar_env():
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(ruta):
        for linea in open(ruta, encoding="utf-8"):
            if "=" in linea and not linea.strip().startswith("#"):
                k, v = linea.strip().split("=", 1)
                if v.strip():
                    os.environ.setdefault(k.strip(), v.strip())


cargar_env()
AQUI = os.path.dirname(os.path.abspath(__file__))
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
MI_ID = os.environ.get("TELEGRAM_MI_ID", "").strip()
COMISION = float(os.environ.get("COMISION", "0.03"))        # lo que se pierde en cada compra y en cada venta
CADA = int(os.environ.get("CADA_SEGUNDOS", "30"))
BOT = "https://api.telegram.org/bot%s/" % TOKEN
ESTADO = os.path.join(AQUI, "papel.json")
REGISTRO = os.path.join(AQUI, "operaciones.csv")
DIRECCION = re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b")
cerrojo = threading.Lock()


def estado():
    try:
        return json.load(open(ESTADO))
    except Exception:
        return {"plan": {"sol": 0.2, "objetivo": 2.0, "corte": 50.0}, "abiertas": {}, "cerradas": []}


def guardar(e):
    json.dump(e, open(ESTADO, "w"), indent=1, ensure_ascii=False)


def telegram(metodo, **datos):
    try:
        return requests.post(BOT + metodo, json=datos, timeout=60).json()
    except Exception:
        return {}


def avisar(texto):
    telegram("sendMessage", chat_id=MI_ID, text=texto, parse_mode="HTML", disable_web_page_preview=True)


def precios(contratos):
    """Precio en SOL, símbolo y capitalización de hasta 30 tokens de una vez (DexScreener)."""
    out = {}
    for i in range(0, len(contratos), 30):
        try:
            pares = requests.get("https://api.dexscreener.com/latest/dex/tokens/" + ",".join(contratos[i:i + 30]), timeout=15).json().get("pairs") or []
        except Exception:
            pares = []
        for p in sorted(pares, key=lambda p: float((p.get("liquidity") or {}).get("usd") or 0)):   # se queda el par con más liquidez
            b = p.get("baseToken") or {}
            if b.get("address") in contratos and p.get("priceNative") and (p.get("quoteToken") or {}).get("symbol") in ("SOL", "WSOL"):
                out[b["address"]] = {"precio": float(p["priceNative"]), "simbolo": b.get("symbol") or "?",
                                     "mc": float(p.get("marketCap") or p.get("fdv") or 0)}
    return out


def apuntar(op):
    nuevo = not os.path.exists(REGISTRO)
    with open(REGISTRO, "a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if nuevo:
            w.writerow(["entrada", "salida", "contrato", "simbolo", "sol_puesto", "sol_recuperado", "resultado_sol", "motivo", "multiplo"])
        w.writerow([op["hora"], time.strftime("%Y-%m-%d %H:%M:%S"), op["ca"], op["simbolo"], op["sol"], round(op["recuperado"], 4),
                    round(op["recuperado"] - op["sol"], 4), op["motivo"], round(op["x"], 3)])


def comprar(ca):
    with cerrojo:
        e = estado()
        if ca in e["abiertas"]:
            return "Ese ya lo tienes abierto."
        p = precios([ca]).get(ca)
        if not p:
            return "No encuentro precio en SOL para ese contrato."
        plan = e["plan"]
        e["abiertas"][ca] = {"ca": ca, "simbolo": p["simbolo"], "sol": plan["sol"], "precio": p["precio"], "mc": p["mc"],
                             "tokens": plan["sol"] * (1 - COMISION) / p["precio"],            # la comisión de entrada ya te quita tokens
                             "objetivo": plan["objetivo"], "corte": plan["corte"], "hora": time.strftime("%Y-%m-%d %H:%M:%S")}
        guardar(e)
    return ("📝 COMPRA EN PAPEL · <b>%s</b>\n   %.2f SOL a una capitalización de %.0f $\n   vendo si hace x%.2f · corto si cae un %.0f %%" % (
        p["simbolo"], plan["sol"], p["mc"], plan["objetivo"], plan["corte"]))


def cerrar(e, ca, precio, motivo):
    op = e["abiertas"].pop(ca)
    op["x"] = precio / op["precio"]
    op["recuperado"] = op["tokens"] * precio * (1 - COMISION)                                 # y la de salida, SOL
    op["motivo"] = motivo
    e["cerradas"].append(op); apuntar(op)
    gana = op["recuperado"] - op["sol"]
    return "%s VENTA EN PAPEL · <b>%s</b> · %s\n   el precio hizo x%.2f · pusiste %.2f SOL y recuperas %.3f · <b>%+.3f SOL</b>" % (
        "🟢" if gana > 0 else "🔴", op["simbolo"], motivo, op["x"], op["sol"], op["recuperado"], gana)


def vigilar():
    while True:
        time.sleep(CADA)
        with cerrojo:
            e = estado()
            if not e["abiertas"]:
                continue
            ahora = precios(list(e["abiertas"]))
            avisos = []
            for ca, op in list(e["abiertas"].items()):
                p = ahora.get(ca)
                if not p:
                    continue
                x = p["precio"] / op["precio"]
                if x >= op["objetivo"]:
                    avisos.append(cerrar(e, ca, p["precio"], "objetivo alcanzado"))
                elif x <= 1 - op["corte"] / 100:
                    avisos.append(cerrar(e, ca, p["precio"], "corte de pérdidas"))
            guardar(e)
        for a in avisos:
            avisar(a)


def cartera():
    e = estado()
    if not e["abiertas"]:
        return "No tienes nada abierto."
    ahora = precios(list(e["abiertas"]))
    lineas = []
    for ca, op in e["abiertas"].items():
        p = ahora.get(ca)
        lineas.append("• <b>%s</b> %s  (%.2f SOL, desde %s)" % (op["simbolo"], "x%.2f" % (p["precio"] / op["precio"]) if p else "sin precio",
                                                               op["sol"], op["hora"][11:16]))
    return "📂 Abiertas %d:\n%s" % (len(lineas), "\n".join(lineas))


def balance():
    e = estado(); c = e["cerradas"]
    if not c:
        return "Todavía no se ha cerrado ninguna operación."
    gan = [o for o in c if o["recuperado"] > o["sol"]]
    puesto = sum(o["sol"] for o in c); vuelto = sum(o["recuperado"] for o in c)
    ultimas = "\n".join("• %s x%.2f · %+.3f SOL · %s" % (o["simbolo"], o["x"], o["recuperado"] - o["sol"], o["motivo"]) for o in c[-8:])
    return ("📊 BALANCE EN PAPEL\n%d operaciones cerradas · %d ganadas (%.0f %%) · %d perdidas\n"
            "puesto %.2f SOL · recuperado %.2f SOL · <b>resultado %+.3f SOL</b>\n(comisión del %.0f %% en cada compra y cada venta)\n\n%s" % (
                len(c), len(gan), 100 * len(gan) / len(c), len(c) - len(gan), puesto, vuelto, vuelto - puesto, 100 * COMISION, ultimas))


def escuchar_bot():
    desde = 0
    while True:
        r = telegram("getUpdates", offset=desde, timeout=50, allowed_updates=["message"])
        for u in r.get("result") or []:
            desde = u["update_id"] + 1
            m = u.get("message") or {}
            chat = (m.get("chat") or {}).get("id")
            quien = str((m.get("from") or {}).get("id"))
            texto = (m.get("text") or "").strip()
            if not chat:
                continue
            if not MI_ID:
                telegram("sendMessage", chat_id=chat, text="Tu número de usuario es %s. Ponlo en TELEGRAM_MI_ID del .env y vuelve a arrancar." % quien)
                continue
            if quien != MI_ID:
                continue
            p = texto.replace(",", ".").split()
            if texto.startswith("/plan"):
                with cerrojo:
                    e = estado()
                    try:
                        e["plan"] = {"sol": float(p[1]), "objetivo": float(p[2]), "corte": float(p[3])}; guardar(e)
                    except (IndexError, ValueError):
                        pass
                    pl = e["plan"]
                avisar("Plan: cada entrada %.2f SOL · vender en x%.2f · cortar si cae un %.0f %%." % (pl["sol"], pl["objetivo"], pl["corte"]))
            elif texto.startswith("/cartera"):
                avisar(cartera())
            elif texto.startswith("/balance"):
                avisar(balance())
            elif texto.startswith("/cierra") and DIRECCION.search(texto):
                ca = DIRECCION.search(texto).group(0)
                with cerrojo:
                    e = estado(); pr = precios([ca]).get(ca)
                    msg = cerrar(e, ca, pr["precio"], "cerrada a mano") if ca in e["abiertas"] and pr else "No la tienes abierta o no hay precio."
                    guardar(e)
                avisar(msg)
            elif DIRECCION.search(texto):
                for ca in dict.fromkeys(DIRECCION.findall(texto)):
                    avisar(comprar(ca))
            else:
                avisar("Pégame un contrato para comprarlo en papel. /plan 0.2 2 50 · /cartera · /balance · /cierra <contrato>")
        if not r:
            time.sleep(3)


def main():
    if not TOKEN:
        print("Falta TELEGRAM_BOT_TOKEN en el fichero .env"); return
    print("Bot en papel en marcha. Pégale un contrato a tu bot. (Ctrl+C para parar)")
    threading.Thread(target=escuchar_bot, daemon=True).start()
    vigilar()


if __name__ == "__main__":
    main()
