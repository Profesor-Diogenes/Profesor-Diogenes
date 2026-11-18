#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EL BOT DEFINITIVO: todas las piezas de la serie en un solo bot de Telegram, con menú.
Canal de YouTube: Profesor Diógenes · sección "Bots de Solana", vídeo 19.

    python3 definitivo.py

No hay código nuevo de análisis: este programa es una CENTRALITA. Arranca los programas de los vídeos
anteriores (tienen que estar en sus carpetas, al lado de esta) y reparte entre ellos lo que tú escribes.
Un solo bot, una sola clave, un solo chat.

Cómo se usa, desde tu bot:
  (pegas un contrato o una billetera)  -> te pregunta con botones qué quieres hacer con él:
                                          ficha, por dentro, seguridad, holders, el dev, analizar o seguir la
                                          billetera, apuntarlo en la libreta, comprarlo en papel, vigilar sus ventas
  /menu                -> las secciones: vigía de billeteras, tokens que nacen, señales, X, ventas gordas,
                          criba, libreta, medir, papel. Entras en una y sus órdenes son las de su vídeo.
  /estado              -> qué piezas están encendidas
  /apaga senales       -> apaga una pieza (deja de avisar y de gastar preguntas)
  /junta               -> mete en la libreta todo lo que han apuntado las demás piezas

Lo que NO hay: ninguna inteligencia artificial y ninguna compra de verdad. El bot mira, apunta, avisa y
juega en papel. Decidir, decides tú.

Aviso de límites: todas las piezas comparten las mismas fuentes gratis (el nodo público de Solana da una
pregunta por segundo; GMGN y GeckoTerminal también cortan). Cuantas más piezas enciendas a la vez, más se
estorban. Enciende las que estés usando.

