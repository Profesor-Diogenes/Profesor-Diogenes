"""Comentarios para tus redes que escribe Claude, pero que solo salen si tú los apruebas.

Uso:
  python comentarios.py encargo          -> las 5 cuentas de Instagram y las 5 de X de hoy
  python comentarios.py posts            -> qué posts recogidos se pueden comentar (lo viejo, fuera)
  python comentarios.py filtro           -> pasa por el filtro las frases de frases_prueba.txt
  python comentarios.py filtro "FRASE"   -> pasa por el filtro una frase tuya
  python comentarios.py escribir         -> Claude escribe dos opciones por post y las filtra
"""
import json
import os
import random
import re
import shutil
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

CARPETA = Path(__file__).resolve().parent
load_dotenv(CARPETA / ".env")

CUENTAS = CARPETA / "cuentas.txt"
POSTS = CARPETA / os.getenv("POSTS", "posts_recogidos.json")
ESTADO = CARPETA / "estado.json"        # opciones, aprobadas y publicadas
MEMORIA = CARPETA / "memoria.txt"       # lo que ya se ha publicado, para no repetirse
FRASES_PRUEBA = CARPETA / "frases_prueba.txt"
TOPE_ME_GUSTA = int(os.getenv("TOPE_ME_GUSTA", "20"))
CLAUDE = os.getenv("CLAUDE_ORDEN", "claude")


# ---------- Paso 2: el encargo diario ----------
def leer_cuentas():
    """cuentas.txt: una cuenta por línea, debajo de [instagram] o de [x]."""
    redes, actual = {"instagram": [], "x": []}, None
    for linea in CUENTAS.read_text(encoding="utf-8").splitlines():
        linea = linea.split("#", 1)[0].strip()
        if not linea:
            continue
        if linea.startswith("[") and linea.endswith("]"):
            actual = linea[1:-1].strip().lower()
            redes.setdefault(actual, [])
        elif actual:
            redes[actual].append(linea.lstrip("@"))
    return redes


def encargo(dia):
    """5 cuentas de Instagram y 5 de X. Cambian cada día, pero el mismo día sale siempre la misma lista."""
    r = random.Random(str(dia))
    redes = leer_cuentas()
    return {
        "dia": str(dia),
        "instagram": r.sample(redes["instagram"], min(5, len(redes["instagram"]))),
        "x": r.sample(redes["x"], min(5, len(redes["x"]))),
        "tope_me_gusta": TOPE_ME_GUSTA,
    }


# ---------- Paso 3: lo viejo no se comenta ----------
MAX_DIAS = {"instagram": 4, "x": 2}


def leer_posts():
    if not POSTS.exists():
        sys.exit(f"No encuentro {POSTS.name}. Copia ahí los posts recogidos (mira posts_ejemplo.json).")
    posts = json.loads(POSTS.read_text(encoding="utf-8"))
    for p in posts:
        p["fecha"] = datetime.fromisoformat(p["fecha"])
    return posts


def vale(post, ahora):
    """Instagram: 4 días o menos y sin fijados. X: 2 días o menos."""
    if post.get("fijado"):
        return False
    return ahora - post["fecha"] <= timedelta(days=MAX_DIAS[post["red"]])


def hoy():
    """El día de hoy. Para probar con los ejemplos, pon HOY=AAAA-MM-DD en el .env."""
    return os.getenv("HOY", "").strip() or str(date.today())


def ahora():
    return datetime.fromisoformat(hoy() + "T12:00") if os.getenv("HOY", "").strip() else datetime.now()


# ---------- Paso 4: lo que se le pide a Claude por cada post ----------
INSTRUCCIONES = """Lee este post y escribe DOS comentarios de tipo distinto
(un dato, un matiz, una pregunta o una broma sobre algo concreto del post).
Antes, mira la memoria con lo que ya dijiste y no te repitas.
Normas: de 4 a 25 palabras, que se note que has leído el post,
habla como un colega de redes, no como un sabio: nada de metáforas ni frases redondas.
Una sola idea por comentario, sobre lo que dice el post, sin inventar nada.
Nada de venta, ni enlaces, ni etiquetas, ni menciones.
Ejemplo bueno: "¿Y con harina de avena también sale así de esponjoso?"
Ejemplo malo: "Una oda a la repostería que nos recuerda que la vida es dulce."
Contesta SOLO con dos líneas, así:
A: primer comentario
B: segundo comentario"""


def pedir_a_claude(post, memoria):
    texto = (INSTRUCCIONES
             + "\n\nMEMORIA (lo que ya dijiste otros días):\n" + ("\n".join(memoria[-50:]) or "(vacía)")
             + f"\n\nPOST de {post['cuenta']} en {post['red']}:\n{post['texto']}")
    orden = shutil.which(CLAUDE)
    if not orden:
        sys.exit(f"No encuentro Claude Code ('{CLAUDE}'). Instálalo o pon su ruta en CLAUDE_ORDEN del .env.")
    r = subprocess.run([orden, "-p", texto], capture_output=True, text=True, encoding="utf-8", timeout=300)
    if r.returncode != 0:
        raise RuntimeError(f"Claude Code ha fallado: {r.stderr.strip()[:300]}")
    opciones = {}
    for linea in r.stdout.splitlines():
        m = re.match(r"\s*\**([AB])\**\s*[:)]\s*(.+)", linea)
        if m:
            texto = re.sub(r"^\**[AB]\**\s*[:)]\**\s*", "", m.group(2).strip())  # quita un "B:" repetido
            opciones[m.group(1)] = texto.strip().strip('"')
    return opciones


