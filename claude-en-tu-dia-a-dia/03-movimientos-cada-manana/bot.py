"""Bot de Telegram que te lee los movimientos del banco.

Órdenes: /mes  /categorias  /alertas  /resumen  /buscar TEXTO
Solo contesta a TU chat (TELEGRAM_CHAT_ID del .env). A cualquier otro, ni caso.

Uso:  python bot.py          -> se queda escuchando (Ctrl+C para pararlo)
      python bot.py aviso    -> te manda los movimientos del último día y termina
"""
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

import finanzas as fz

CARPETA = Path(__file__).resolve().parent
load_dotenv(CARPETA / ".env")
TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
MI_CHAT = os.getenv("TELEGRAM_CHAT_ID", "").strip()
ALERTA = float(os.getenv("ALERTA_EUROS", "100"))
API = f"https://api.telegram.org/bot{TOKEN}/"


def datos():
    return fz.cargar(fz.ruta_movimientos()), fz.reglas()


def linea(m, r):
    return f"{m['fecha'][5:]} {m['concepto']} {fz.eur(m['importe'])} → {fz.categoria(m['concepto'], r)}"


def orden(texto):
    lista, r = datos()
    cmd, _, arg = texto.strip().partition(" ")
    cmd = cmd.split("@")[0].lower()
    mes = fz.ultimo_mes(lista)

    if cmd == "/mes":
        g, i = fz.totales(lista, r, mes)
        s = [f"📅 Mes {mes}"]
        s += [f"{c}: {fz.eur(v)}" for c, v in fz.gastos_por_categoria(lista, r, mes).items()]
        s += [f"Total gastos: {fz.eur(g)}", f"Ingresos: {fz.eur(i)}", "(traspasos fuera de las sumas)"]
        return "\n".join(s)

    if cmd == "/categorias":
        meses = sorted({fz.mes_de(m) for m in lista})
        suma = {}
        for me in meses:
            for c, v in fz.gastos_por_categoria(lista, r, me).items():
                suma[c] = suma.get(c, 0) + v
        s = [f"📊 Media al mes por categoría ({len(meses)} meses)"]
        s += [f"{c}: {fz.eur(v / len(meses))}" for c, v in sorted(suma.items(), key=lambda x: -x[1])]
        return "\n".join(s)

    if cmd == "/alertas":
        grandes = [m for m in lista if fz.mes_de(m) == mes and m["importe"] <= -ALERTA
                   and fz.categoria(m["concepto"], r) != fz.TRASPASOS]
        if not grandes:
            return f"⚠️ Ningún cargo de más de {fz.eur(ALERTA)} en {mes}"
        return "\n".join([f"⚠️ Cargos de más de {fz.eur(ALERTA)} en {mes}"] + [linea(m, r) for m in grandes])

    if cmd == "/resumen":
        meses = sorted({fz.mes_de(m) for m in lista})[-6:]
        s = ["🗓 Últimos meses (sin traspasos)"]
        for me in meses:
            g, i = fz.totales(lista, r, me)
            s.append(f"{me}: gastos {fz.eur(g)} · ingresos {fz.eur(i)}")
        return "\n".join(s)

    if cmd == "/buscar":
        if not arg:
            return "Dime qué buscar. Ejemplo: /buscar super"
        hits = [m for m in lista if arg.upper() in m["concepto"].upper()]
        return "\n".join([f"🔎 \"{arg}\": {len(hits)} resultado(s)"] + [linea(m, r) for m in hits])

    return "Órdenes: /mes /categorias /alertas /resumen /buscar TEXTO"


def manda(texto):
    requests.post(API + "sendMessage", data={"chat_id": MI_CHAT, "text": texto}, timeout=20).raise_for_status()


def aviso():
    lista, r = datos()
    dia = max(m["fecha"] for m in lista)
    hoy = [m for m in lista if m["fecha"] == dia]
    manda(f"☀️ Movimientos del {dia}\n\n" + "\n".join(linea(m, r) for m in hoy))


def escuchar():
    print("Bot en marcha. Escríbele /mes en Telegram. Ctrl+C para parar.")
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
            m = u.get("message") or {}
            chat = str(m.get("chat", {}).get("id", ""))
            if chat != MI_CHAT:
                print(f"Mensaje de otro chat ({chat}) ignorado. Si eres tú, pon TELEGRAM_CHAT_ID={chat} en el .env")
                continue
            manda(orden(m.get("text") or ""))


if __name__ == "__main__":
    if not TOKEN or TOKEN == "TU_TOKEN_AQUI":
        sys.exit("Falta TELEGRAM_TOKEN en el archivo .env (copia .env.ejemplo a .env y rellénalo).")
    if sys.argv[1:] == ["aviso"]:
        aviso()
    else:
        try:
            escuchar()
        except KeyboardInterrupt:
            print("\nBot parado.")
