#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tu bot de Telegram que te enseña las cuatro maneras de examinar un modelo, y cuál es la única honrada.
Canal de YouTube: Profesor Diógenes · sección "Bots de Solana".

    python3 bot.py

Órdenes:
  /engano            las cuatro maneras, una detrás de otra
  /engano memoria    (o azar, trampa, fecha) solo una

Antes, en el fichero .env (mira .env.ejemplo):
  TELEGRAM_BOT_TOKEN = la clave que te da BotFather al crear el bot
  TELEGRAM_MI_ID     = tu número de usuario de Telegram, para que el bot SOLO te conteste a ti

Esto no es consejo financiero. Es una herramienta para medir.
"""
import os, sys, time
import requests

AQUI = os.path.dirname(os.path.abspath(__file__))
if os.path.exists(os.path.join(AQUI, ".env")):
    for linea in open(os.path.join(AQUI, ".env"), encoding="utf-8"):
        if "=" in linea and not linea.strip().startswith("#"):
            k, v = linea.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

import engano

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
MI_ID = os.environ.get("TELEGRAM_MI_ID", "").strip()
API = "https://api.telegram.org/bot%s/" % TOKEN
AYUDA = 'Te enseño cómo se engaña un modelo, y cómo te engaña a ti.\n\n/engano — las cuatro maneras\n/engano memoria · /engano azar · /engano trampa · /engano fecha'


def telegram(metodo, **datos):
    try:
        return requests.post(API + metodo, json=datos, timeout=60).json()
    except Exception:
        return {}


def mandar(chat, texto):
    texto = texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    for i in range(0, len(texto), 3500):
        telegram("sendMessage", chat_id=chat, text="<pre>%s</pre>" % texto[i:i + 3500], parse_mode="HTML")


def main():
    if not TOKEN:
        print("Falta TELEGRAM_BOT_TOKEN en el fichero .env"); sys.exit(1)
    yo = telegram("getMe").get("result") or {}
    print("Bot en marcha: @%s. Escríbele /engano. (Ctrl+C para parar)" % yo.get("username"))
    desde = 0
    while True:
        r = telegram("getUpdates", offset=desde, timeout=50, allowed_updates=["message"])
        for u in r.get("result") or []:
            desde = u["update_id"] + 1
            m = u.get("message") or {}
            chat = (m.get("chat") or {}).get("id")
            quien = str((m.get("from") or {}).get("id"))
            partes = (m.get("text") or "").split()
            if not chat:
                continue
            if not MI_ID:
                telegram("sendMessage", chat_id=chat, text="Tu número de usuario es %s. Ponlo en TELEGRAM_MI_ID del .env y vuelve a arrancar el bot." % quien)
                continue
            if quien != MI_ID:
                continue                      # no es el dueño: ni contesta
            if not partes or not partes[0].startswith("/") or partes[0] in ("/start", "/ayuda"):
                telegram("sendMessage", chat_id=chat, text=AYUDA)
                continue
            orden = partes[0][1:].split("@")[0]
            try:
                if orden != "engano":
                    raise ValueError("orden desconocida")
                telegram("sendMessage", chat_id=chat, text="Entrenando y examinando… tarda un poco.")
                mandar(chat, engano.main(partes[1:]))
            except Exception as e:
                telegram("sendMessage", chat_id=chat, text="No lo he entendido (%s).\n\n%s" % (e, AYUDA))
        if not r:
            time.sleep(3)


if __name__ == "__main__":
    main()
