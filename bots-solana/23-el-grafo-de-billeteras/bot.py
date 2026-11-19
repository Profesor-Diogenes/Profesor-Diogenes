#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tu bot de Telegram: le pegas la dirección de un contrato de Solana y te contesta con el mapa dibujado y el detalle.
Canal de YouTube: Profesor Diógenes · sección "Bots de Solana".

    python3 bot.py

Antes, en el fichero .env (mira .env.ejemplo):
  TELEGRAM_BOT_TOKEN = la clave que te da BotFather al crear el bot
  TELEGRAM_MI_ID     = tu número de usuario de Telegram, para que el bot SOLO te conteste a ti
                       (si no lo sabes, deja esto vacío, arranca el bot, escríbele y te lo dice)

Cómo se crea el bot en BotFather: lo tienes en el Curso de Claude del canal (enlace en el README).
Esto no es consejo financiero. Es una herramienta para mirar.
"""
import os, re, io, sys, time, contextlib, threading
import requests

import grafo as analisis         # el programa de este capítulo (el mismo que se arranca a mano)

analisis.cargar_env() if hasattr(analisis, "cargar_env") else None
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
MI_ID = os.environ.get("TELEGRAM_MI_ID", "").strip()
API = "https://api.telegram.org/bot%s/" % TOKEN
UNO_A_LA_VEZ = threading.Lock()                               # de uno en uno: las fuentes gratis cortan si corres
CONTRATO = re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b")   # así es una dirección de Solana


def telegram(metodo, **datos):
    try:
        return requests.post(API + metodo, json=datos, timeout=60).json()
    except Exception:
        return {}


def mandar(chat, texto):
    """Telegram corta los mensajes a 4.096 letras: si es más largo, lo manda en trozos."""
    trozo = ""
    for linea in texto.splitlines():
        if len(trozo) + len(linea) > 3500:
            telegram("sendMessage", chat_id=chat, text="<pre>%s</pre>" % escapar(trozo), parse_mode="HTML")
            trozo = ""
        trozo += linea + "\n"
    if trozo.strip():
        telegram("sendMessage", chat_id=chat, text="<pre>%s</pre>" % escapar(trozo), parse_mode="HTML")


def escapar(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def analizar(chat, ca):
    telegram("sendMessage", chat_id=chat, text="🔎 Mirando %s… dame un momento." % ca)
    salida = io.StringIO()
    with UNO_A_LA_VEZ, contextlib.redirect_stdout(salida):
        imagen = None
        try:
            imagen = analisis.main(ca)
        except Exception as e:
            print("Algo ha fallado: %s" % e)
    if imagen and os.path.exists(imagen):                          # primero el dibujo, luego el detalle en texto
        try:
            requests.post(API + "sendPhoto", data={"chat_id": chat}, files={"photo": open(imagen, "rb")}, timeout=120)
        except Exception:
            pass
    mandar(chat, salida.getvalue())


def main():
    if not TOKEN:
        print("Falta TELEGRAM_BOT_TOKEN en el fichero .env"); sys.exit(1)
    yo = telegram("getMe").get("result") or {}
    print("Bot en marcha: @%s. Escríbele un contrato. (Ctrl+C para parar)" % yo.get("username"))
    desde = 0
    while True:
        r = telegram("getUpdates", offset=desde, timeout=50, allowed_updates=["message"])
        for u in r.get("result") or []:
            desde = u["update_id"] + 1
            m = u.get("message") or {}
            chat = (m.get("chat") or {}).get("id")
            quien = str((m.get("from") or {}).get("id"))
            texto = m.get("text") or ""
            if not chat:
                continue
            if not MI_ID:
                telegram("sendMessage", chat_id=chat, text="Tu número de usuario es %s. Ponlo en TELEGRAM_MI_ID del .env y vuelve a arrancar el bot." % quien)
                continue
            if quien != MI_ID:
                continue                      # no es el dueño: ni contesta
            encontrados = CONTRATO.findall(texto)
            if not encontrados:
                telegram("sendMessage", chat_id=chat, text="Pégame la dirección de un contrato de Solana.")
                continue
            threading.Thread(target=analizar, args=(chat, encontrados[0]), daemon=True).start()
        if not r:
            time.sleep(3)


if __name__ == "__main__":
    main()
