"""El botón: las opciones te llegan a Telegram con tres botones (A, B o fuera).

Uso:  python bot.py enviar   -> te manda las opciones pendientes (o te avisa si hoy no ha llegado nada) y termina
      python bot.py          -> se queda escuchando los botones (Ctrl+C para pararlo)
Solo hace caso a TU chat (TELEGRAM_CHAT_ID del .env).
"""
import json
import os
import sys
import time

import requests

import comentarios as cm

TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
MI_CHAT = os.getenv("TELEGRAM_CHAT_ID", "").strip()
API = f"https://api.telegram.org/bot{TOKEN}/"


def llama(metodo, **datos):
    r = requests.post(API + metodo, data=datos, timeout=20).json()
    if not r.get("ok"):
        sys.exit(f"Telegram dice que no: {r.get('description')}. ¿Están bien TELEGRAM_TOKEN y TELEGRAM_CHAT_ID en el .env?")
    return r["result"]


def texto_de(e):
    lineas = [f"📝 Post de {e['cuenta']} ({e['red']}):", f"\"{e['post'][:300]}\"", ""]
    lineas += [f"{letra}) {t}" for letra, t in sorted(e["opciones"].items())]
    return "\n".join(lineas)


def botones(pid, e):
    fila = [{"text": f"✅ {letra}", "callback_data": f"{pid}|{letra}"} for letra in sorted(e["opciones"])]
    fila.append({"text": "❌ Fuera", "callback_data": f"{pid}|X"})
    return json.dumps({"inline_keyboard": [fila]})


def enviar():
    estado = cm.leer_estado()
    pendientes = [(pid, e) for pid, e in estado.items() if e["estado"] == "pendiente"]
    if not any(e["dia"] == cm.hoy() for e in estado.values()):
        llama("sendMessage", chat_id=MI_CHAT,
              text="⚠️ Esta mañana no ha llegado ninguna opción. Mira si se recogieron los posts y si Claude contestó.")
    for pid, e in pendientes:
        llama("sendMessage", chat_id=MI_CHAT, text=texto_de(e), reply_markup=botones(pid, e))
        e["estado"] = "enviado"
        cm.guardar_estado(estado)
    print(f"Enviadas {len(pendientes)} tanda(s) de opciones a Telegram.")


def boton(q):
    """Alguien ha pulsado un botón. Si no eres tú, ni caso."""
    if str(q["from"]["id"]) != MI_CHAT:
        print(f"Botón pulsado por otro ({q['from']['id']}), ignorado.")
        return
    llama("answerCallbackQuery", callback_query_id=q["id"])
    pid, letra = q["data"].split("|", 1)
    estado = cm.leer_estado()
    e = estado.get(pid)
    if not e or e["estado"] not in ("pendiente", "enviado"):
        return  # ya decidido antes: no se aprueba dos veces
    if letra == "X":
        e["estado"], fin = "descartado", "❌ Descartado. No se publica nada."
    else:
        e["estado"], e["aprobada"] = "aprobado", e["opciones"][letra]
        fin = f"✅ Aprobada la {letra}. Se publica en la próxima pasada."
    cm.guardar_estado(estado)
    m = q["message"]
    llama("editMessageText", chat_id=m["chat"]["id"], message_id=m["message_id"], text=texto_de(e) + "\n\n" + fin)
    print(f"{pid}: {e['estado']}")


def escuchar():
    print("Bot en marcha, esperando tus botones. Ctrl+C para parar.")
    offset = None
    while True:
        try:
            res = requests.get(API + "getUpdates", params={"timeout": 25, "offset": offset}, timeout=40).json()
        except requests.RequestException:
            time.sleep(3)
            continue
        if not res.get("ok"):
            sys.exit(f"Telegram dice que no: {res.get('description')}. ¿Está bien TELEGRAM_TOKEN en el .env?")
        for u in res.get("result", []):
            offset = u["update_id"] + 1
            if "callback_query" in u:
                boton(u["callback_query"])
            elif u.get("message"):
                chat = str(u["message"]["chat"]["id"])
                if chat != MI_CHAT:
                    print(f"Mensaje de otro chat ({chat}) ignorado. Si eres tú, pon TELEGRAM_CHAT_ID={chat} en el .env")


if __name__ == "__main__":
    if not TOKEN or TOKEN == "TU_TOKEN_AQUI":
        sys.exit("Falta TELEGRAM_TOKEN en el archivo .env (copia .env.ejemplo a .env y rellénalo).")
    if sys.argv[1:] == ["enviar"]:
        enviar()
    else:
        try:
            escuchar()
        except KeyboardInterrupt:
            print("\nBot parado.")
