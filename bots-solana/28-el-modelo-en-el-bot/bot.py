#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tu bot de Telegram con el modelo dentro: le pone nota a cada token nuevo del ranking de GMGN y lo mide en papel.
Canal de YouTube: Profesor Diógenes · sección "Bots de Solana".

    python3 bot.py

Órdenes:
  (solo, cada 10 minutos)  lee el ranking de GMGN, pone nota a cada token nuevo y te avisa si el modelo lo compraría
  /balance    mide en papel lo apuntado que ya tenga 6 horas: lo que eligió el modelo, contra todo y contra una moneda
  /ultimos    los últimos que eligió el modelo

Antes, en el fichero .env (mira .env.ejemplo):
  TELEGRAM_BOT_TOKEN = la clave que te da BotFather al crear el bot
  TELEGRAM_MI_ID     = tu número de usuario de Telegram, para que el bot SOLO te conteste a ti

Esto no es consejo financiero. Es una herramienta para medir.
"""
import os, sys, time, threading
import requests

AQUI = os.path.dirname(os.path.abspath(__file__))
if os.path.exists(os.path.join(AQUI, ".env")):
    for linea in open(os.path.join(AQUI, ".env"), encoding="utf-8"):
        if "=" in linea and not linea.strip().startswith("#"):
            k, v = linea.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

import modelo

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
MI_ID = os.environ.get("TELEGRAM_MI_ID", "").strip()
API = "https://api.telegram.org/bot%s/" % TOKEN
AYUDA = 'El modelo está vigilando el ranking de GMGN y te aviso de lo que compraría (en papel).\n\n/balance — cómo le va, medido a 6 horas\n/ultimos — los últimos que eligió'


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
    print("Bot en marcha: @%s. Vigilando el ranking de GMGN. (Ctrl+C para parar)" % yo.get("username"))
    if not os.path.exists(modelo.MODELO):
        print(modelo.entrena())
    threading.Thread(target=modelo.vigila, args=(lambda t: telegram("sendMessage", chat_id=MI_ID, text=t),), daemon=True).start()
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
                if orden == "balance":
                    telegram("sendMessage", chat_id=chat, text="Midiendo… las velas van despacio (unas 10 por minuto).")
                    threading.Thread(target=lambda c=chat: mandar(c, modelo.balance()), daemon=True).start()
                elif orden == "ultimos":
                    el = [a for a in modelo.apuntados() if a.get("elegido")][-10:]
                    mandar(chat, "\n".join("%s · nota %.2f · %s" % (a["simbolo"], a["nota"], a["ca"]) for a in el) or "Todavía no ha elegido ninguno.")
                else:
                    raise ValueError("orden desconocida")
            except Exception as e:
                telegram("sendMessage", chat_id=chat, text="No lo he entendido (%s).\n\n%s" % (e, AYUDA))
        if not r:
            time.sleep(3)


if __name__ == "__main__":
    main()
