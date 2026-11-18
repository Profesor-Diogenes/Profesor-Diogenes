#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vigilar un token de pump.fun EN DIRECTO y que tu bot te avise cuando alguien vende mucho de golpe.
Canal de YouTube: Profesor Diógenes · sección "Bots de Solana", vídeo 13.

    python3 ventas_gordas.py

Cómo se usa, desde Telegram:
  - Le pegas un contrato (y un nombre detrás si quieres) -> lo vigila.
  - /lista · /quitar <contrato>
  - /umbral 2      -> avisar de ventas de 2 SOL o más (por defecto 2)
  - /supply 0.5    -> o de ventas del 0,5 % del supply o más (por defecto 0,5)

Cómo funciona por dentro:
  - Una conexión abierta con el nodo público de Solana (gratis, sin clave): "avísame de todo lo que toque este token".
  - De cada aviso solo se miran las VENTAS (el registro de la operación dice "Instruction: Sell", tanto en la
    curva de pump.fun como en su mercado de después, PumpSwap). Se pide la operación entera y se mira
    quién vende, cuántos tokens suelta, cuánto SOL saca y cuánto le queda.
  - Si pasa del umbral, te avisa.

Límite real: el nodo gratis contesta más o menos una pregunta por segundo. En un token con muchísimas ventas
por segundo la cola se llena y las más viejas se tiran: para eso hace falta un nodo propio (SOLANA_RPC y SOLANA_WS).
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
LISTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tokens.json")
AJUSTES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ajustes.json")
DIRECCION = re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b")
WSOL = "So11111111111111111111111111111111111111112"   # la moneda SOL "envuelta" (dirección pública)  # pragma: allowlist secret
ESTABLES = {"EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": "USDC", "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": "USDT"}  # pragma: allowlist secret
COLA_MAXIMA = 40          # ventas esperando a ser miradas; si hay más, se tiran las más viejas


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


def ajustes():
    try:
        return json.load(open(AJUSTES))
    except Exception:
        return {"umbral_sol": 2.0, "umbral_supply": 0.5}


_supply = {}


def supply(mint):
    if mint not in _supply:
        r = nodo("getTokenSupply", [mint]) or {}
        _supply[mint] = num((r.get("value") or {}).get("uiAmountString")) or 1e9      # pump.fun: mil millones
    return _supply[mint]


def mirar_venta(firma, mint):
    """Quién vende, cuánto suelta, cuánto SOL saca y cuánto le queda. Devuelve None si no llega al umbral."""
    t = nodo("getTransaction", [firma, {"encoding": "json", "maxSupportedTransactionVersion": 1, "commitment": "confirmed"}])
    if not t or not t.get("meta") or t["meta"].get("err"):
        return None
    m = t["meta"]; k = list(t["transaction"]["message"]["accountKeys"])
    vendedor = k[0]                                              # el que firma y paga la operación
    antes = sum(num((b.get("uiTokenAmount") or {}).get("uiAmountString")) for b in m.get("preTokenBalances") or []
                if b.get("mint") == mint and b.get("owner") == vendedor)
    despues = sum(num((b.get("uiTokenAmount") or {}).get("uiAmountString")) for b in m.get("postTokenBalances") or []
                  if b.get("mint") == mint and b.get("owner") == vendedor)
    vendido = antes - despues
    if vendido <= 0:
        return None
    sol = (m["postBalances"][0] - m["preBalances"][0] + m.get("fee", 0)) / 1e9
    for lado, signo in (("preTokenBalances", -1), ("postTokenBalances", 1)):        # por si cobra en SOL envuelto
        for b in m.get(lado) or []:
            if b.get("mint") == WSOL and b.get("owner") == vendedor:
                sol += signo * num((b.get("uiTokenAmount") or {}).get("uiAmountString"))
    total = supply(mint); a = ajustes()
    pct = 100 * vendido / total
    if sol < a["umbral_sol"] and pct < a["umbral_supply"]:
        return None
    return {"vendedor": vendedor, "vendido": vendido, "pct": pct, "sol": sol, "queda": 100 * despues / total}


def aviso(mint, nombre, firma, v):
    f = ficha_token(mint)
    saca = "saca <b>%.2f SOL</b>" % v["sol"] if v["sol"] > 0.005 else "el SOL lo cobra otra billetera"
    return ("🔻 <b>VENTA GORDA en %s</b>\n   %s suelta el <b>%.2f %%</b> del supply y %s\n   %s\n"
            "   capitalización %s · liquidez %s\n   <a href='https://solscan.io/tx/%s'>ver en Solscan</a>" % (
                nombre or f["simbolo"], v["vendedor"][:6] + "…" + v["vendedor"][-4:], v["pct"], saca,
                "le queda el %.2f %%" % v["queda"] if v["queda"] >= 0.01 else "ha vendido TODO lo que tenía",
                dinero(f["mc"]), dinero(f["liq"]) if f["liq"] else "todavía en pump.fun", firma))


