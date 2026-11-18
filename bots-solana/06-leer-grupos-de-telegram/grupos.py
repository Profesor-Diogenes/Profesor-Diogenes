#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Leer los grupos de calls de Telegram, sacar cada contrato que publican y que tu bot te lo mande al móvil.
Canal de YouTube: Profesor Diógenes · sección "Bots de Solana", vídeo 6.

    python3 grupos.py

La primera vez te pide tu número de teléfono y el código que te manda Telegram (es TU cuenta, la que
está metida en los grupos). Queda guardado en el fichero "sesion_grupos.session": no se lo pases a nadie.

Cómo se usa, desde tu bot de Telegram:
  /grupos            -> los grupos y canales en los que estás, con su número
  /grupos calls      -> solo los que llevan "calls" en el nombre
  /escucha <número>  -> empieza a escuchar ese grupo (puedes poner varios números)
  /quita <número>    -> deja de escucharlo
  /lista             -> los que estás escuchando
  /ultimos           -> las últimas llamadas que ha visto

Cómo funciona por dentro:
  - Tu cuenta de Telegram (con Telethon) recibe los mensajes NUEVOS de los grupos que elijas. No baja historial:
    bajar el historial de cientos de grupos es la forma más rápida de que Telegram te bloquee la cuenta.
  - De cada mensaje saca las direcciones de Solana. Si DexScreener o pump.fun conocen ese token, te avisa
    con el nombre, la capitalización, la liquidez y el grupo. Cada grupo y contrato, una sola vez.
  - Si otro grupo de los tuyos ya lo había llamado, te dice cuál y hace cuánto (eso es eco, no confirmación).
  - Apunta cada llamada en "llamadas.csv", para que puedas medir tú después a qué llegó cada una.

