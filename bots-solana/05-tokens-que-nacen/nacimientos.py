#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Escuchar EN DIRECTO los tokens que nacen en pump.fun y que tu bot de Telegram te avise de los que cumplen TUS reglas.
Canal de YouTube: Profesor Diógenes · sección "Bots de Solana", vídeo 5.

    python3 nacimientos.py

Desde Telegram:
  /reglas                 -> te dice las reglas que tienes puestas
  /palabras gato,perro    -> avisa si el nombre o el ticker lleva alguna de estas palabras (vacío = cualquiera)
  /compra 1               -> avisa solo si el creador compra él mismo al nacer al menos 1 SOL (0 = da igual)
  /historial 0 10         -> avisa solo si el creador ha lanzado antes entre 0 y 10 tokens
  /pausa  y  /sigue       -> para o reanuda los avisos
  /cuentas                -> cuántos han nacido desde que arrancó y de cuántos te ha avisado

Cómo funciona por dentro:
  - Una conexión abierta (WebSocket) con el nodo público de Solana, escuchando el programa de pump.fun.
  - Cada operación de pump.fun deja escrito un "evento" en sus registros. Leemos el de NACIMIENTO
    (nombre, ticker, dirección, creador) y el de COMPRA del propio creador en esa misma operación.
    Todo sale del aviso: no hay que preguntar nada más al nodo.
  - Para el historial del creador, una pregunta a GMGN (clave de pruebas o la tuya).

