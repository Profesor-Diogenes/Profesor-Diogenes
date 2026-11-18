#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LA MINI APP: tu bot de Solana, pero en una pantalla con pestañas dentro de Telegram.
Canal de YouTube: Profesor Diógenes · sección "Bots de Solana", vídeo 20.

    python3 miniapp.py

Qué es una mini app: una página web normal que Telegram abre DENTRO del chat de tu bot. Por eso hacen
falta dos cosas: este programa (que sirve la página y contesta a sus preguntas) y una dirección de
internet con https que apunte a él (un dominio tuyo, o un túnel gratis para probar: mira el README).

Qué enseña, en tres pestañas:
  Analizar  -> pegas un contrato o una billetera y eliges qué mirar. Contestan los programas de los
               vídeos 1, 2, 3, 7, 8 y 10 (tienen que estar en sus carpetas, al lado de esta).
  Libreta   -> lo que tienes apuntado en la libreta del vídeo 15, en una tabla.
  Papel     -> la cartera y el balance del bot en papel del vídeo 17.

Cómo se cambia el aspecto: todo está en "aspecto.json" (título, lema, foto de arriba, colores, qué
pestañas salen y en qué orden) y en "web/index.html". No hace falta saber programar: díselo a Claude.

Quién puede entrar: SOLO TÚ. Telegram le pasa a la página una firma hecha con la clave de tu bot; este
programa la comprueba y mira que el usuario sea TELEGRAM_MI_ID. Sin esa firma no contesta a nadie,
aunque encuentren la dirección.