# ───────────────────────────────────────────────── el vigía en directo
async def trabajador(cola):
    """Mira las ventas de una en una, al ritmo que deja el nodo gratis."""
    while True:
        mint, firma = await cola.get()
        v = await asyncio.to_thread(mirar_venta, firma, mint)
        if v and mint in leer_lista():
            await asyncio.to_thread(avisar, await asyncio.to_thread(aviso, mint, leer_lista().get(mint), firma, v))


async def vigias():
    cola = asyncio.Queue()
    asyncio.create_task(trabajador(cola))
    vistas = set()
    while True:
        try:
            async with websockets.connect(NODO_WS, ping_interval=20, ping_timeout=20, max_size=2 ** 22) as ws:
                suscritas, pendientes, n = {}, {}, 0
                async def suscribir(mint):
                    nonlocal n
                    n += 1; pendientes[n] = mint
                    await ws.send(json.dumps({"jsonrpc": "2.0", "id": n, "method": "logsSubscribe",
                                              "params": [{"mentions": [mint]}, {"commitment": "confirmed"}]}))
                for mint in leer_lista():
                    await suscribir(mint)
                ultima_mirada = time.time()
                while True:
                    try:
                        msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
                    except asyncio.TimeoutError:
                        msg = {}
                    if msg.get("id") in pendientes and "result" in msg:
                        suscritas[msg["result"]] = pendientes.pop(msg["id"])
                        print("vigilando", suscritas[msg["result"]])
                    p = msg.get("params") or {}
                    mint = suscritas.get(p.get("subscription"))
                    val = (p.get("result") or {}).get("value") or {}
                    firma = val.get("signature")
                    if mint and firma and not val.get("err") and firma not in vistas and mint in leer_lista():
                        vistas.add(firma)
                        if any("Instruction: Sell" in l for l in val.get("logs") or []):      # solo las ventas
                            while cola.qsize() >= COLA_MAXIMA:
                                cola.get_nowait()                                            # se tiran las más viejas
                            cola.put_nowait((mint, firma))
                    if time.time() - ultima_mirada > 3:
                        ultima_mirada = time.time()
                        for mint in leer_lista():
                            if mint not in suscritas.values() and mint not in pendientes.values():
                                await suscribir(mint)
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
            lista = leer_lista(); a = ajustes()
            valor = (texto.split() + [""])[1].replace(",", ".")
            if texto.startswith("/lista"):
                avisar("👁 Vigilando %d:\n%s\nAviso desde %.1f SOL o desde el %.2f %% del supply." % (
                    len(lista), "\n".join("• %s — <code>%s</code>" % (n, w) for w, n in lista.items()) or "ninguno",
                    a["umbral_sol"], a["umbral_supply"]))
            elif texto.startswith("/quitar"):
                for w in DIRECCION.findall(texto):
                    lista.pop(w, None)
                guardar_lista(lista); avisar("Hecho. Vigilando %d." % len(lista))
            elif texto.startswith(("/umbral", "/supply")):
                try:
                    a["umbral_sol" if texto.startswith("/umbral") else "umbral_supply"] = float(valor)
                    json.dump(a, open(AJUSTES, "w"))
                except ValueError:
                    pass
                avisar("Aviso de ventas desde %.1f SOL o desde el %.2f %% del supply." % (a["umbral_sol"], a["umbral_supply"]))
            elif DIRECCION.search(texto):
                w = DIRECCION.search(texto).group(0)
                nombre = texto.replace(w, "").strip() or ficha_token(w)["simbolo"]
                lista[w] = nombre; guardar_lista(lista)
                avisar("👁 Vigilando <b>%s</b>. Te aviso si alguien suelta %.1f SOL o más, o el %.2f %% del supply." % (
                    nombre, a["umbral_sol"], a["umbral_supply"]))
            else:
                avisar("Pégame el contrato de un token de pump.fun. /lista · /quitar · /umbral 2 · /supply 0.5")
        if not r:
            time.sleep(3)


def main():
    if not TOKEN:
        print("Falta TELEGRAM_BOT_TOKEN en el fichero .env"); return
    print("En marcha. Pégale un contrato a tu bot. (Ctrl+C para parar)")
    threading.Thread(target=escuchar_telegram, daemon=True).start()
    asyncio.run(vigias())


if __name__ == "__main__":
    main()
