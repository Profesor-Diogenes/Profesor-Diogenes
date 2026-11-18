#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EL EXAMEN: ¿acierta una IA qué token va a doblar?
Canal de YouTube: Profesor Diógenes · sección "Bots de Solana", vídeo 18.

    python3 examen.py            (usa el modelo que tengas puesto en el .env)
    python3 examen.py 200        (solo las 200 primeras fichas)

Qué hace: coge fichas de tokens REALES de pump.fun, tal como estaban en el momento en que los vimos
(capitalización, liquidez, holders, bundlers, el creador…), SIN nada de lo que pasó después. Le enseña
cada ficha a la IA y le pregunta: ¿doblará en las próximas 6 horas? Luego compara con lo que pasó de verdad.

Vale cualquier modelo que hable el idioma de OpenAI, que son casi todos: uno local con Ollama, o de pago
(OpenAI, Gemini, Grok, Claude…). Se elige en el .env con tres líneas: IA_URL, IA_MODELO, IA_CLAVE.
"""
import os, sys, json, time, random
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
IA_URL = os.environ.get("IA_URL", "http://localhost:11434/v1").rstrip("/")     # Ollama en tu ordenador
IA_MODELO = os.environ.get("IA_MODELO", "qwen2.5:14b")
IA_CLAVE = os.environ.get("IA_CLAVE", "local")

PREGUNTA = ("Eres un trader experto en memecoins de Solana. Esta es la ficha de un token de pump.fun en el momento "
            "exacto en que lo veo. Los porcentajes van de 0 a 1. De media, uno de cada cuatro tokens como estos llega "
            "a doblar de precio en las 6 horas siguientes.\n\n%s\n\n¿Este token llegará a doblar de precio en las "
            "próximas 6 horas? Responde con UNA sola palabra: SI o NO.")


def preguntar(ficha):
    cuerpo = {"model": IA_MODELO, "messages": [{"role": "user", "content": PREGUNTA % json.dumps(ficha, ensure_ascii=False, indent=0)}]}
    for intento in range(4):
        try:
            r = requests.post(IA_URL + "/chat/completions", json=cuerpo, timeout=180,
                              headers={"Authorization": "Bearer " + IA_CLAVE})
            if r.status_code == 429:
                time.sleep(20); continue
            t = (r.json()["choices"][0]["message"].get("content") or "").strip().upper()
            t = t.replace("SÍ", "SI")
            ultima = [p.strip(".,:;*!¡\"'") for p in t.split()][-1:] or [""]
            if "SI" in (t.split()[0:1] + ultima) or t.startswith("SI"):
                return 1
            if "NO" in (t.split()[0:1] + ultima) or t.startswith("NO"):
                return 0
            return None
        except Exception as e:
            time.sleep(5)
    return None


def main():
    fichas = json.load(open(os.path.join(AQUI, "examen.json")))
    cuantas = int(sys.argv[1]) if len(sys.argv) > 1 else len(fichas)
    fichas = fichas[:cuantas]
    dice_si = acierta_si = sin_respuesta = 0
    doblan = sum(f["dobla"] for f in fichas)
    salida = os.path.join(AQUI, "respuestas_%s.jsonl" % IA_MODELO.replace("/", "_").replace(":", "_"))
    hechas = sum(1 for _ in open(salida)) if os.path.exists(salida) else 0
    for i, f in enumerate(fichas):
        if i < hechas:
            continue
        r = preguntar(f["ficha"])
        with open(salida, "a") as fh:
            fh.write(json.dumps({"i": i, "ia": r, "dobla": f["dobla"]}) + "\n")
        if i % 25 == 0:
            print(time.strftime("%H:%M:%S"), i, "de", len(fichas), flush=True)
    filas = [json.loads(l) for l in open(salida)][:cuantas]
    for x in filas:
        if x["ia"] is None: sin_respuesta += 1
        elif x["ia"] == 1:
            dice_si += 1; acierta_si += x["dobla"]
    dice_no = len(filas) - dice_si - sin_respuesta
    doblan_no = sum(x["dobla"] for x in filas if x["ia"] == 0)
    print("\nEXAMEN · modelo %s · %d fichas" % (IA_MODELO, len(filas)))
    print("De todas, doblaron de verdad: %d (%.1f %%)  <- esto es lo que aciertas comprando a ciegas" % (doblan, 100.0 * doblan / len(filas)))
    print("La IA dijo SI en %d. De esas doblaron %d (%.1f %%)" % (dice_si, acierta_si, 100.0 * acierta_si / max(dice_si, 1)))
    print("La IA dijo NO en %d. De esas doblaron %d (%.1f %%)" % (dice_no, doblan_no, 100.0 * doblan_no / max(dice_no, 1)))
    if sin_respuesta:
        print("No contestó SI ni NO en %d." % sin_respuesta)
    print("Para no perder dinero con objetivo de doblar y corte a la mitad hay que acertar casi el 35 %.")


if __name__ == "__main__":
    main()