Aquí no hay ninguna inteligencia artificial y no se compra nada de verdad.
Esto NO es consejo financiero. Es una herramienta para mirar.
"""
import os, io, re, sys, hmac, json, time, hashlib, sqlite3, threading, contextlib, importlib.util
from urllib.parse import parse_qsl
import requests
from flask import Flask, request, jsonify, send_from_directory

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


cargar_env()
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
MI_ID = os.environ.get("TELEGRAM_MI_ID", "").strip()
DIRECCION = os.environ.get("MINIAPP_URL", "").strip()          # https://tudominio.com  (o la del túnel)
PUERTO = int(os.environ.get("MINIAPP_PUERTO", "8080"))

# qué se puede mirar: clave -> (carpeta, fichero, nombre del botón, qué pide)
MIRAR = {
    "ficha":     ("01-analizar-contrato-gmgn", "analizar.py", "🔎 Ficha", "contrato"),
    "seguridad": ("10-seguridad-en-la-cadena", "seguridad.py", "🔐 Seguridad", "contrato"),
    "holders":   ("07-radiografia-de-holders", "radiografia.py", "🩻 Holders", "contrato"),
    "dev":       ("08-el-dev-en-la-cadena", "dev.py", "👤 El dev", "contrato"),
    "dentro":    ("02-contrato-por-dentro-nodo", "por_dentro.py", "⛓ Por dentro", "contrato"),
    "billetera": ("03-analizar-billetera", "billetera.py", "👛 Billetera", "billetera"),
}
LIBRETA = os.path.join(SERIE, "15-guardar-todo", "libreta.db")
PAPEL = os.path.join(SERIE, "17-bot-en-papel", "papel.json")
DIRECCION_SOLANA = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")
UNO_A_LA_VEZ = threading.Lock()                    # las fuentes gratis cortan si corres
programas = {}

app = Flask(__name__, static_folder=None)


# ─────────────────────────────────────────────────────────────────────────────────────────────────────
#  LA PUERTA: comprobar que quien pregunta eres tú
# ─────────────────────────────────────────────────────────────────────────────────────────────────────
def quien_es(firmado):
    """Telegram le da a la página un texto firmado (initData). Si la firma es buena, devuelve el número
    de usuario; si no, None. La firma solo se puede hacer con la clave de TU bot."""
    try:
        datos = dict(parse_qsl(firmado, keep_blank_values=True))
        firma = datos.pop("hash")
        texto = "\n".join("%s=%s" % (k, datos[k]) for k in sorted(datos))
        secreto = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
        buena = hmac.new(secreto, texto.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(buena, firma):
            return None
        if time.time() - int(datos.get("auth_date", 0)) > 86400:      # firmas de más de un día, no
            return None
        return str(json.loads(datos["user"])["id"])
    except Exception:
        return None


def solo_yo():
    quien = quien_es(request.headers.get("X-Telegram", ""))
    if not quien:
        return "Abre esto desde el botón de tu bot en Telegram."
    if not MI_ID:
        return "Tu número de usuario es %s. Ponlo en TELEGRAM_MI_ID del .env y vuelve a arrancar." % quien
    if quien != MI_ID:
        return "Esta mini app es privada."
    return None


# ─────────────────────────────────────────────────────────────────────────────────────────────────────
#  LA PÁGINA
# ─────────────────────────────────────────────────────────────────────────────────────────────────────
@app.route("/")
def pagina():
    r = send_from_directory(os.path.join(AQUI, "web"), "index.html", max_age=0)
    r.headers["Cache-Control"] = "no-cache"            # que el móvil coja siempre la última versión
    return r


@app.route("/web/<path:fichero>")
def ficheros(fichero):
    return send_from_directory(os.path.join(AQUI, "web"), fichero)


@app.route("/aspecto")
def aspecto():
    a = json.load(open(os.path.join(AQUI, "aspecto.json"), encoding="utf-8"))
    a["botones"] = [{"clave": k, "nombre": v[2], "pide": v[3]} for k, v in MIRAR.items()
                    if os.path.exists(os.path.join(SERIE, v[0], v[1]))]
    return jsonify(a)


# ─────────────────────────────────────────────────────────────────────────────────────────────────────
#  LO QUE PREGUNTA LA PÁGINA
# ─────────────────────────────────────────────────────────────────────────────────────────────────────
@app.route("/api/mirar", methods=["POST"])
def mirar():
    no = solo_yo()
    if no:
        return jsonify({"error": no}), 403
    d = request.get_json(silent=True) or {}
    clave, direccion = d.get("que"), (d.get("direccion") or "").strip()
    if clave not in MIRAR or not DIRECCION_SOLANA.match(direccion):
        return jsonify({"error": "Pega una dirección de Solana y elige qué mirar."}), 400
    carpeta, fichero = MIRAR[clave][0], MIRAR[clave][1]
    salida = io.StringIO()
    with UNO_A_LA_VEZ:
        if clave not in programas:                     # el programa de ese vídeo, tal cual
            sys.path.insert(0, os.path.join(SERIE, carpeta))
            spec = importlib.util.spec_from_file_location("pieza_" + clave, os.path.join(SERIE, carpeta, fichero))
            programas[clave] = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(programas[clave])
        with contextlib.redirect_stdout(salida):
            try:
                programas[clave].main(direccion)
            except Exception as e:
                print("Algo ha fallado: %s" % e)
    return jsonify({"texto": salida.getvalue()})


@app.route("/api/libreta", methods=["POST"])
def libreta():
    no = solo_yo()
    if no:
        return jsonify({"error": no}), 403
    if not os.path.exists(LIBRETA):
        return jsonify({"filas": [], "aviso": "Todavía no hay libreta. Es la del vídeo 15: arráncala y apunta algo."})
    c = sqlite3.connect("file:%s?mode=ro" % LIBRETA, uri=True)      # solo leer: la libreta es de su bot
    filas = []
    for contrato, simbolo, visto, origen, antes, vivo in c.execute(
            "SELECT contrato, simbolo, visto, origen, capitalizacion, vivo FROM contratos ORDER BY visto DESC LIMIT 60"):
        ahora = c.execute("SELECT capitalizacion FROM fotos WHERE contrato=? ORDER BY hora DESC LIMIT 1", (contrato,)).fetchone()
        filas.append({"contrato": contrato, "simbolo": simbolo or "?", "visto": visto, "origen": origen or "",
                      "antes": antes, "ahora": ahora[0] if ahora else None, "vivo": bool(vivo)})
    total = c.execute("SELECT COUNT(*) FROM contratos").fetchone()[0]
    c.close()
    return jsonify({"filas": filas, "total": total})


@app.route("/api/papel", methods=["POST"])
def papel():
    no = solo_yo()
    if no:
        return jsonify({"error": no}), 403
    if not os.path.exists(PAPEL):
        return jsonify({"aviso": "Todavía no has jugado en papel. Es el bot del vídeo 17."})
    p = json.load(open(PAPEL, encoding="utf-8"))
    cerradas = p.get("cerradas") or []
    ganadas = sum(1 for o in cerradas if o.get("recuperado", 0) > o.get("sol", 0))
    resultado = sum(o.get("recuperado", 0) - o.get("sol", 0) for o in cerradas)
    return jsonify({"plan": p.get("plan"), "abiertas": list((p.get("abiertas") or {}).values()),
                    "cerradas": cerradas[-30:][::-1], "ganadas": ganadas, "resultado": resultado})


# ─────────────────────────────────────────────────────────────────────────────────────────────────────
def poner_boton():
    """Le dice a Telegram que el botón de menú de tu bot abra la mini app. Solo en TU chat con el bot."""
    datos = {"menu_button": {"type": "web_app", "text": "Abrir", "web_app": {"url": DIRECCION}}}
    if MI_ID:
        datos["chat_id"] = int(MI_ID)
    r = requests.post("https://api.telegram.org/bot%s/setChatMenuButton" % TOKEN, timeout=30, json=datos).json()
    print("Botón de menú del bot -> %s : %s" % (DIRECCION, "puesto" if r.get("ok") else r.get("description")))


def main():
    if not TOKEN:
        print("Falta TELEGRAM_BOT_TOKEN en el fichero .env"); return
    if DIRECCION.startswith("https://"):
        poner_boton()
    else:
        print("Sin MINIAPP_URL (tiene que empezar por https://) no pongo el botón en el bot. Mira el README.")
    print("Mini app en marcha en el puerto %d. (Ctrl+C para parar)" % PUERTO)
    try:
        from waitress import serve
        serve(app, host="127.0.0.1", port=PUERTO, threads=8)
    except ImportError:
        app.run(host="127.0.0.1", port=PUERTO, threaded=True)


if __name__ == "__main__":
    main()
