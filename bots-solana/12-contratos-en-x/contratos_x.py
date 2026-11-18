#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quién está nombrando qué token en X (Twitter), en tu Telegram y sin cuenta de X.
Canal de YouTube: Profesor Diógenes · sección "Bots de Solana", vídeo 12.

    python3 contratos_x.py

De dónde sale: GMGN tiene en su web un apartado, el "Twitter tracker", que sigue a miles de cuentas de X
(influencers, traders, fundadores, medios…) y marca en qué mensajes se nombra un token. Este bot lee ESE
apartado, el mismo que ves tú en la web. No toca X, no necesita cuenta de X y no necesita ninguna clave.

Cómo se usa, desde tu bot:
  /x                   -> cómo lo tienes puesto
  /seguidores 10000    -> solo cuentas con al menos estos seguidores
  /minimo 20000        -> solo tokens que valgan al menos esto (en dólares) cuando los nombran
  /sigue ansem         -> avisa SOLO de estas cuentas (puedes poner varias, una por orden)
  /quita ansem         -> deja de seguir a esa cuenta (sin ninguna en la lista, valen todas)
  /repes si|no         -> avisar también cuando otra cuenta nombra un token que ya te avisé
  /ultimos             -> los últimos tokens nombrados y cuántas cuentas distintas llevan

Cómo funciona por dentro:
  - Cada 20 segundos pide a la web de GMGN los últimos mensajes de X que nombran un token de Solana.
    La web no tiene clave, pero está detrás de Cloudflare y solo contesta a navegadores: por eso se usa
    la librería curl_cffi, que hace la petición con la misma "huella" que un Chrome de verdad.
  - Cada mensaje trae quién lo escribe, cuántos seguidores tiene, el texto, y el token con su precio y su
    capitalización EN ESE MOMENTO. Con eso se puede medir luego sin hacerse trampas.
  - Te avisa y lo apunta en "x.csv" (la libreta del vídeo 15 se lo traga con /importa).

Dos avisos honrados:
  - Esto NO es una API oficial. Es la misma dirección que usa la web de GMGN por dentro. Pueden cambiarla
    o cerrarla cuando quieran, y si le preguntas demasiado deprisa te bloquean un rato. No bajes de 15 s.
  - Solo salen las cuentas que GMGN sigue. Si tu cuenta favorita no está en su lista, aquí no aparece.