Esto NO es consejo financiero. Es una herramienta para mirar.
"""
import os, re, json, time, uuid, base64, struct, hashlib, asyncio, threading
import requests, websockets, base58


def cargar_env():
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(ruta):
        for linea in open(ruta, encoding="utf-8"):
            if "=" in linea and not linea.strip().startswith("#"):
                k, v = linea.strip().split("=", 1)
                if v.strip():
                    os.environ.setdefault(k.strip(), v.strip())


cargar_env()
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
MI_ID = os.environ.get("TELEGRAM_MI_ID", "").strip()
NODO_WS = os.environ.get("SOLANA_WS", "wss://api.mainnet-beta.solana.com")
CLAVE_GMGN = os.environ.get("GMGN_API_KEY") or "gmgn_solbscbaseethmonadtron"   # la pública de pruebas de GMGN
API = "https://api.telegram.org/bot%s/" % TOKEN
PUMP = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"      # el programa de pump.fun (dirección pública)  # pragma: allowlist secret
REGLAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reglas.json")
POR_DEFECTO = {"palabras": [], "compra_minima_sol": 0.5, "historial_min": 0, "historial_max": 1000000, "pausa": False}
CUENTAS = {"nacidos": 0, "avisados": 0, "desde": time.time()}


def evento(nombre):
    """Cada evento de pump.fun empieza por 8 bytes que salen de su nombre."""
    return hashlib.sha256(("event:" + nombre).encode()).digest()[:8]


NACE, OPERA = evento("CreateEvent"), evento("TradeEvent")


def leer_texto(b, o):
    n = struct.unpack_from("<I", b, o)[0]; o += 4
    return b[o:o + n].decode("utf-8", "replace"), o + n


def leer_direccion(b, o):
    return base58.b58encode(b[o:o + 32]).decode(), o + 32


def leer_nacimiento(b):
    o = 8
    nombre, o = leer_texto(b, o); ticker, o = leer_texto(b, o); uri, o = leer_texto(b, o)
    mint, o = leer_direccion(b, o); curva, o = leer_direccion(b, o); creador, o = leer_direccion(b, o)
    return {"nombre": nombre, "ticker": ticker, "uri": uri, "mint": mint, "creador": creador}


def leer_operacion(b):
    o = 8
    mint, o = leer_direccion(b, o)
    sol, tokens = struct.unpack_from("<QQ", b, o); o += 16
    compra = b[o] == 1; o += 1
    quien, o = leer_direccion(b, o)
    return {"mint": mint, "sol": sol / 1e9, "compra": compra, "quien": quien}


# ───────────────────────────────────────────────── reglas y Telegram
def reglas():
    try:
        return {**POR_DEFECTO, **json.load(open(REGLAS))}
    except Exception:
        return dict(POR_DEFECTO)


def guardar_reglas(r):
    json.dump(r, open(REGLAS, "w"), indent=1, ensure_ascii=False)


def telegram(metodo, **datos):
    try:
        return requests.post(API + metodo, json=datos, timeout=60).json()
    except Exception:
        return {}


def avisar(texto):
    telegram("sendMessage", chat_id=MI_ID, text=texto, parse_mode="HTML", disable_web_page_preview=True)


def historial_creador(w):
    """Cuántos tokens ha lanzado antes, cuántos salieron de la curva de pump.fun y el mejor que tuvo (GMGN)."""
    try:
        q = {"chain": "sol", "wallet_address": w, "timestamp": int(time.time()), "client_id": str(uuid.uuid4())}
        d = requests.get("https://openapi.gmgn.ai/v1/user/created_tokens", params=q, headers={"X-APIKEY": CLAVE_GMGN}, timeout=15).json().get("data") or {}
        ath = d.get("creator_ath_info") or {}
        return {"lanzados": int(d.get("inner_count") or 0) + int(d.get("open_count") or 0), "salieron": int(d.get("open_count") or 0),
                "mejor": float(ath.get("ath_mc") or 0), "mejor_ticker": ath.get("token_symbol")}
    except Exception:
        return None


def dinero(x):
    if not x: return "?"
    if x >= 1e6: return "%.2f M$" % (x / 1e6)
    if x >= 1e3: return "%.0f K$" % (x / 1e3)
    return "%.0f $" % x


def decidir_y_avisar(n, compra_creador):
    r = reglas()
    if r["pausa"]:
        return
    texto = (n["nombre"] + " " + n["ticker"]).lower()
    if r["palabras"] and not any(p.lower() in texto for p in r["palabras"]):
        return
    if compra_creador < float(r["compra_minima_sol"]):
        return
    h = historial_creador(n["creador"])
    if h is not None and not (int(r["historial_min"]) <= h["lanzados"] <= int(r["historial_max"])):
        return
    CUENTAS["avisados"] += 1
    if h is None:
        hist = "historial: GMGN no contesta"
    elif h["lanzados"] <= 1:
        hist = "es su <b>primer</b> token"
    else:
        hist = "ha lanzado <b>%d</b> tokens · salieron de la curva %d (%.0f%%) · su mejor: %s %s" % (
            h["lanzados"], h["salieron"], 100.0 * h["salieron"] / h["lanzados"], h["mejor_ticker"] or "", dinero(h["mejor"]))
    avisar("🐣 NACE <b>%s</b> (%s)\n   el creador compra %.2f SOL al nacer\n   %s\n   <code>%s</code>\n   <a href='https://pump.fun/coin/%s'>pump.fun</a> · <a href='https://solscan.io/account/%s'>el creador</a>" % (
        n["ticker"], n["nombre"][:40], compra_creador, hist, n["mint"], n["mint"], n["creador"]))


# ───────────────────────────────────────────────── el oído en directo
async def escuchar():
    vistas = set()
    while True:
        try:
            async with websockets.connect(NODO_WS, max_size=None, ping_interval=20, ping_timeout=30) as ws:
                await ws.send(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "logsSubscribe",
                                          "params": [{"mentions": [PUMP]}, {"commitment": "confirmed"}]}))
                await ws.recv()
                print("escuchando pump.fun")
                while True:
                    v = ((json.loads(await asyncio.wait_for(ws.recv(), 60)).get("params") or {}).get("result") or {}).get("value") or {}
                    if not v or v.get("err") or v.get("signature") in vistas:
                        continue
                    vistas.add(v["signature"])
                    if len(vistas) > 100000:
                        vistas.clear()
                    nacidos, compras = [], {}
                    for linea in v.get("logs") or []:
                        if not linea.startswith("Program data: "):
                            continue
                        try:
                            b = base64.b64decode(linea[14:])
                            if b[:8] == NACE:
                                nacidos.append(leer_nacimiento(b))
                            elif b[:8] == OPERA:
                                op = leer_operacion(b)
                                if op["compra"]:
                                    compras[(op["mint"], op["quien"])] = compras.get((op["mint"], op["quien"]), 0) + op["sol"]
                        except Exception:
                            continue
                    for n in nacidos:
                        CUENTAS["nacidos"] += 1
                        threading.Thread(target=decidir_y_avisar, args=(n, compras.get((n["mint"], n["creador"]), 0.0)), daemon=True).start()
        except Exception as e:
            print("conexión caída (%s): reconecto en 5 s" % str(e)[:60])
            await asyncio.sleep(5)


# ───────────────────────────────────────────────── lo que le escribes al bot
def escuchar_telegram():
    desde = 0
    while True:
        res = telegram("getUpdates", offset=desde, timeout=50, allowed_updates=["message"])
        for u in res.get("result") or []:
            desde = u["update_id"] + 1
            m = u.get("message") or {}
            chat = (m.get("chat") or {}).get("id")
            quien = str((m.get("from") or {}).get("id"))
            t = (m.get("text") or "").strip()
            if not chat:
                continue
            if not MI_ID:
                telegram("sendMessage", chat_id=chat, text="Tu número de usuario es %s. Ponlo en TELEGRAM_MI_ID del .env y vuelve a arrancar." % quien)
                continue
            if quien != MI_ID:
                continue
            r = reglas(); partes = t.split()
            if t.startswith("/palabras"):
                r["palabras"] = [p.strip() for p in t[9:].split(",") if p.strip()]; guardar_reglas(r)
            elif t.startswith("/compra") and len(partes) > 1:
                r["compra_minima_sol"] = float(partes[1].replace(",", ".")); guardar_reglas(r)
            elif t.startswith("/historial") and len(partes) > 2:
                r["historial_min"], r["historial_max"] = int(partes[1]), int(partes[2]); guardar_reglas(r)
            elif t.startswith("/pausa"):
                r["pausa"] = True; guardar_reglas(r)
            elif t.startswith("/sigue"):
                r["pausa"] = False; guardar_reglas(r)
            if t.startswith("/cuentas"):
                minutos = (time.time() - CUENTAS["desde"]) / 60
                avisar("En %.0f minutos han nacido <b>%d</b> tokens en pump.fun (%.1f por minuto). Te he avisado de <b>%d</b>." % (
                    minutos, CUENTAS["nacidos"], CUENTAS["nacidos"] / max(minutos, 1), CUENTAS["avisados"]))
            else:
                r = reglas()
                hist = "cualquiera" if r["historial_max"] >= 1000000 and r["historial_min"] <= 0 else "entre %d y %d" % (r["historial_min"], r["historial_max"])
                avisar("⚙️ Tus reglas:\n• palabras: %s\n• el creador compra al nacer al menos %s SOL\n• tokens lanzados antes por el creador: %s\n• %s" % (
                    ", ".join(r["palabras"]) or "cualquiera", r["compra_minima_sol"], hist, "EN PAUSA" if r["pausa"] else "avisando"))
        if not res:
            time.sleep(3)


def main():
    if not TOKEN:
        print("Falta TELEGRAM_BOT_TOKEN en el fichero .env"); return
    print("En marcha. Escríbele /reglas a tu bot. (Ctrl+C para parar)")
    threading.Thread(target=escuchar_telegram, daemon=True).start()
    asyncio.run(escuchar())


if __name__ == "__main__":
    main()
