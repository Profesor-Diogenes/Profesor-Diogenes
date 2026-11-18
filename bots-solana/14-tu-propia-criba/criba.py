#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tu propia criba: cada pocos minutos mira los tokens que más se mueven en GMGN, se queda con los que cumplen
TUS reglas y te los manda a Telegram. Y los apunta, para medir después si tu criba sirve.
Canal de YouTube: Profesor Diógenes · sección "Bots de Solana", vídeo 14.

    python3 criba.py

Cómo se usa, desde tu bot:
  /criba                     -> tus reglas de ahora
  /pon mc 25000 600000       -> capitalización entre 25.000 y 600.000 $
  /pon liquidez 5000         -> liquidez mínima en $ (y siempre al menos el 10 % de la capitalización)
  /pon volumen 50000         -> volumen mínimo de las últimas 24 h en $
  /pon holders 150 400       -> número de holders entre 150 y 400 (0 0 para no mirarlo)
  /ahora                     -> los que pasan la criba ahora mismo
  /pausa · /sigue

Reglas fijas (no se quitan): solo pump.fun, nadie puede fabricar más tokens ni congelarte, y liquidez quemada.

Cómo funciona por dentro: le pide a GMGN la lista de los tokens con más movimiento (vale la clave pública de pruebas),
que ya trae capitalización, liquidez, volumen, holders y seguridad de cada uno, y aplica tus reglas.
Cada token que pasa se avisa UNA vez y se apunta en "cribados.csv" con su capitalización de ese momento.
Esto NO es consejo financiero. Es una herramienta para mirar.
"""
import os, csv, json, time, uuid, threading
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
CADA = int(os.environ.get("CADA_MINUTOS", "3"))
BOT = "https://api.telegram.org/bot%s/" % TOKEN
REGLAS = os.path.join(AQUI, "reglas.json")
REGISTRO = os.path.join(AQUI, "cribados.csv")
DE_SERIE = {"mc_min": 25000, "mc_max": 600000, "liquidez": 5000, "volumen": 50000, "holders_min": 0, "holders_max": 0, "pausa": False}


def reglas():
    try:
        return dict(DE_SERIE, **json.load(open(REGLAS)))
    except Exception:
        return dict(DE_SERIE)


def telegram(metodo, **datos):
    try:
        return requests.post(BOT + metodo, json=datos, timeout=60).json()
    except Exception:
        return {}


def avisar(texto):
    telegram("sendMessage", chat_id=MI_ID, text=texto, parse_mode="HTML", disable_web_page_preview=True)


def num(x, d=0.0):
    try:
        return float(x)
    except Exception:
        return d


def dinero(x):
    if x >= 1e6: return "%.2f M$" % (x / 1e6)
    if x >= 1e3: return "%.1f K$" % (x / 1e3)
    return "%.0f $" % x


def universo():
    """Los tokens con más movimiento según GMGN en las últimas 24 h y en la última hora (dos preguntas)."""
    vistos = {}
    for intervalo in ("24h", "1h"):
        q = {"chain": "sol", "interval": intervalo, "limit": 100, "timestamp": int(time.time()), "client_id": str(uuid.uuid4())}
        try:
            d = requests.get("https://openapi.gmgn.ai/v1/market/rank", params=q, timeout=25,
                             headers={"X-APIKEY": CLAVE, "User-Agent": "profesor-diogenes"}).json()
            lista = ((d.get("data") or {}).get("data") or d.get("data") or {}).get("rank") or []
        except Exception:
            lista = []
        for t in lista:
            if intervalo == "24h":
                t["volumen_24h"] = num(t.get("volume"))
            vistos.setdefault(t.get("address"), {}).update(t)
        time.sleep(1.5)
    return list(vistos.values())


def pasa(t, r):
    mc, liq = num(t.get("market_cap")), num(t.get("liquidity"))
    plataforma = ("%s %s" % (t.get("launchpad") or "", t.get("launchpad_platform") or "")).lower()
    if "pump" not in plataforma:
        return False                                             # solo pump.fun: es donde los precios se pueden medir
    if str(t.get("renounced_mint")) != "1" or str(t.get("renounced_freeze_account")) != "1":
        return False                                             # pueden fabricar más o congelarte
    if t.get("burn_status") != "burn":
        return False                                             # liquidez sin quemar
    if not (r["mc_min"] <= mc <= r["mc_max"]):
        return False
    if liq < r["liquidez"] or liq < 0.10 * mc:                   # bonito pero seco
        return False
    if "volumen_24h" in t and t["volumen_24h"] < r["volumen"]:
        return False
    h = num(t.get("holder_count"))
    if r["holders_max"] and not (r["holders_min"] <= h <= r["holders_max"]):
        return False
    return True


def linea(t):
    mc = num(t.get("market_cap"))
    return ("<b>%s</b> (%s)\n   capitalización %s · liquidez %s · holders %d\n   <code>%s</code>\n"
            "   <a href='https://gmgn.ai/sol/token/%s'>GMGN</a> · <a href='https://dexscreener.com/solana/%s'>DexScreener</a>" % (
                t.get("symbol") or "?", (t.get("name") or "")[:30], dinero(mc), dinero(num(t.get("liquidity"))),
                num(t.get("holder_count")), t.get("address"), t.get("address"), t.get("address")))


def vigilar():
    ya = set()
    if os.path.exists(REGISTRO):
        ya = {r["contrato"] for r in csv.DictReader(open(REGISTRO, encoding="utf-8"))}
    primera = True
    while True:
        r = reglas()
        if not r["pausa"]:
            for t in universo():
                ca = t.get("address")
                if ca in ya or not pasa(t, r):
                    continue
                ya.add(ca)
                nuevo = not os.path.exists(REGISTRO)
                with open(REGISTRO, "a", newline="", encoding="utf-8") as fh:
                    w = csv.writer(fh)
                    if nuevo:
                        w.writerow(["hora", "contrato", "simbolo", "capitalizacion", "liquidez", "holders"])
                    w.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), ca, t.get("symbol") or "", int(num(t.get("market_cap"))),
                                int(num(t.get("liquidity"))), int(num(t.get("holder_count")))])
                if not primera:                      # al arrancar se apuntan los que ya pasaban, sin avisar de todos de golpe
                    avisar("🧺 PASA TU CRIBA\n" + linea(t))
            primera = False
        time.sleep(CADA * 60)


def texto_reglas(r):
    return ("🧺 Tu criba%s:\n• capitalización entre %s y %s\n• liquidez de %s o más (y al menos el 10 %% de la capitalización)\n"
            "• volumen de 24 h de %s o más\n• holders: %s\n• fijas: solo pump.fun, sin poder fabricar ni congelar, liquidez quemada" % (
                " (EN PAUSA)" if r["pausa"] else "", dinero(r["mc_min"]), dinero(r["mc_max"]), dinero(r["liquidez"]), dinero(r["volumen"]),
                "entre %d y %d" % (r["holders_min"], r["holders_max"]) if r["holders_max"] else "cualquiera"))


def escuchar_bot():
    desde = 0
    while True:
        resp = telegram("getUpdates", offset=desde, timeout=50, allowed_updates=["message"])
        for u in resp.get("result") or []:
            desde = u["update_id"] + 1
            m = u.get("message") or {}
            chat = (m.get("chat") or {}).get("id")
            quien = str((m.get("from") or {}).get("id"))
            p = (m.get("text") or "").strip().lower().split()
            if not chat or not p:
                continue
            if not MI_ID:
                telegram("sendMessage", chat_id=chat, text="Tu número de usuario es %s. Ponlo en TELEGRAM_MI_ID del .env y vuelve a arrancar." % quien)
                continue
            if quien != MI_ID:
                continue
            r = reglas()
            numeros = [num(x.replace(".", "").replace(",", ""), None) for x in p[2:]]
            if p[0] == "/pon" and len(p) >= 3 and None not in numeros:
                if p[1] == "mc" and len(numeros) == 2: r["mc_min"], r["mc_max"] = numeros
                elif p[1].startswith("liq"): r["liquidez"] = numeros[0]
                elif p[1].startswith("vol"): r["volumen"] = numeros[0]
                elif p[1].startswith("hold") and len(numeros) == 2: r["holders_min"], r["holders_max"] = int(numeros[0]), int(numeros[1])
                json.dump(r, open(REGLAS, "w"))
            elif p[0] in ("/pausa", "/sigue"):
                r["pausa"] = p[0] == "/pausa"; json.dump(r, open(REGLAS, "w"))
            elif p[0] == "/ahora":
                avisar("Mirando…")
                ok = [t for t in universo() if pasa(t, r)]
                avisar("Ahora mismo pasan %d:\n\n%s" % (len(ok), "\n\n".join(linea(t) for t in ok[:8]) or "ninguno"))
                continue
            elif p[0] != "/criba":
                avisar("Órdenes: /criba · /pon mc 25000 600000 · /pon liquidez 5000 · /pon volumen 50000 · /pon holders 150 400 · /ahora · /pausa · /sigue")
                continue
            avisar(texto_reglas(r))
        if not resp:
            time.sleep(3)


def main():
    if not TOKEN:
        print("Falta TELEGRAM_BOT_TOKEN en el fichero .env"); return
    print("Criba en marcha. Escríbele /criba a tu bot. (Ctrl+C para parar)")
    threading.Thread(target=escuchar_bot, daemon=True).start()
    vigilar()


if __name__ == "__main__":
    main()