Esto NO es consejo financiero. Es una herramienta para mirar.
"""
import os, re, sys, json, time, glob, shutil, queue, threading, subprocess, importlib.util
import requests

AQUI = os.path.dirname(os.path.abspath(__file__))
SERIE = os.path.dirname(AQUI)                      # la carpeta donde están todas las del curso


def cargar_env():
    ruta = os.path.join(AQUI, ".env")
    if os.path.exists(ruta):
        for linea in open(ruta, encoding="utf-8"):
            if "=" in linea and not linea.strip().startswith("#"):
                k, v = linea.strip().split("=", 1)
                if v.strip():
                    os.environ.setdefault(k.strip(), v.strip())


# clave: (carpeta, fichero, nombre en el menú, qué es)
#   "contrato" = le pasas un contrato o una billetera y contesta · "seccion" = tiene sus propias órdenes
PIEZAS = {
    "ficha":     ("01-analizar-contrato-gmgn", "bot.py", "🔎 Ficha", "contrato"),
    "dentro":    ("02-contrato-por-dentro-nodo", "bot.py", "⛓ Por dentro", "contrato"),
    "seguridad": ("10-seguridad-en-la-cadena", "bot.py", "🔐 Seguridad", "contrato"),
    "holders":   ("07-radiografia-de-holders", "bot.py", "🩻 Holders", "contrato"),
    "dev":       ("08-el-dev-en-la-cadena", "bot.py", "👤 El dev", "contrato"),
    "billetera": ("03-analizar-billetera", "bot.py", "👛 Analizar billetera", "contrato"),
    "vigia":     ("11-varias-billeteras-compran-lo-mismo", "coincidencias.py", "👁 Vigía de billeteras", "seccion"),
    "nacen":     ("05-tokens-que-nacen", "nacimientos.py", "🐣 Tokens que nacen", "seccion"),
    "senales":   ("09-senales-de-gmgn", "senales.py", "📡 Señales", "seccion"),
    "x":         ("12-contratos-en-x", "contratos_x.py", "🐦 X", "seccion"),
    "ventas":    ("13-ventas-gordas-en-directo", "ventas_gordas.py", "🔻 Ventas gordas", "seccion"),
    "criba":     ("14-tu-propia-criba", "criba.py", "🪙 Criba", "seccion"),
    "libreta":   ("15-guardar-todo", "libreta.py", "📒 Libreta", "seccion"),
    "medir":     ("16-medir-sin-trampa", "medir.py", "📏 Medir", "seccion"),
    "papel":     ("17-bot-en-papel", "papel.py", "📝 Papel", "seccion"),
}
# qué se puede hacer con un contrato pegado, por orden, en filas de botones
BOTONES_CONTRATO = [["ficha", "seguridad"], ["holders", "dev"], ["dentro", "billetera"],
                    ["vigia", "ventas"], ["libreta", "papel"]]
TEXTO_BOTON = {"vigia": "👁 Seguir billetera", "ventas": "🔻 Vigilar ventas", "libreta": "📒 Apuntar", "papel": "📝 Comprar en papel"}
CONTRATO = re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b")


# ═════════════════════════════════════════════════════════════════════════════════════════════════════
#  MODO HIJO: así arranca la centralita cada pieza. Carga el programa de ese vídeo tal cual y solo le
#  cambia una cosa: en vez de preguntarle a Telegram qué le han escrito, lee lo que le pasa la centralita.
# ═════════════════════════════════════════════════════════════════════════════════════════════════════
def hijo(clave):
    carpeta, fichero = PIEZAS[clave][0], PIEZAS[clave][1]
    ruta = os.path.join(SERIE, carpeta)
    sys.path.insert(0, ruta)
    entrada = sys.stdin                              # por aquí llegan los mensajes, uno por línea
    sys.stdin = open(os.devnull)
    sys.stdout = open(os.path.join(AQUI, "pieza_%s.log" % clave), "a", buffering=1)
    sys.stderr = sys.stdout
    spec = importlib.util.spec_from_file_location("pieza_" + clave, os.path.join(ruta, fichero))
    programa = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(programa)
    cola = queue.Queue()

    def leer():
        for linea in entrada:
            try:
                cola.put(json.loads(linea))
            except ValueError:
                pass
        os._exit(0)                                  # la centralita se ha cerrado: fuera
    threading.Thread(target=leer, daemon=True).start()
    hablar = programa.telegram

    def telegram(metodo, **datos):
        if metodo != "getUpdates":
            return hablar(metodo, **datos)
        try:
            return {"ok": True, "result": [cola.get(timeout=25)]}
        except queue.Empty:
            return {"ok": True, "result": []}
    programa.telegram = telegram
    programa.main()


# ═════════════════════════════════════════════════════════════════════════════════════════════════════
#  LA CENTRALITA
# ═════════════════════════════════════════════════════════════════════════════════════════════════════
cargar_env()
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
MI_ID = os.environ.get("TELEGRAM_MI_ID", "").strip()
BOT = "https://api.telegram.org/bot%s/" % TOKEN
AJUSTES = os.path.join(AQUI, "definitivo.json")
hijos = {}                # clave -> proceso
numero = [1]              # para numerar los mensajes que se reparten
activa = [None]           # la sección en la que estás
pendientes = {}           # id del mensaje con botones -> lo que habías pegado


def ajustes():
    try:
        return json.load(open(AJUSTES))
    except Exception:
        return {"encendidas": ["libreta", "papel"]}


def guardar(a):
    json.dump(a, open(AJUSTES, "w"), indent=1)


def telegram(metodo, **datos):
    try:
        return requests.post(BOT + metodo, json=datos, timeout=60).json()
    except Exception:
        return {}


def decir(texto, botones=None):
    datos = {"chat_id": MI_ID, "text": texto, "parse_mode": "HTML", "disable_web_page_preview": True}
    if botones:
        datos["reply_markup"] = {"inline_keyboard": botones}
    return telegram("sendMessage", **datos)


def viva(clave):
    return clave in hijos and hijos[clave].poll() is None


def arrancar(clave):
    if viva(clave):
        return True
    carpeta, fichero = PIEZAS[clave][0], PIEZAS[clave][1]
    if not os.path.exists(os.path.join(SERIE, carpeta, fichero)):
        decir("No encuentro la carpeta <b>%s</b>. Baja la serie entera del GitHub: las piezas tienen que estar al lado de esta." % carpeta)
        return False
    entorno = dict(os.environ, LIBRETA=os.path.join(SERIE, PIEZAS["libreta"][0], "libreta.db"))
    hijos[clave] = subprocess.Popen([sys.executable, os.path.abspath(__file__), "--hijo", clave],
                                    stdin=subprocess.PIPE, env=entorno, text=True)
    time.sleep(1.5)
    return True


def apagar(clave):
    if viva(clave):
        hijos[clave].terminate()
    hijos.pop(clave, None)


def pasar(clave, texto):
    """Le entrega a una pieza un mensaje, como si se lo hubieras escrito a ella."""
    if not arrancar(clave):
        return
    numero[0] += 1
    yo = int(MI_ID)
    mensaje = {"update_id": numero[0], "message": {"message_id": numero[0], "chat": {"id": yo}, "from": {"id": yo}, "text": texto}}
    try:
        hijos[clave].stdin.write(json.dumps(mensaje) + "\n"); hijos[clave].stdin.flush()
    except Exception:
        apagar(clave); decir("La pieza <b>%s</b> se había caído. Vuelve a intentarlo." % clave)


def menu():
    filas, fila = [], []
    for clave, (_, _, nombre, tipo) in PIEZAS.items():
        if tipo != "seccion":
            continue
        fila.append({"text": ("🟢 " if viva(clave) else "⚪ ") + nombre, "callback_data": "s:" + clave})
        if len(fila) == 2:
            filas.append(fila); fila = []
    if fila:
        filas.append(fila)
    decir("Elige una sección. 🟢 encendida · ⚪ apagada.\nO pégame un contrato o una billetera y te pregunto qué hacer con él.", filas)


def estado():
    a = ajustes()
    decir("🟢 Encendidas ahora: %s\nAl arrancar se encienden solas: %s\nSección en la que estás: %s" % (
        ", ".join(c for c in PIEZAS if viva(c)) or "ninguna", ", ".join(a["encendidas"]) or "ninguna", activa[0] or "ninguna"))


def juntar():
    """Copia a la carpeta de la libreta lo que han ido apuntando las demás piezas y le dice que lo importe."""
    destino = os.path.join(SERIE, PIEZAS["libreta"][0])
    copiados = []
    for clave in ("senales", "x", "criba"):
        for f in glob.glob(os.path.join(SERIE, PIEZAS[clave][0], "*.csv")):
            shutil.copy(f, destino); copiados.append(os.path.basename(f))
    for f in glob.glob(os.path.join(SERIE, "06-leer-grupos-de-telegram", "llamadas.csv")):
        shutil.copy(f, destino); copiados.append("llamadas.csv")
    decir("Le paso a la libreta: %s" % (", ".join(copiados) or "nada todavía (ninguna pieza ha apuntado nada)"))
    if copiados:
        pasar("libreta", "/importa")


def escuchar():
    desde = 0
    while True:
        r = telegram("getUpdates", offset=desde, timeout=50, allowed_updates=["message", "callback_query"])
        for u in r.get("result") or []:
            desde = u["update_id"] + 1
            pulsado = u.get("callback_query")
            m = u.get("message") or (pulsado or {}).get("message") or {}
            quien = str(((pulsado or u.get("message") or {}).get("from") or {}).get("id"))
            chat = (m.get("chat") or {}).get("id")
            if not chat:
                continue
            if not MI_ID:
                telegram("sendMessage", chat_id=chat, text="Tu número de usuario es %s. Ponlo en TELEGRAM_MI_ID del .env y vuelve a arrancar." % quien)
                continue
            if quien != MI_ID:
                continue
            if pulsado:                                           # has tocado un botón
                telegram("answerCallbackQuery", callback_query_id=pulsado["id"])
                tipo, _, clave = (pulsado.get("data") or "").partition(":")
                if clave not in PIEZAS:
                    continue
                if tipo == "s":                                   # entrar en una sección
                    activa[0] = clave
                    a = ajustes()
                    if clave not in a["encendidas"]:
                        a["encendidas"].append(clave); guardar(a)
                    decir("Estás en <b>%s</b>. Lo que escribas con / va para esta pieza. Sus órdenes:" % PIEZAS[clave][2])
                    pasar(clave, "/ayuda")
                elif tipo == "c":                                 # hacer algo con lo que pegaste
                    texto = pendientes.get(m.get("message_id"))
                    if texto:
                        pasar(clave, texto)
                continue
            texto = (m.get("text") or "").strip()
            orden = texto.lower().split()[0] if texto else ""
            palabra = (texto.lower().split() + ["", ""])[1]
            if orden in ("/menu", "/start"):
                menu()
            elif orden == "/estado":
                estado()
            elif orden == "/junta":
                juntar()
            elif orden == "/apaga" and palabra in PIEZAS:
                apagar(palabra)
                a = ajustes(); a["encendidas"] = [c for c in a["encendidas"] if c != palabra]; guardar(a)
                if activa[0] == palabra:
                    activa[0] = None
                decir("Apagada: %s" % PIEZAS[palabra][2])
            elif texto.startswith("/"):
                if activa[0]:
                    pasar(activa[0], texto)
                else:
                    decir("Órdenes de la centralita: /menu · /estado · /apaga pieza · /junta\nPara las órdenes de una pieza, entra primero en su sección con /menu.")
            elif CONTRATO.search(texto):
                filas = [[{"text": TEXTO_BOTON.get(c, PIEZAS[c][2]), "callback_data": "c:" + c} for c in fila] for fila in BOTONES_CONTRATO]
                enviado = decir("¿Qué hago con <code>%s</code>?" % CONTRATO.search(texto).group(0), filas)
                pendientes[(enviado.get("result") or {}).get("message_id")] = texto
            elif activa[0]:
                pasar(activa[0], texto)
            else:
                decir("Pégame un contrato o una billetera, o escribe /menu.")
        if not r:
            time.sleep(3)


def main():
    if not TOKEN:
        print("Falta TELEGRAM_BOT_TOKEN en el fichero .env"); return
    print("Centralita en marcha. Escríbele /menu a tu bot. (Ctrl+C para parar)")
    if MI_ID:
        for clave in ajustes()["encendidas"]:
            if clave in PIEZAS:
                arrancar(clave)
    try:
        escuchar()
    finally:
        for clave in list(hijos):
            apagar(clave)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--hijo":
        hijo(sys.argv[2])
    else:
        main()
