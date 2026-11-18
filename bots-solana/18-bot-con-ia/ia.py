#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tu bot de Telegram con una IA dentro: le pegas un contrato, recoge la ficha y le pide opinión al modelo
que tú elijas. Y una orden para examinar a ese modelo con tokens reales, que es lo importante.
Canal de YouTube: Profesor Diógenes · sección "Bots de Solana", vídeo 18.

    python3 ia.py

Cómo se usa, desde tu bot:
  (pegas un contrato)   -> recoge la ficha de GMGN y te manda lo que opina la IA
  /modelo               -> con qué IA está hablando
  /examen 100           -> le pasa 100 fichas de tokens reales de los que ya se sabe qué hicieron,
                           y te dice cuántas acertó (tarda: una pregunta por ficha)

Qué IA usa: la que pongas en el .env. Vale cualquiera que hable el idioma de OpenAI, que son casi todas.
  - Una en tu ordenador, gratis, con Ollama:   IA_URL=http://localhost:11434/v1   IA_MODELO=qwen2.5:14b
  - OpenAI:   IA_URL=https://api.openai.com/v1                                 IA_MODELO=el que quieras   IA_CLAVE=tu clave
  - Gemini:   IA_URL=https://generativelanguage.googleapis.com/v1beta/openai   IA_MODELO=…                IA_CLAVE=tu clave
  - Grok:     IA_URL=https://api.x.ai/v1                                       IA_MODELO=…                IA_CLAVE=tu clave
  - Claude:   IA_URL=https://api.anthropic.com/v1                              IA_MODELO=…                IA_CLAVE=tu clave

Lo que tienes que saber antes de fiarte: una IA contesta SIEMPRE, y siempre con seguridad. Que conteste no
quiere decir que acierte. Para eso está /examen. La IA aquí opina: no decide ni compra nada.