Esto NO es consejo financiero. Es una herramienta para mirar.
"""
import os, re, csv, json, time, threading
import requests
from curl_cffi import requests as navegador     # pide como un Chrome de verdad


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
BOT = "https://api.telegram.org/bot%s/" % TOKEN
AJUSTES = os.path.join(AQUI, "ajustes.json")
REGISTRO = os.path.join(AQUI, "x.csv")
CADA_SEGUNDOS = max(15, int(os.environ.get("CADA_SEGUNDOS") or 20))

# El apartado "Twitter tracker" de la web de GMGN: mensajes que nombran un token de Solana
FUENTE = ("https://gmgn.ai/vas/api/v1/twitter/messages?from_app=gmgn&os=web&has_token=true&chain=sol"
          "&tw_types=tweet&tw_types=quote&tw_types=reply&tw_types=repost")
QUE_HACE = {"tweet": "escribe", "quote": "cita", "reply": "responde", "repost": "repostea"}
ETIQUETA = {"kol": "influencer", "trader": "trader", "master": "maestro", "politics": "política", "media": "medio",
            "companies": "empresa", "founder": "fundador", "exchange": "exchange", "celebrity": "famoso"}

nombrados = {}          # contrato -> {"simbolo":…, "cuentas": {cuenta: hora}, "mc": la primera capitalización}


# ───────────────────────────────────────────────── ajustes
def ajustes():
    a = {"seguidores": 10000, "minimo": 20000, "cuentas": [], "repes": False}
    try:
        a.update(json.load(open(AJUSTES)))
    except Exception:
        pass
    return a


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


def mensajes_de_x():
    """Los últimos 20 mensajes de X que nombran un token de Solana, según el Twitter tracker de GMGN."""
    try:
        r = navegador.get(FUENTE, impersonate="chrome", timeout=25)
        if "json" not in (r.headers.get("content-type") or ""):
            print(time.strftime("%H:%M:%S"), "GMGN no contesta con datos (código %s). Espero." % r.status_code)
            return None
        d = r.json()
    except Exception as e:
        print(time.strftime("%H:%M:%S"), "fallo al leer GMGN:", str(e)[:80]); return None
    if d.get("code") != 0:
        print("GMGN contesta", d.get("code"), d.get("reason")); return None
    return d.get("data") or []


def dinero(x):
    if not x: return "?"
    if x >= 1e6: return "%.2f M$" % (x / 1e6)
    if x >= 1e3: return "%.1f K$" % (x / 1e3)
    return "%.0f $" % x


def limpio(t):
    return (t or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ───────────────────────────────────────────────── el vigía
def vigilar():
    vistos = set()
    estrenado = False                    # lo que ya había al arrancar no se avisa: solo lo nuevo
    while True:
        lista = mensajes_de_x()
        if lista is None:
            time.sleep(60); continue
        a = ajustes()
        solo = {c.lower() for c in a["cuentas"]}
        for m in sorted(lista, key=lambda m: int(m.get("tw_timestamp") or 0)):
            if m.get("id") in vistos:
                continue
            vistos.add(m.get("id"))
            tk = m.get("token") or {}
            ca = tk.get("ca")
            if not ca or tk.get("chain") != "sol":
                continue
            quien = m.get("user") or {}
            cuenta = quien.get("screen_name") or "?"
            seguidores = int(quien.get("followers") or 0)
            mc = float(tk.get("mcap") or 0)
            hora = int(int(m.get("tw_timestamp") or 0) / 1000) or int(time.time())
            ficha = nombrados.setdefault(ca, {"simbolo": tk.get("symbol") or ca[:6], "cuentas": {}, "mc": mc})
            ya_estaba = bool(ficha["cuentas"])
            cuenta_nueva = cuenta not in ficha["cuentas"]
            ficha["cuentas"].setdefault(cuenta, hora)
            if not estrenado:
                continue
            # se apunta TODO lo que nombra un token, pase o no tus filtros: así luego puedes medir también lo descartado
            nuevo = not os.path.exists(REGISTRO)
            with open(REGISTRO, "a", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh)
                if nuevo:
                    w.writerow(["hora", "contrato", "simbolo", "cuenta", "seguidores", "tipo", "capitalizacion"])
                w.writerow([time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(hora)), ca, ficha["simbolo"], cuenta,
                            seguidores, m.get("tw_type"), int(mc)])
            if solo and cuenta.lower() not in solo:
                continue
            if not solo and seguidores < int(a["seguidores"]):
                continue
            if mc < float(a["minimo"]):
                continue
            if ya_estaba and not (a["repes"] and cuenta_nueva):
                continue
            texto = ((m.get("content") or {}).get("text") or (m.get("source_content") or {}).get("text") or "").strip()
            if len(texto) > 280:
                texto = texto[:280] + "…"
            etiquetas = ", ".join(ETIQUETA.get(e, e) for e in (m.get("user_tags") or []))
            cabecera = "🐦 <b>@%s</b> %s" % (limpio(cuenta), QUE_HACE.get(m.get("tw_type"), m.get("tw_type")))
            if ya_estaba:
                cabecera += " · ya van %d cuentas con este token" % len(ficha["cuentas"])
            avisar("%s\n   %s seguidores%s\n\n<i>%s</i>\n\n<b>%s</b> · capitalización %s\n<code>%s</code>\n"
                   "<a href='https://x.com/%s/status/%s'>ver en X</a> · <a href='https://gmgn.ai/sol/token/%s'>GMGN</a> · "
                   "<a href='https://dexscreener.com/solana/%s'>DexScreener</a>" % (
                       cabecera, "{:,}".format(seguidores).replace(",", "."), (" · " + etiquetas) if etiquetas else "",
                       limpio(texto), limpio(ficha["simbolo"]), dinero(mc), ca, cuenta, m.get("tweet_id"), ca, ca))
        estrenado = True
        if len(vistos) > 20000:
            vistos.clear()
        time.sleep(CADA_SEGUNDOS)


def ultimos():
    if not nombrados:
        return "Todavía no he visto ningún token nombrado. Dame un minuto."
    filas = sorted(nombrados.items(), key=lambda kv: -max(kv[1]["cuentas"].values()))[:12]
    return "🐦 Últimos tokens nombrados en X:\n" + "\n".join(
        "• <b>%s</b> · %d cuenta%s · %s cuando lo vi\n   <code>%s</code>" % (
            limpio(f["simbolo"]), len(f["cuentas"]), "" if len(f["cuentas"]) == 1 else "s", dinero(f["mc"]), ca)
        for ca, f in filas)


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
            texto = (m.get("text") or "").strip()
            if not chat:
                continue
            if not MI_ID:
                telegram("sendMessage", chat_id=chat, text="Tu número de usuario es %s. Ponlo en TELEGRAM_MI_ID del .env y vuelve a arrancar." % quien)
                continue
            if quien != MI_ID:
                continue
            a = ajustes()
            orden = texto.lower().split()[0] if texto else ""
            palabra = (texto.split() + ["", ""])[1].lstrip("@")
            numero = re.sub(r"\D", "", palabra)
            if orden == "/seguidores" and numero:
                a["seguidores"] = int(numero); guardar(a)
            elif orden == "/minimo" and numero:
                a["minimo"] = int(numero); guardar(a)
            elif orden == "/sigue" and palabra:
                a["cuentas"] = sorted(set(a["cuentas"]) | {palabra}); guardar(a)
            elif orden == "/quita" and palabra:
                a["cuentas"] = [c for c in a["cuentas"] if c.lower() != palabra.lower()]; guardar(a)
            elif orden == "/repes" and palabra.lower() in ("si", "sí", "no"):
                a["repes"] = palabra.lower() != "no"; guardar(a)
            elif orden == "/ultimos":
                avisar(ultimos()); continue
            elif orden != "/x":
                avisar("Órdenes: /x · /seguidores 10000 · /minimo 20000 · /sigue cuenta · /quita cuenta · /repes si|no · /ultimos"); continue
            avisar("🐦 Tokens de Solana nombrados en X (Twitter tracker de GMGN)\n• cuentas: %s\n• el token tiene que valer al menos %s\n"
                   "• si otra cuenta nombra uno que ya te avisé: %s" % (
                       ("solo " + ", ".join("@" + c for c in a["cuentas"])) if a["cuentas"] else
                       "todas las que tengan %s seguidores o más" % "{:,}".format(a["seguidores"]).replace(",", "."),
                       dinero(a["minimo"]), "te aviso" if a["repes"] else "no te aviso"))
        if not r:
            time.sleep(3)


def main():
    if not TOKEN:
        print("Falta TELEGRAM_BOT_TOKEN en el fichero .env"); return
    print("Mirando X a través de GMGN cada %d s. Escríbele /x a tu bot. (Ctrl+C para parar)" % CADA_SEGUNDOS)
    threading.Thread(target=escuchar_bot, daemon=True).start()
    vigilar()


if __name__ == "__main__":
    main()