Esto NO es consejo financiero. Es una herramienta para mirar.
"""
import os, re, csv, json, time, asyncio, threading
import requests
from telethon import TelegramClient, events


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
API_ID = os.environ.get("TELEGRAM_API_ID", "").strip()
API_HASH = os.environ.get("TELEGRAM_API_HASH", "").strip()
BOT = "https://api.telegram.org/bot%s/" % TOKEN
LISTA = os.path.join(AQUI, "escuchando.json")
LLAMADAS = os.path.join(AQUI, "llamadas.csv")
DIRECCION = re.compile(r"[1-9A-HJ-NP-Za-km-z]{32,44}")
NO_SON_MEMES = {"So11111111111111111111111111111111111111112",   # pragma: allowlist secret
                "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",   # pragma: allowlist secret
                "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"}   # pragma: allowlist secret

misgrupos = {}          # número -> nombre, de la última vez que pediste /grupos
vistos = {}             # contrato -> [(hora, grupo)], para saber quién lo llamó antes
ultimas = []            # las últimas llamadas, para /ultimos
cerrojo = threading.Lock()


# ───────────────────────────────────────────────── la lista de grupos que escuchas
def leer_lista():
    try:
        return {int(k): v for k, v in json.load(open(LISTA)).items()}
    except Exception:
        return {}


def guardar_lista(d):
    json.dump({str(k): v for k, v in d.items()}, open(LISTA, "w"), indent=1, ensure_ascii=False)


# ───────────────────────────────────────────────── tu bot
def telegram(metodo, **datos):
    try:
        return requests.post(BOT + metodo, json=datos, timeout=60).json()
    except Exception:
        return {}


def avisar(texto):
    telegram("sendMessage", chat_id=MI_ID, text=texto, parse_mode="HTML", disable_web_page_preview=True)


# ───────────────────────────────────────────────── qué token es
def num(x, d=0.0):
    try:
        return float(x)
    except Exception:
        return d


def dinero(x):
    if not x: return "?"
    if x >= 1e6: return "%.2f M$" % (x / 1e6)
    if x >= 1e3: return "%.1f K$" % (x / 1e3)
    return "%.0f $" % x


def ficha_token(ca):
    """Nombre, capitalización y liquidez. Primero DexScreener; si no lo conoce, pump.fun (sigue en la curva).
    Si no lo conoce nadie, no es un token (será una billetera o basura) y devuelve None."""
    try:
        pares = requests.get("https://api.dexscreener.com/latest/dex/tokens/" + ca, timeout=15).json().get("pairs") or []
    except Exception:
        pares = []
    pares = [p for p in pares if (p.get("baseToken") or {}).get("address") == ca]
    if pares:
        p = max(pares, key=lambda p: num((p.get("liquidity") or {}).get("usd")))
        b = p.get("baseToken") or {}
        return {"simbolo": b.get("symbol") or ca[:6], "nombre": b.get("name") or "",
                "mc": num(p.get("marketCap") or p.get("fdv")), "liq": num((p.get("liquidity") or {}).get("usd"))}
    d = {}
    try:   # pump.fun está detrás de Cloudflare: con curl_cffi se hace pasar por un navegador normal.
        from curl_cffi import requests as cr          # Cloudflare a veces dice que no a la primera: se insiste.
        for intento in range(4):                      # y la ruta cambia de vez en cuando (17-nov-2026: coins-v3)
            for ruta in ("coins-v3", "coins-v2"):
                r = cr.get("https://frontend-api-v3.pump.fun/%s/%s" % (ruta, ca), impersonate="chrome", timeout=15)
                if r.status_code == 200 and r.json().get("mint") == ca:
                    d = r.json(); break
            if d:
                break
            time.sleep(2)
    except Exception:
        d = {}
    if d.get("mint") == ca:
        return {"simbolo": d.get("symbol") or ca[:6], "nombre": d.get("name") or "",
                "mc": num(d.get("usd_market_cap")), "liq": 0}
    return None


def contratos(texto):
    """Las direcciones de Solana que hay en el mensaje (también las que van dentro de un enlace)."""
    out = []
    for c in DIRECCION.findall(texto or ""):
        if c in NO_SON_MEMES or c == c.lower() or c == c.upper() or c in out:
            continue        # una dirección de verdad mezcla mayúsculas y minúsculas
        out.append(c)
    return out


def hace(segundos):
    if segundos < 90: return "%d s" % segundos
    if segundos < 5400: return "%d min" % (segundos / 60)
    return "%.1f h" % (segundos / 3600)


def apuntar(ahora, grupo, ca, f):
    nuevo = not os.path.exists(LLAMADAS)
    with open(LLAMADAS, "a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if nuevo:
            w.writerow(["hora", "grupo", "contrato", "simbolo", "capitalizacion_al_llamar", "liquidez_al_llamar"])
        w.writerow([time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ahora)), grupo, ca, f["simbolo"], int(f["mc"]), int(f["liq"])])


def llamada(grupo, ca):
    """Un contrato nuevo en un grupo: mirar qué es y avisar."""
    with cerrojo:                                # varios mensajes pueden llegar a la vez
        antes = vistos.setdefault(ca, [])
        if any(g == grupo for _, g in antes):
            return                               # este grupo ya lo había llamado: no repetir
        previos = list(antes)
        ahora = time.time()
        antes.append((ahora, grupo))             # se apunta YA, antes de preguntar qué token es
    f = ficha_token(ca)
    if not f:
        return
    texto = "📣 <b>%s</b> llama <b>%s</b> %s\n   capitalización %s · liquidez %s\n   <code>%s</code>" % (
        grupo, f["simbolo"], ("(%s)" % f["nombre"]) if f["nombre"] and f["nombre"] != f["simbolo"] else "",
        dinero(f["mc"]), dinero(f["liq"]) if f["liq"] else "todavía en pump.fun", ca)
    if previos:
        h, g = previos[0]
        texto += "\n   🔁 ya lo llamó <b>%s</b> hace %s" % (g, hace(ahora - h))
    texto += "\n   <a href='https://dexscreener.com/solana/%s'>DexScreener</a> · <a href='https://pump.fun/coin/%s'>pump.fun</a>" % (ca, ca)
    ultimas.append("%s · %s · %s · %s" % (time.strftime("%H:%M", time.localtime(ahora)), grupo, f["simbolo"], dinero(f["mc"])))
    del ultimas[:-15]
    apuntar(ahora, grupo, ca, f)
    avisar(texto)


# ───────────────────────────────────────────────── lo que le escribes a tu bot
def escuchar_bot(cuenta, bucle):
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
            numeros = [int(x) for x in re.findall(r"-?\d{6,}", texto)]
            if texto.startswith("/grupos"):
                palabra = texto[7:].strip().lower()
                grupos = asyncio.run_coroutine_threadsafe(mis_grupos(cuenta), bucle).result(120)
                misgrupos.clear(); misgrupos.update(grupos)
                elegidos = [(i, n) for i, n in grupos.items() if palabra in n.lower()][:40]
                avisar("📋 Estás en %d grupos y canales%s:\n%s\n\nPara escuchar uno: /escucha <número>" % (
                    len(grupos), (" (con «%s»: %d)" % (palabra, len(elegidos))) if palabra else "",
                    "\n".join("<code>%s</code> %s" % (i, n) for i, n in elegidos) or "ninguno"))
            elif texto.startswith("/escucha"):
                if any(i not in misgrupos for i in numeros):
                    misgrupos.update(asyncio.run_coroutine_threadsafe(mis_grupos(cuenta), bucle).result(120))
                for i in numeros:
                    lista[i] = misgrupos.get(i) or str(i)
                guardar_lista(lista)
                avisar("👂 Escuchando %d grupos. Te aviso de cada contrato nuevo que publiquen." % len(lista))
            elif texto.startswith("/quita"):
                for i in numeros:
                    lista.pop(i, None)
                guardar_lista(lista); avisar("Hecho. Escuchando %d." % len(lista))
            elif texto.startswith("/lista"):
                avisar("👂 Escuchando %d:\n%s" % (len(lista), "\n".join("• %s <code>%s</code>" % (n, i) for i, n in lista.items()) or "ninguno"))
            elif texto.startswith("/ultimos"):
                avisar("🕘 Últimas llamadas:\n" + ("\n".join(ultimas[-10:]) or "todavía ninguna"))
            else:
                avisar("Órdenes: /grupos [palabra] · /escucha <número> · /quita <número> · /lista · /ultimos")
        if not r:
            time.sleep(3)


async def mis_grupos(cuenta):
    out = {}
    async for d in cuenta.iter_dialogs():
        if not d.is_user:
            out[d.id] = d.name or str(d.id)
    return out


# ───────────────────────────────────────────────── tu cuenta escuchando
async def principal():
    cuenta = TelegramClient(os.path.join(AQUI, "sesion_grupos"), int(API_ID), API_HASH)
    await cuenta.start()            # la primera vez: tu teléfono y el código que te manda Telegram
    yo = await cuenta.get_me()
    print("Escuchando con la cuenta de", yo.first_name)

    @cuenta.on(events.NewMessage())
    async def nuevo(ev):
        lista = leer_lista()
        if ev.chat_id not in lista:
            return
        for ca in contratos(ev.raw_text):
            await asyncio.to_thread(llamada, lista[ev.chat_id], ca)

    threading.Thread(target=escuchar_bot, args=(cuenta, asyncio.get_running_loop()), daemon=True).start()
    print("En marcha. Escríbele /grupos a tu bot. (Ctrl+C para parar)")
    await cuenta.run_until_disconnected()


def main():
    falta = [k for k, v in (("TELEGRAM_BOT_TOKEN", TOKEN), ("TELEGRAM_API_ID", API_ID), ("TELEGRAM_API_HASH", API_HASH)) if not v]
    if falta:
        print("Falta en el fichero .env:", ", ".join(falta)); return
    asyncio.run(principal())


if __name__ == "__main__":
    main()