Esto NO es consejo financiero. Es una herramienta para mirar.
"""
import os, re, json, time, uuid, threading
import requests
import examen                      # el examen y la conexión con la IA están en examen.py

AQUI = os.path.dirname(os.path.abspath(__file__))
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
MI_ID = os.environ.get("TELEGRAM_MI_ID", "").strip()
CLAVE_GMGN = os.environ.get("GMGN_API_KEY") or "gmgn_solbscbaseethmonadtron"   # la pública de pruebas de GMGN
BOT = "https://api.telegram.org/bot%s/" % TOKEN
CONTRATO = re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b")

OPINION = ("Eres un trader experto en memecoins de Solana. Esta es la ficha de un token en este momento. "
           "Los porcentajes van de 0 a 1.\n\n%s\n\nContesta en español, en tres líneas como mucho:\n"
           "1) ¿Crees que llegará a doblar de precio en las próximas 6 horas? Empieza con SI o NO.\n"
           "2) El dato de la ficha que más pesa en tu respuesta.\n3) El mayor riesgo que ves.")


def telegram(metodo, **datos):
    try:
        return requests.post(BOT + metodo, json=datos, timeout=60).json()
    except Exception:
        return {}


def avisar(texto):
    telegram("sendMessage", chat_id=MI_ID, text=texto[:4000], disable_web_page_preview=True)


def gmgn(ruta, ca):
    q = {"chain": "sol", "address": ca, "timestamp": int(time.time()), "client_id": str(uuid.uuid4())}
    try:
        d = requests.get("https://openapi.gmgn.ai" + ruta, params=q, timeout=25,
                         headers={"X-APIKEY": CLAVE_GMGN, "User-Agent": "profesor-diogenes"}).json()
        return d.get("data") or {}
    except Exception:
        return {}


def num(x):
    try:
        return float(x)
    except Exception:
        return 0.0


def ficha_de(ca):
    """Lo mismo que vería una persona en GMGN, en limpio, para dárselo a la IA."""
    info = gmgn("/v1/token/info", ca)
    time.sleep(0.4)
    seg = gmgn("/v1/token/security", ca)
    if not info.get("symbol"):
        return None, None
    p = info.get("price") or {}
    nacio = num(info.get("open_timestamp") or info.get("creation_timestamp"))
    ficha = {
        "market_cap": round(num(p.get("price")) * num(info.get("total_supply"))),
        "liquidity": round(num(info.get("liquidity"))),
        "volume_24h": round(num(p.get("volume_24h"))),
        "buys_24h": p.get("buys_24h"), "sells_24h": p.get("sells_24h"),
        "holder_count": info.get("holder_count"),
        "edad_minutos": round((time.time() - nacio) / 60) if nacio else None,
        "top_10_holder_rate": seg.get("top_10_holder_rate"),
        "bundler_trader_amount_rate": seg.get("bundler_trader_amount_rate"),
        "rat_trader_amount_rate": seg.get("rat_trader_amount_rate"),
        "renounced_mint": seg.get("renounced_mint"), "renounced_freeze_account": seg.get("renounced_freeze_account"),
        "burn_status": seg.get("burn_status"),
        "launchpad": info.get("launchpad"), "progress": info.get("launchpad_progress"),
    }
    return info.get("symbol"), {k: v for k, v in ficha.items() if v is not None}


def opinion(ficha):
    cuerpo = {"model": examen.IA_MODELO, "messages": [{"role": "user", "content": OPINION % json.dumps(ficha, ensure_ascii=False, indent=0)}]}
    try:
        r = requests.post(examen.IA_URL + "/chat/completions", json=cuerpo, timeout=180,
                          headers={"Authorization": "Bearer " + examen.IA_CLAVE})
        return (r.json()["choices"][0]["message"].get("content") or "").strip()
    except Exception as e:
        return "La IA no contesta (%s). Mira IA_URL, IA_MODELO e IA_CLAVE en el .env." % str(e)[:80]


def hacer_examen(cuantas):
    fichas = json.load(open(os.path.join(AQUI, "examen.json")))[:cuantas]
    si = acierta = no = doblan_no = mudas = 0
    for i, f in enumerate(fichas):
        r = examen.preguntar(f["ficha"])
        if r is None: mudas += 1
        elif r == 1: si += 1; acierta += f["dobla"]
        else: no += 1; doblan_no += f["dobla"]
        if i and i % 50 == 0:
            avisar("… voy por la %d de %d" % (i, len(fichas)))
    base = sum(f["dobla"] for f in fichas)
    avisar("🎓 EXAMEN a %s · %d tokens reales\n\n"
           "Doblaron de verdad: %d (%.0f %%). Eso es lo que aciertas comprando a ciegas.\n\n"
           "La IA dijo SI en %d. De esos doblaron %d (%.0f %%).\n"
           "La IA dijo NO en %d. De esos doblaron %d (%.0f %%).\n%s\n"
           "Para no perder dinero con objetivo de doblar y corte a la mitad hay que acertar casi el 35 %%." % (
               examen.IA_MODELO, len(fichas), base, 100.0 * base / len(fichas),
               si, acierta, 100.0 * acierta / max(si, 1), no, doblan_no, 100.0 * doblan_no / max(no, 1),
               ("No supo decir SI ni NO en %d.\n" % mudas) if mudas else ""))


def escuchar_bot():
    desde = 0
    while True:
        r = telegram("getUpdates", offset=desde, timeout=50, allowed_updates=["message"])
        for u in r.get("result") or []:
            desde = u["update_id"] + 1
            m = u.get("message") or {}
            chat = (m.get("chat") or {}).get("id")
            quien = str((m.get("from") or {}).get("id"))
            texto = (m.get("text") or "").strip()
            if not chat:
                continue
            if not MI_ID:
                telegram("sendMessage", chat_id=chat, text="Tu número de usuario es %s. Ponlo en TELEGRAM_MI_ID del .env y vuelve a arrancar." % quien)
                continue
            if quien != MI_ID:
                continue
            ca = CONTRATO.search(texto)
            if texto.lower().startswith("/modelo"):
                avisar("🤖 Estoy hablando con: %s\n(en %s)" % (examen.IA_MODELO, examen.IA_URL))
            elif texto.lower().startswith("/examen"):
                n = int(re.sub(r"\D", "", texto) or 100)
                avisar("Empiezo el examen con %d tokens reales. Una pregunta por token: ten paciencia." % n)
                threading.Thread(target=hacer_examen, args=(n,), daemon=True).start()
            elif ca:
                simbolo, ficha = ficha_de(ca.group(0))
                if not ficha:
                    avisar("GMGN no conoce ese contrato."); continue
                avisar("📋 %s · capitalización %s $ · liquidez %s $ · holders %s\nPreguntando a %s…" % (
                    simbolo, "{:,}".format(ficha.get("market_cap", 0)).replace(",", "."),
                    "{:,}".format(ficha.get("liquidity", 0)).replace(",", "."), ficha.get("holder_count", "?"), examen.IA_MODELO))
                avisar("🤖 %s opina:\n\n%s\n\n⚠️ Una IA contesta siempre y siempre segura. Antes de fiarte, pásale el /examen." % (
                    examen.IA_MODELO, opinion(ficha)))
            else:
                avisar("Pégame un contrato de Solana, o usa /modelo o /examen 100.")
        if not r:
            time.sleep(3)


if __name__ == "__main__":
    if not TOKEN:
        print("Falta TELEGRAM_BOT_TOKEN en el fichero .env")
    else:
        print("Bot con IA en marcha (%s). Pégale un contrato. (Ctrl+C para parar)" % examen.IA_MODELO)
        escuchar_bot()