# ---------- Paso 5: el quitador de pinta de máquina ----------
CAMBIOS = {"—": ",", "–": ",", "“": '"', "”": '"', "‘": "'", "’": "'"}
FOLLETO = ["sin lugar a dudas", "fascinante", "cabe destacar", "en definitiva", "sin duda alguna"]
VENTA = ["link en bio", "enlace en", "descuento", "oferta", "sígueme", "sigueme", "compra ya", "escríbeme"]


def limpia(t):
    """Quita lo que se puede arreglar: rayas largas, comillas tipográficas y frases de folleto."""
    for a, b in CAMBIOS.items():
        t = t.replace(a, b)
    for f in FOLLETO:
        t = re.sub(r"\s*,?\s*" + f + r"\s*,?", " ", t, flags=re.I)
    t = re.sub(r"\s+", " ", t).replace(" ,", ",").strip(" ,")
    return t[:1].upper() + t[1:]


def descarta(t):
    """Si la opción no tiene arreglo, dice por qué. Si vale, devuelve None."""
    s = t.lower()
    if s.startswith("gran post"):
        return 'empieza con "gran post"'
    if re.search(r"no es solo .+, es ", s):
        return '"no es solo esto, es lo otro"'
    if re.search(r"\w+, \w+ y \w+", s):
        return "lista de tres"
    if "\U0001F680" in t:
        return "emoji de cohete"
    if "http" in s or "www." in s or "#" in t or "@" in t:
        return "enlace, etiqueta o mención"
    if any(v in s for v in VENTA):
        return "suena a venta"
    n = len(t.split())
    if n < 4 or n > 25:
        return f"{n} palabras (tienen que ser de 4 a 25)"
    return None


def filtra(t, memoria=()):
    """Devuelve (texto_limpio, None) si vale, o (texto, motivo) si va fuera."""
    motivo = descarta(t)
    if motivo:
        return t, motivo
    limpio = limpia(t)
    if limpio.lower() in {m.lower() for m in memoria}:
        return t, "ya lo dijiste otro día"
    return limpio, None


# ---------- Estado y memoria ----------
def leer_estado():
    return json.loads(ESTADO.read_text(encoding="utf-8")) if ESTADO.exists() else {}


def guardar_estado(estado):
    tmp = ESTADO.with_suffix(".tmp")
    tmp.write_text(json.dumps(estado, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(ESTADO)


def leer_memoria():
    if not MEMORIA.exists():
        return []
    return [l.strip() for l in MEMORIA.read_text(encoding="utf-8").splitlines() if l.strip()]


def apuntar_en_memoria(texto):
    with MEMORIA.open("a", encoding="utf-8") as f:
        f.write(texto.replace("\n", " ") + "\n")


# ---------- Órdenes ----------
def escribir():
    posts, estado, memoria = leer_posts(), leer_estado(), leer_memoria()
    momento = ahora()
    nuevos = 0
    for p in posts:
        if p["id"] in estado or not vale(p, momento):
            continue
        try:
            crudas = pedir_a_claude(p, memoria)
        except Exception as e:  # un post que falla no para los demás
            print(f"{p['id']}: {e}")
            continue
        opciones = {}
        for letra, texto in crudas.items():
            limpio, motivo = filtra(texto, memoria)
            if motivo:
                print(f"{p['id']} opción {letra} FUERA ({motivo}): {texto}")
            else:
                opciones[letra] = limpio
        if not opciones:
            print(f"{p['id']}: ninguna opción ha pasado el filtro, este post se salta hoy.")
            continue
        estado[p["id"]] = {"dia": hoy(), "cuenta": p["cuenta"], "red": p["red"],
                           "enlace": p.get("enlace", ""), "post": p["texto"],
                           "opciones": opciones, "estado": "pendiente"}
        guardar_estado(estado)
        nuevos += 1
        print(f"{p['id']}: {len(opciones)} opción(es) listas")
    print(f"Listo: {nuevos} post(s) con opciones esperando tu OK. Mándalas con: python bot.py enviar")


def main():
    args = sys.argv[1:]
    if args[:1] == ["encargo"]:
        print(json.dumps(encargo(hoy()), ensure_ascii=False, indent=1))
    elif args[:1] == ["posts"]:
        momento = ahora()
        for p in leer_posts():
            dias = (momento - p["fecha"]).days
            fij = " (fijado)" if p.get("fijado") else ""
            print(f"{p['cuenta']:20} {p['red']:9} hace {dias:2} días{fij:9} ->  "
                  f"{'SE COMENTA' if vale(p, momento) else 'fuera'}")
    elif args[:1] == ["filtro"]:
        frases = args[1:] or [l for l in FRASES_PRUEBA.read_text(encoding="utf-8").splitlines()
                              if l.strip() and not l.startswith("#")]
        for t in frases:
            limpio, motivo = filtra(t)
            print(f"FUERA  {t}\n       motivo: {motivo}" if motivo else f"VALE   {limpio}")
    elif args[:1] == ["escribir"]:
        escribir()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
