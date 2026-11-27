"""Publica tus vídeos en tus redes con la API de un servicio de publicación.

Está hecho para Upload-Post (el servicio que sale en el vídeo .2). Si usas otro,
pásale a Claude este archivo y la documentación de tu servicio para que lo adapte.

Órdenes:
  python publicar.py revisar           mira textos, topes y repetidos SIN mandar nada
  python publicar.py programar         programa lo del calendario que aún no tiene número
  python publicar.py estado [NÚMERO]   pregunta cómo va una subida (o todas)
  python publicar.py lista             lo programado en el servicio contra tu calendario
  python publicar.py cancelar NÚMERO   cancela una programación (luego, programar otra vez)
"""
import csv
import json
import os
import re
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import requests
from dotenv import load_dotenv

CARPETA = Path(__file__).resolve().parent
load_dotenv(CARPETA / ".env")
API = os.getenv("SERVICIO_URL", "https://api.upload-post.com").rstrip("/")  # no lo cambies (sirve para probar)
CLAVE = os.getenv("UPLOAD_POST_CLAVE", "").strip()
PERFIL = os.getenv("UPLOAD_POST_PERFIL", "").strip()
NUMEROS = CARPETA / "numeros.json"
TIMEOUT = (15, 600)  # 15 s para conectar, hasta 10 min para subir un vídeo grande

# Máximo de publicaciones en 24 horas por cuenta, según la documentación del servicio
# (docs.upload-post.com/guides/limit-of-uploads, noviembre de 2026; puede cambiar).
# Se mira cuando sale, no cuando lo programas.
TOPES = {"tiktok": 15, "youtube": 30, "instagram": 50, "x": 10,
         "facebook": 25, "threads": 50, "linkedin": 150, "pinterest": 20}
ENLACE = re.compile(r"(https?://|www\.)\S+|\b[\w-]+\.(com|es|net|org|io)(/\S*)?\b", re.I)


# ---------- archivos tuyos ----------

