#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Seguir billeteras de Solana EN DIRECTO y que tu bot de Telegram te avise en cuanto compran o venden.
Canal de YouTube: Profesor Diógenes · sección "Bots de Solana", vídeo 4.

    python3 vigia.py

Cómo se usa, desde Telegram:
  - Le pegas una billetera  -> la empieza a vigilar.
  - Le pegas "billetera nombre" (ej: "9ncm3Mfx... el creador") -> la vigila con ese nombre.
  - /lista                  -> te dice cuáles vigila.
  - /quitar <billetera>     -> deja de vigilarla.

Cómo funciona por dentro:
  - Se conecta al nodo público de Solana por WebSocket (una conexión que se queda abierta)
    y le dice: "avísame de todo lo que toque esta billetera". Gratis y sin clave.
  - Cuando llega algo, pide la operación entera, mira cuánto SOL salió o entró y qué token,
    le pregunta a DexScreener el nombre y el precio, y te lo manda a Telegram.
  - Si la conexión se cae, se vuelve a conectar sola.

Esto NO es consejo financiero. Es una herramienta para mirar.
"""
import os, re, json, time, asyncio, threading
import requests
import websockets


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
NODO = os.environ.get("SOLANA_RPC", "https://api.mainnet-beta.solana.com")
NODO_WS = os.environ.get("SOLANA_WS", "wss://api.mainnet-beta.solana.com")
API = "https://api.telegram.org/bot%s/" % TOKEN
LISTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vigiladas.json")
DIRECCION = re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b")
WSOL = "So11111111111111111111111111111111111111112"   # la moneda SOL "envuelta" (dirección pública)  # pragma: allowlist secret
ESTABLES = {"EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": "USDC", "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": "USDT"}  # pragma: allowlist secret
MINIMO_SOL = float(os.environ.get("MINIMO_SOL", "0.05"))   # no avisar de movimientos más pequeños que esto


# ───────────────────────────────────────────────── la lista de billeteras
def leer_lista():
    try:
        return json.load(open(LISTA))
    except Exception:
        return {}


def guardar_lista(d):
    json.dump(d, open(LISTA, "w"), indent=1, ensure_ascii=False)


# ───────────────────────────────────────────────── Telegram
def telegram(metodo, **datos):
    try:
        return requests.post(API + metodo, json=datos, timeout=60).json()
    except Exception:
        return {}


def avisar(texto):
    telegram("sendMessage", chat_id=MI_ID, text=texto, parse_mode="HTML", disable_web_page_preview=True)


# ───────────────────────────────────────────────── el nodo
_ultima = [0.0]
_cerrojo = threading.Lock()


def nodo(metodo, params):
    """Pregunta al nodo público, como mucho una vez por segundo (corta por IP si corres)."""
    for intento in range(8):
        with _cerrojo:
            falta = 1.1 - (time.time() - _ultima[0])
            if falta > 0:
                time.sleep(falta)
            _ultima[0] = time.time()
        try:
            d = requests.post(NODO, json={"jsonrpc": "2.0", "id": 1, "method": metodo, "params": params}, timeout=20).json()
        except Exception:
            continue
        if d.get("error"):
            if d["error"].get("code") in (429, -32429) or "rate" in str(d["error"]).lower():
                time.sleep(5); continue
            return None
        if d.get("result") is None:
            time.sleep(2); continue          # recién confirmada: a veces tarda un poco en estar
        return d.get("result")
    return None


def num(x, d=0.0):
    try:
        return float(x)
    except Exception:
        return d


def ficha_token(mint):
    """Nombre, precio y liquidez del token según DexScreener (gratis)."""
    try:
        pares = requests.get("https://api.dexscreener.com/latest/dex/tokens/" + mint, timeout=15).json().get("pairs") or []
    except Exception:
        pares = []
    pares = [p for p in pares if (p.get("baseToken") or {}).get("address") == mint] or pares
    if not pares:
        return {"simbolo": mint[:6] + "…", "mc": None, "liq": None}
    p = max(pares, key=lambda p: num((p.get("liquidity") or {}).get("usd")))
    return {"simbolo": (p.get("baseToken") or {}).get("symbol") or mint[:6], "mc": p.get("marketCap") or p.get("fdv"),
            "liq": num((p.get("liquidity") or {}).get("usd"))}


def dinero(x):
    if x is None: return "?"
    if x >= 1e6: return "%.2f M$" % (x / 1e6)
    if x >= 1e3: return "%.1f K$" % (x / 1e3)
    return "%.0f $" % x


def leer_operacion(firma, w):
    """Qué hizo la billetera en esta operación: SOL que salió/entró y tokens que entraron/salieron."""
    t = nodo("getTransaction", [firma, {"encoding": "json", "maxSupportedTransactionVersion": 1, "commitment": "confirmed"}])
    if not t or not t.get("meta") or t["meta"].get("err"):
        return None
    m = t["meta"]; k = list(t["transaction"]["message"]["accountKeys"])
    k += (m.get("loadedAddresses") or {}).get("writable") or []
    k += (m.get("loadedAddresses") or {}).get("readonly") or []
    sol = 0.0
    if w in k:
        j = k.index(w)
        sol = (m["postBalances"][j] - m["preBalances"][j] + (m.get("fee", 0) if j == 0 else 0)) / 1e9
    cambios = {}
    for lado, signo in (("preTokenBalances", -1), ("postTokenBalances", 1)):
        for b in m.get(lado) or []:
            if b.get("owner") == w:
                cambios[b["mint"]] = cambios.get(b["mint"], 0) + signo * num((b.get("uiTokenAmount") or {}).get("uiAmountString"))
    sol += cambios.pop(WSOL, 0)
    estable = {ESTABLES[x]: cambios.pop(x) for x in list(cambios) if x in ESTABLES}
    cambios = {mint: c for mint, c in cambios.items() if abs(c) > 0}
    return {"sol": sol, "estable": estable, "tokens": cambios, "hora": t.get("blockTime")}


def describir(w, nombre, firma, op):
    """El mensaje de Telegram. Si no hay nada que contar (propinas, polvo), devuelve None."""
    if not op["tokens"]:
        if abs(op["sol"]) < MINIMO_SOL:
            return None
        return "💸 <b>%s</b> %s %.2f SOL\n<a href='https://solscan.io/tx/%s'>ver en Solscan</a>" % (
            nombre, "recibe" if op["sol"] > 0 else "envía", abs(op["sol"]), firma)
    fichas = {mint: ficha_token(mint) for mint in op["tokens"]}
    lineas = []
    for mint, c in op["tokens"].items():
        compra = c > 0
        if abs(op["sol"]) >= 0.001:
            if abs(op["sol"]) < MINIMO_SOL:
                continue
            pago = "%.2f SOL" % abs(op["sol"])
        elif op["estable"]:
            if max(abs(v) for v in op["estable"].values()) < 5:
                continue                       # céntimos: no molestar
            pago = " · ".join("%.0f %s" % (abs(v), k) for k, v in op["estable"].items())
        else:
            otros = [fichas[m]["simbolo"] for m, x in op["tokens"].items() if (x > 0) != compra]
            if not otros:
                continue                       # le llegó o se fue sin pagar nada: no es una compra ni una venta
            pago = "a cambio de " + ", ".join(otros)
        f = fichas[mint]
        lineas.append("%s <b>%s</b> %s <b>%s</b> %s%s\n   capitalización %s · liquidez %s\n   <code>%s</code>" % (
            "🟢" if compra else "🔴", nombre, "COMPRA" if compra else "VENDE", f["simbolo"],
            pago if pago.startswith("a cambio") else ("por " if compra else "y saca ") + pago, "",
            dinero(f["mc"]), dinero(f["liq"]) if f["liq"] else "todavía en pump.fun", mint))
    if not lineas:
        return None
    return "\n".join(lineas) + "\n<a href='https://solscan.io/tx/%s'>ver en Solscan</a>" % firma


# ───────────────────────────────────────────────── el vigía en directo
async def procesar(w, firma, vistas):
    if firma in vistas:
        return
    vistas.add(firma)
    nombre = leer_lista().get(w) or w[:8] + "…"
    op = await asyncio.to_thread(leer_operacion, firma, w)
    if op:
        texto = await asyncio.to_thread(describir, w, nombre, firma, op)
        if texto:
            await asyncio.to_thread(avisar, texto)


async def vigias():
    """UNA sola conexión abierta con el nodo, con una suscripción por billetera.
    (El nodo gratis corta si abres muchas conexiones desde la misma IP; muchas suscripciones en una, sí las aguanta.)
    Si se cae, se vuelve a conectar y repasa lo que se haya perdido mientras."""
    vistas = {}
    desde = time.time()
    while True:
        try:
            async with websockets.connect(NODO_WS, ping_interval=20, ping_timeout=20, max_size=2 ** 22) as ws:
                suscritas, pendientes, n = {}, {}, 0          # id de suscripción -> billetera
                async def suscribir(w):
                    nonlocal n
                    n += 1; pendientes[n] = w
                    await ws.send(json.dumps({"jsonrpc": "2.0", "id": n, "method": "logsSubscribe",
                                              "params": [{"mentions": [w]}, {"commitment": "confirmed"}]}))
                for w in leer_lista():
                    await suscribir(w)
                    perdidas = await asyncio.to_thread(nodo, "getSignaturesForAddress", [w, {"limit": 10}]) or []
                    for x in reversed(perdidas):
                        if (x.get("blockTime") or 0) >= desde and not x.get("err"):
                            await procesar(w, x["signature"], vistas.setdefault(w, set()))
                ultima_mirada = time.time()
                while True:
                    try:
                        msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
                    except asyncio.TimeoutError:
                        msg = {}
                    if msg.get("id") in pendientes and "result" in msg:          # confirmación de una suscripción
                        suscritas[msg["result"]] = pendientes.pop(msg["id"])
                        print("vigilando", suscritas[msg["result"]])
                    p = msg.get("params") or {}
                    w = suscritas.get(p.get("subscription"))
                    val = (p.get("result") or {}).get("value") or {}
                    if w and w in leer_lista() and val.get("signature") and not val.get("err"):
                        await procesar(w, val["signature"], vistas.setdefault(w, set()))
                        desde = time.time() - 30
                    if time.time() - ultima_mirada > 3:                       # ¿le han pegado billeteras nuevas al bot?
                        ultima_mirada = time.time()
                        for w in leer_lista():
                            if w not in suscritas.values() and w not in pendientes.values():
                                await suscribir(w)
        except Exception as e:
            print("conexión caída (%s): reconecto en 10 s" % str(e)[:60])
            await asyncio.sleep(10)


# ───────────────────────────────────────────────── lo que le escribes al bot
def escuchar_telegram():
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
            lista = leer_lista()
            if texto.startswith("/lista"):
                avisar("👁 Vigilando %d:\n%s" % (len(lista), "\n".join("• %s — <code>%s</code>" % (n, w) for w, n in lista.items()) or "ninguna"))
            elif texto.startswith("/quitar"):
                for w in DIRECCION.findall(texto):
                    lista.pop(w, None)
                guardar_lista(lista); avisar("Hecho. Vigilando %d." % len(lista))
            elif DIRECCION.search(texto):
                w = DIRECCION.search(texto).group(0)
                nombre = texto.replace(w, "").strip() or w[:8] + "…"
                lista[w] = nombre; guardar_lista(lista)
                avisar("👁 Vigilando a <b>%s</b>. Te aviso en cuanto compre o venda." % nombre)
            else:
                avisar("Pégame una billetera de Solana (y si quieres, un nombre detrás). /lista para ver las que vigilo.")
        if not r:
            time.sleep(3)


def main():
    if not TOKEN:
        print("Falta TELEGRAM_BOT_TOKEN en el fichero .env"); return
    print("Vigía en marcha. Escríbele una billetera a tu bot. (Ctrl+C para parar)")
    threading.Thread(target=escuchar_telegram, daemon=True).start()
    asyncio.run(vigias())


if __name__ == "__main__":
    main()
