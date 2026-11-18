#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Las señales de GMGN en tu Telegram: compra un KOL, compra el "dinero listo", vende el bundler del lanzamiento,
la comunidad se queda el token (CTO). Y una orden para medir tú si sirven de algo.
Canal de YouTube: Profesor Diógenes · sección "Bots de Solana", vídeo 9.

    python3 senales.py

Cómo se usa, desde tu bot:
  /senales            -> qué señales tienes encendidas
  /pon kol            -> enciende una (kol, smart, bundler, cto)
  /quita bundler      -> apaga una
  /minimo 50000       -> solo avisa si el token vale al menos esto en el disparo (en dólares)
  /mide               -> cómo han ido las señales que te ha mandado (precio de ahora contra el del disparo)

Cómo funciona por dentro:
  - Cada minuto le pregunta a GMGN por las últimas señales (vale la clave pública de pruebas).
    GMGN da, en cada señal, la capitalización EN EL INSTANTE del disparo: con eso se puede medir sin trampa.
  - Te avisa de las nuevas y las apunta en "senales.csv".
  - /mide compara la capitalización de ahora (DexScreener) con la del disparo.

Esto NO es consejo financiero. Es una herramienta para mirar.
"""
import os, re, csv, json, time, uuid, threading
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
CLAVE = os.environ.get("GMGN_API_KEY") or "gmgn_solbscbaseethmonadtron"   # la pública de pruebas de GMGN
BOT = "https://api.telegram.org/bot%s/" % TOKEN
AJUSTES = os.path.join(AQUI, "ajustes.json")
REGISTRO = os.path.join(AQUI, "senales.csv")

# Los números son los tipos de señal de GMGN
TIPOS = {"smart": (12, "🧠 compra el dinero listo"), "kol": (20, "📢 compra un KOL"),
         "bundler": (10, "🔻 vende el bundler del lanzamiento"), "cto": (11, "🏴 CTO: la comunidad se queda el token")}
NOMBRE = {n: (k, t) for k, (n, t) in TIPOS.items()}


# ───────────────────────────────────────────────── ajustes
def ajustes():
    try:
        return json.load(open(AJUSTES))
    except Exception:
        return {"encendidas": ["smart", "kol"], "minimo": 0}


def guardar(a):
    json.dump(a, open(AJUSTES, "w"), indent=1)


# ───────────────────────────────────────────────── fuentes
def telegram(metodo, **datos):
    try:
        return requests.post(BOT + metodo, json=datos, timeout=60).json()
    except Exception:
        return {}


def avisar(texto):
    telegram("sendMessage", chat_id=MI_ID, text=texto, parse_mode="HTML", disable_web_page_preview=True)


def gmgn_senales(tipos):
    """GMGN deja como mucho 2 tipos por grupo: se piden por parejas, en una sola petición."""
    grupos = [{"signal_type": tipos[i:i + 2]} for i in range(0, len(tipos), 2)]
    q = {"timestamp": int(time.time()), "client_id": str(uuid.uuid4())}
    try:
        r = requests.post("https://openapi.gmgn.ai/v1/market/token_signal", params=q, timeout=25,
                          json={"chain": "sol", "groups": grupos},
                          headers={"X-APIKEY": CLAVE, "User-Agent": "profesor-diogenes"})
        d = r.json()
    except Exception:
        return []
    if str(d.get("code")) != "0":
        print("GMGN contesta", d.get("code"), d.get("message")); return []
    salida = []
    for x in d.get("data") or []:
        salida += x if isinstance(x, list) else [x]
    return salida


def capitalizacion_ahora(ca):
    try:
        pares = requests.get("https://api.dexscreener.com/latest/dex/tokens/" + ca, timeout=15).json().get("pairs") or []
    except Exception:
        return None
    pares = [p for p in pares if (p.get("baseToken") or {}).get("address") == ca]
    if not pares:
        return None
    p = max(pares, key=lambda p: float((p.get("liquidity") or {}).get("usd") or 0))
    return float(p.get("marketCap") or p.get("fdv") or 0) or None


def dinero(x):
    if not x: return "?"
    if x >= 1e6: return "%.2f M$" % (x / 1e6)
    if x >= 1e3: return "%.1f K$" % (x / 1e3)
    return "%.0f $" % x


# ───────────────────────────────────────────────── el vigía de señales
def vigilar():
    vistas = set()
    if os.path.exists(REGISTRO):
        vistas = {r["id"] for r in csv.DictReader(open(REGISTRO, encoding="utf-8"))}
    estrenados = set()                   # tipos de señal que ya hemos leído al menos una vez
    while True:
        a = ajustes()
        tipos = [TIPOS[k][0] for k in a["encendidas"] if k in TIPOS]
        nuevas = []
        for s in sorted(gmgn_senales(tipos), key=lambda s: s.get("trigger_at") or 0):
            if s.get("id") in vistas:
                continue
            vistas.add(s.get("id"))
            if s.get("signal_type") not in estrenados:
                continue                 # lo que ya había al arrancar o al encender una señal no se avisa: solo lo nuevo
            mc = float(s.get("trigger_mc") or 0)
            if mc < float(a.get("minimo") or 0):
                continue
            nuevas.append(s)
        estrenados.update(tipos)
        for s in nuevas:
            dat = s.get("data") or {}
            ca = s.get("token_address") or dat.get("address")
            clave, texto = NOMBRE.get(s.get("signal_type"), ("?", "señal %s" % s.get("signal_type")))
            avisar("%s\n<b>%s</b> (%s)\n   capitalización en el disparo %s · holders %s\n   <code>%s</code>\n   <a href='https://gmgn.ai/sol/token/%s'>GMGN</a> · <a href='https://dexscreener.com/solana/%s'>DexScreener</a>" % (
                texto, dat.get("symbol") or ca[:6], dat.get("name") or "", dinero(float(s.get("trigger_mc") or 0)),
                dat.get("holder_count") or "?", ca, ca, ca))
            nuevo = not os.path.exists(REGISTRO)
            with open(REGISTRO, "a", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh)
                if nuevo:
                    w.writerow(["id", "hora", "senal", "contrato", "simbolo", "capitalizacion_disparo"])
                w.writerow([s.get("id"), time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(s.get("trigger_at") or time.time())),
                            clave, ca, dat.get("symbol") or "", int(float(s.get("trigger_mc") or 0))])
        time.sleep(60)


def medir():
    """Precio de ahora contra el del disparo, por tipo de señal. Solo las de hace más de 3 horas."""
    if not os.path.exists(REGISTRO):
        return "Todavía no hay señales apuntadas."
    filas = [r for r in csv.DictReader(open(REGISTRO, encoding="utf-8"))
             if time.time() - time.mktime(time.strptime(r["hora"], "%Y-%m-%d %H:%M:%S")) > 3 * 3600]
    if not filas:
        return "Ninguna señal tiene todavía 3 horas. Vuelve a pedirlo más tarde."
    res = {}
    for r in filas[-60:]:                       # las 60 últimas, para no tardar
        ahora = capitalizacion_ahora(r["contrato"]) or 0
        x = ahora / max(float(r["capitalizacion_disparo"]), 1)
        d = res.setdefault(r["senal"], [0, 0, 0])
        d[0] += 1; d[1] += x >= 2; d[2] += x <= 0.5
        time.sleep(0.3)
    lineas = ["%s: %d señales · ahora valen el doble o más %d · valen la mitad o menos %d" % (k, n, dob, mit)
              for k, (n, dob, mit) in res.items()]
    return "📏 Señales de hace más de 3 h, capitalización de AHORA contra la del disparo:\n" + "\n".join(lineas) + \
        "\n(Ojo: esto mira solo el precio de ahora. Si subió y bajó por el camino, aquí no se ve.)"


# ───────────────────────────────────────────────── lo que le escribes a tu bot
def escuchar_bot():
    desde = 0
    while True:
        r = telegram("getUpdates", offset=desde, timeout=50, allowed_updates=["message"])
        for u in r.get("result") or []:
            desde = u["update_id"] + 1
            m = u.get("message") or {}
            chat = (m.get("chat") or {}).get("id")
            quien = str((m.get("from") or {}).get("id"))
            texto = (m.get("text") or "").strip().lower()
            if not chat:
                continue
            if not MI_ID:
                telegram("sendMessage", chat_id=chat, text="Tu número de usuario es %s. Ponlo en TELEGRAM_MI_ID del .env y vuelve a arrancar." % quien)
                continue
            if quien != MI_ID:
                continue
            a = ajustes()
            palabra = (texto.split() + ["", ""])[1]
            if texto.startswith("/pon") and palabra in TIPOS:
                a["encendidas"] = sorted(set(a["encendidas"]) | {palabra}); guardar(a)
            elif texto.startswith("/quita") and palabra in TIPOS:
                a["encendidas"] = [x for x in a["encendidas"] if x != palabra]; guardar(a)
            elif texto.startswith("/minimo") and re.sub(r"\D", "", palabra):
                a["minimo"] = int(re.sub(r"\D", "", palabra)); guardar(a)
            elif texto.startswith("/mide"):
                avisar("Midiendo… (un momento)"); avisar(medir()); continue
            elif not texto.startswith("/senales"):
                avisar("Órdenes: /senales · /pon kol|smart|bundler|cto · /quita … · /minimo 50000 · /mide"); continue
            avisar("📡 Señales encendidas:\n%s\nMínimo de capitalización en el disparo: %s" % (
                "\n".join("• %s — %s" % (k, TIPOS[k][1]) for k in a["encendidas"]) or "ninguna", dinero(a.get("minimo")) if a.get("minimo") else "ninguno"))
        if not r:
            time.sleep(3)


def main():
    if not TOKEN:
        print("Falta TELEGRAM_BOT_TOKEN en el fichero .env"); return
    print("Señales en marcha. Escríbele /senales a tu bot. (Ctrl+C para parar)")
    threading.Thread(target=escuchar_bot, daemon=True).start()
    vigilar()


if __name__ == "__main__":
    main()