def calendario():
    """calendario.csv: video,fecha,hora,zona,redes  (redes separadas por espacios)"""
    with open(CARPETA / "calendario.csv", encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    for f in filas:
        f["redes"] = f["redes"].lower().split()
        f["clave"] = f"{f['video']}|{f['fecha']}|{f['hora']}"
    return filas


def textos():
    """textos.json: {"video.mp4": {"youtube": "...", "x": "..."}}"""
    with open(CARPETA / "textos.json", encoding="utf-8") as f:
        return json.load(f)


def numeros():
    if NUMEROS.exists():
        return json.loads(NUMEROS.read_text(encoding="utf-8"))
    return {}


def guardar_numeros(n):
    NUMEROS.write_text(json.dumps(n, indent=1, ensure_ascii=False), encoding="utf-8")


def momento(f):
    """Fecha y hora de la fila CON su zona horaria. Sin zona, no se programa."""
    if not f.get("zona"):
        raise ValueError("falta la zona horaria (por ejemplo Europe/Madrid)")
    try:
        zona = ZoneInfo(f["zona"])
    except ZoneInfoNotFoundError:
        raise ValueError(f"zona horaria desconocida: {f['zona']}")
    return datetime.fromisoformat(f"{f['fecha']}T{f['hora']}").replace(tzinfo=zona)


# ---------- revisar (no manda nada) ----------

def problemas_texto(red, t):
    if not t:
        return "no hay texto para esta red"
    if red == "x" and ENLACE.search(t):
        return "X borra los enlaces: quítalo"
    if red in ("instagram", "tiktok") and ENLACE.search(t):
        return "aquí el enlace no se puede pulsar: pon 'enlace en el perfil'"
    return ""


def revisar():
    filas, tx, fallos = calendario(), textos(), 0
    print("TEXTOS (uno por red)")
    for f in filas:
        for red in f["redes"]:
            p = problemas_texto(red, tx.get(f["video"], {}).get(red, ""))
            fallos += bool(p)
            print(f"   {f['video']:<22} {red:<10} {p or 'ok'}")

    print("\nFECHA, HORA Y ZONA")
    for f in filas:
        try:
            cuando = momento(f)
            nota = "ok" if cuando > datetime.now(cuando.tzinfo) else "YA HA PASADO"
        except ValueError as e:
            nota = f"MAL: {e}"
        fallos += nota != "ok"
        print(f"   {f['video']:<22} {f['fecha']} {f['hora']} {f.get('zona') or '¿?':<14} {nota}")

    print("\nCUÁNTAS SALEN CADA DÍA EN CADA RED")
    cuenta = {}
    for f in filas:
        for red in f["redes"]:
            cuenta[(f["fecha"], red)] = cuenta.get((f["fecha"], red), 0) + 1
    for (dia, red), c in sorted(cuenta.items()):
        tope = TOPES.get(red)
        pasa = tope is not None and c > tope
        fallos += pasa
        print(f"   {dia} {red:<10} {c} de {tope or '?'}" + ("   <- se pasa del tope: muévelo a otro día" if pasa else ""))

    print("\nREPETIDOS (mismo vídeo, misma red, menos de 48 horas)")
    vistos, rep = {}, 0
    for f in sorted(filas, key=lambda f: (f["fecha"], f["hora"])):
        try:
            cuando = momento(f)
        except ValueError:
            continue
        for red in f["redes"]:
            antes = vistos.get((f["video"], red))
            if antes and cuando - antes < timedelta(hours=48):
                rep += 1
                print(f"   {f['video']} en {red}: {f['fecha']} {f['hora']} -> lo rechazará. Cambia el texto y deja pasar 48 h")
            vistos[(f["video"], red)] = cuando
    if not rep:
        print("   ninguno")
    fallos += rep
    print(f"\n{'Todo bien: puedes programar.' if not fallos else f'{fallos} cosa(s) que arreglar antes de programar.'}")
    return fallos


# ---------- hablar con el servicio ----------

def cabecera(extra=None):
    if not CLAVE or "TU_CLAVE" in CLAVE:
        sys.exit("Falta UPLOAD_POST_CLAVE en el .env (copia .env.ejemplo a .env y pon tu clave).")
    h = {"Authorization": f"Apikey {CLAVE}"}
    h.update(extra or {})
    return h


def respuesta(r):
    try:
        datos = r.json()
    except ValueError:
        datos = {"message": r.text[:300]}
    if r.status_code == 401:
        sys.exit("El servicio dice que la clave no vale (401). Revisa UPLOAD_POST_CLAVE en el .env.")
    return datos


def programar():
    if revisar():
        sys.exit("No programo nada hasta que la revisión salga limpia.")
    if not PERFIL or "TU_PERFIL" in PERFIL:
        sys.exit("Falta UPLOAD_POST_PERFIL en el .env (el nombre del perfil donde conectaste tus redes).")
    n, tx = numeros(), textos()
    print("\nPROGRAMANDO")
    for f in calendario():
        if f["clave"] in n:
            v = n[f["clave"]]
            if v.get("numero"):
                print(f"   {f['clave']}: ya tiene número ({v['numero']}). No se vuelve a mandar.")
            else:
                print(f"   {f['clave']}: se mandó y no hubo respuesta. NO se repite:"
                      f" python publicar.py estado {v['peticion']}")
            continue
        video = CARPETA / "videos" / f["video"]
        if not video.exists():
            print(f"   {f['clave']}: no encuentro videos/{f['video']}. Saltado.")
            continue
        # Nuestro propio número de petición, guardado ANTES de mandar: si la respuesta
        # se pierde, con él se pregunta el estado. Y nunca se vuelve a enviar.
        peticion = str(uuid.uuid4())
        n[f["clave"]] = {"numero": None, "peticion": peticion, "redes": f["redes"], "estado": "enviando"}
        guardar_numeros(n)
        datos = [("user", PERFIL), ("scheduled_date", f"{f['fecha']}T{f['hora']}:00"),
                 ("timezone", f["zona"]), ("request_id", peticion)]
        datos += [("platform[]", red) for red in f["redes"]]
        t = tx[f["video"]]
        datos.append(("title", t.get("youtube") or next(iter(t.values()))))
        datos += [(f"{red}_title", t[red]) for red in f["redes"]]
        try:
            with open(video, "rb") as fv:
                r = requests.post(f"{API}/api/upload", headers=cabecera({"Idempotency-Key": peticion}),
                                  data=datos, files={"video": (video.name, fv)}, timeout=TIMEOUT)
        except requests.exceptions.RequestException as e:
            n[f["clave"]]["estado"] = "sin respuesta"
            guardar_numeros(n)
            print(f"   {f['clave']}: SIN RESPUESTA ({type(e).__name__}). Puede que haya llegado.")
            print(f"      NO lo repitas: pregunta con  python publicar.py estado {peticion}")
            continue
        d = respuesta(r)
        if r.status_code in (200, 201, 202) and d.get("success", True):
            numero = d.get("job_id") or d.get("request_id") or peticion
            n[f["clave"]].update(numero=numero, estado="programado" if d.get("job_id") else "subiendo")
            guardar_numeros(n)
            print(f"   {f['fecha']} {f['hora']} {f['zona']}  {' '.join(f['redes']):<28} n.º {numero}")
        else:
            del n[f["clave"]]
            guardar_numeros(n)
            motivo = d.get("message") or d.get("error") or r.status_code
            for v in d.get("violations", []):
                motivo = f"{motivo} | {v.get('message')}"
            print(f"   {f['clave']}: RECHAZADO ({r.status_code}): {motivo}")


def estado(numero=None):
    n = numeros()
    lista = [(k, v) for k, v in n.items() if numero in (None, v.get("numero"), v.get("peticion"))]
    if numero and not lista:
        lista = [(numero, {"numero": numero, "peticion": None})]
    for clave, v in lista:
        num = v.get("numero")
        # Si sabemos el job_id, por job_id; si no (subida en segundo plano o sin respuesta), por request_id.
        param = {"job_id": num} if num and num != v.get("peticion") else {"request_id": v.get("peticion") or num}
        r = requests.get(f"{API}/api/uploadposts/status", headers=cabecera(), params=param, timeout=30)
        d = respuesta(r)
        print(f"{clave}: {d.get('status', r.status_code)}")
        for res in d.get("results", []):
            print(f"   {res.get('platform')}: {res.get('message') or res.get('error') or ''}")
        if d.get("job_id") and clave in n and not n[clave].get("numero"):
            n[clave].update(numero=d["job_id"], estado="programado")
            guardar_numeros(n)


def lista():
    """Lo programado en el servicio, red por red, contra tu calendario."""
    r = requests.get(f"{API}/api/uploadposts/schedule", headers=cabecera(),
                     params={"profile_username": PERFIL} if PERFIL else None, timeout=30)
    d = respuesta(r)
    en_servicio = {p["job_id"]: p for p in d.get("scheduled_posts", [])}
    n, mal = numeros(), 0
    print("TU CALENDARIO CONTRA LO PROGRAMADO")
    for f in calendario():
        num = (n.get(f["clave"]) or {}).get("numero")
        p = en_servicio.pop(num, None) if num else None
        for red in f["redes"]:
            if p and red in p.get("platforms", []):
                nota = f"ok  (n.º {num})"
            else:
                nota = "FALTA: no está programado"
                mal += 1
            print(f"   {f['fecha']} {f['hora']} {red:<10} {f['video']:<22} {nota}")
    for num, p in en_servicio.items():
        mal += 1
        print(f"   SOBRA en el servicio: n.º {num} {p.get('scheduled_date')} {' '.join(p.get('platforms', []))}"
              " -> no está en tu calendario")
    print("Cuadra con tu calendario." if not mal else f"{mal} diferencia(s).")


def cancelar(numero):
    r = requests.delete(f"{API}/api/uploadposts/schedule/{numero}", headers=cabecera(), timeout=30)
    d = respuesta(r)
    if r.status_code != 200:
        sys.exit(f"No se ha podido cancelar ({r.status_code}): {d.get('error') or d.get('message')}")
    n = numeros()
    for k in [k for k, v in n.items() if v.get("numero") == numero]:
        del n[k]
    guardar_numeros(n)
    print(f"Cancelado n.º {numero}. Cambia el calendario y vuelve a programar.")


if __name__ == "__main__":
    orden = sys.argv[1] if len(sys.argv) > 1 else ""
    if orden == "revisar":
        revisar()
    elif orden == "programar":
        programar()
    elif orden == "estado":
        estado(sys.argv[2] if len(sys.argv) > 2 else None)
    elif orden == "lista":
        lista()
    elif orden == "cancelar" and len(sys.argv) > 2:
        cancelar(sys.argv[2])
    else:
        print(__doc__)
