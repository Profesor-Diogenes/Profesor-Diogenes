#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Medir sin hacerse trampas: a qué llegó cada contrato DESDE QUE LO VISTE TÚ, no desde antes.
Lee la libreta del vídeo 15 (libreta.db) y baja las velas minuto a minuto de cada token.
Canal de YouTube: Profesor Diógenes · sección "Bots de Solana", vídeo 16.

    python3 medir.py            (pon al lado el fichero libreta.db del vídeo 15)

Cómo se usa, desde tu bot:
  /mide            -> mide todo lo que lleve al menos 6 horas en la libreta y te da el resumen
  /mide 3          -> lo mismo con una ventana de 3 horas
  /detalle         -> los contratos uno a uno

Las tres reglas para no engañarse (cada una nos costó un disgusto):
  1. Se entra en la vela SIGUIENTE al momento en que lo viste. Nunca en la misma, nunca antes.
  2. Si en esas horas el token movió menos de 1.000 $ en total, NO se mide: un precio sin volumen no es un precio.
  3. El máximo que cuenta es el de DESPUÉS de verlo. El bot te enseña también la cuenta tramposa
     (contando desde que nació el token) para que veas cuánto cambia.

Las velas salen de GeckoTerminal (gratis, sin clave, unas 10 preguntas por minuto: por eso va despacio).
Esto NO es consejo financiero. Es una herramienta para mirar.
"""
import os, time, sqlite3, threading
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
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
MI_ID = os.environ.get("TELEGRAM_MI_ID", "").strip()
BOT = "https://api.telegram.org/bot%s/" % TOKEN
BASE = os.environ.get("LIBRETA", os.path.join(AQUI, "libreta.db"))
GECKO = "https://api.geckoterminal.com/api/v2/networks/solana"
VOLUMEN_MINIMO = 1000
_ultima = [0.0]
ultimo_detalle = []


def telegram(metodo, **datos):
    try:
        return requests.post(BOT + metodo, json=datos, timeout=60).json()
    except Exception:
        return {}


def avisar(texto):
    for i in range(0, len(texto), 3800):
        telegram("sendMessage", chat_id=MI_ID, text=texto[i:i + 3800], parse_mode="HTML", disable_web_page_preview=True)


def gecko(ruta, **p):
    """GeckoTerminal gratis: unas 10 preguntas por minuto. Vamos a una cada 6,5 segundos; si aun así corta, se espera."""
    for intento in range(8):
        espera = 6.5 - (time.time() - _ultima[0])
        if espera > 0:
            time.sleep(espera)
        _ultima[0] = time.time()
        try:
            r = requests.get(GECKO + ruta, params=p, timeout=25, headers={"Accept": "application/json"})
            if r.status_code == 429:
                time.sleep(30); continue
            return r.json() if r.status_code == 200 else None
        except Exception:
            time.sleep(3)
    return None


def pools_gordos(contratos):
    """El pool con más liquidez de cada token, preguntando a DexScreener de 30 en 30 (gratis y rápido).
    No vale cualquier pool: uno vacío da precios fantasma."""
    out = {}
    for i in range(0, len(contratos), 30):
        try:
            pares = requests.get("https://api.dexscreener.com/latest/dex/tokens/" + ",".join(contratos[i:i + 30]), timeout=15).json().get("pairs") or []
        except Exception:
            pares = []
        # Ojo: esa pregunta devuelve como mucho 30 PARES en total, no 30 tokens. Si en el lote hay un token con
        # muchos pools, se come el cupo y los demás no salen. Esta otra devuelve un par de cada token: no falta ninguno.
        try:
            uno = requests.get("https://api.dexscreener.com/tokens/v1/solana/" + ",".join(contratos[i:i + 30]), timeout=15).json()
            pares += uno if isinstance(uno, list) else []
        except Exception:
            pass
        for par in sorted(pares, key=lambda x: float((x.get("liquidity") or {}).get("usd") or 0)):
            ca = (par.get("baseToken") or {}).get("address")
            if ca in contratos and par.get("pairAddress"):
                out[ca] = par["pairAddress"]
        time.sleep(0.3)
    return out


def velas(pool, desde, hasta):
    """Velas de un minuto entre dos momentos: [hora, apertura, máximo, mínimo, cierre, volumen], de vieja a nueva."""
    todas, antes = [], hasta + 60
    for _ in range(3):                                   # 3 páginas de 1.000 minutos = 50 horas
        d = gecko("/pools/%s/ohlcv/minute" % pool, aggregate=1, limit=1000, before_timestamp=antes)
        if d is None:
            return None                                  # GeckoTerminal no ha contestado: no es lo mismo que "no hay velas"
        l = (((d.get("data") or {}).get("attributes") or {}).get("ohlcv_list")) or []
        if not l:
            break
        todas += l
        antes = min(x[0] for x in l)
        if antes <= desde or len(l) < 1000:
            break
    return sorted([[int(x[0])] + [float(y) for y in x[1:]] for x in todas if x[0] <= hasta], key=lambda x: x[0])


def medir_uno(pool, visto, horas):
    """Devuelve un diccionario con la medida, o {"motivo": ...} si no se puede medir."""
    if not pool:
        return {"motivo": "sin pool"}
    v = velas(pool, visto - 6 * 3600, visto + horas * 3600)
    if v is None:
        return {"motivo": "GeckoTerminal no contesta (vuelve a pedirlo luego)"}
    despues = [x for x in v if x[0] > visto]              # REGLA 1: solo velas que EMPIEZAN después de verlo
    if len(despues) < 2:
        return {"motivo": "sin velas después"}
    if sum(x[5] for x in despues) < VOLUMEN_MINIMO:      # REGLA 2: sin volumen no hay precio
        return {"motivo": "sin volumen"}
    entrada = despues[0][1]                               # la apertura de la primera vela después de verlo
    if not entrada:
        return {"motivo": "sin precio"}
    maximo, minimo = entrada, entrada
    dobla = mitad = None
    for x in despues:
        maximo = max(maximo, x[2]); minimo = min(minimo, x[3])
        if dobla is None and x[2] >= 2 * entrada: dobla = x[0]
        if mitad is None and x[3] <= 0.5 * entrada: mitad = x[0]
    primer_precio = v[0][1] or entrada                    # la cuenta TRAMPOSA: desde 6 horas antes de verlo (o desde que nació)
    return {"x_max": maximo / entrada, "x_min": minimo / entrada, "x_fin": despues[-1][4] / entrada,
            "dobla_antes_de_caer": dobla is not None and (mitad is None or dobla <= mitad),
            "x_max_tramposo": max(x[2] for x in v) / primer_precio}


def medir(horas=6):
    if not os.path.exists(BASE):
        return "No encuentro libreta.db. Pon aquí la libreta del vídeo 15 (o indica su ruta en LIBRETA, en el .env)."
    b = sqlite3.connect(BASE)
    filas = b.execute("SELECT contrato, simbolo, visto, origen FROM contratos WHERE visto < ? ORDER BY visto", (time.time() - horas * 3600,)).fetchall()
    if not filas:
        return "Ningún contrato lleva todavía %d horas en la libreta." % horas
    avisar("Midiendo %d contratos con una ventana de %d horas. Tardo unos %d minutos (GeckoTerminal gratis va despacio)." % (
        len(filas), horas, max(1, len(filas) * 7 // 60)))
    ok, fuera = [], {}
    ultimo_detalle.clear()
    pools = pools_gordos([f[0] for f in filas])
    for ca, simbolo, visto, origen in filas:
        m = medir_uno(pools.get(ca), visto, horas)
        if "motivo" in m:
            fuera[m["motivo"]] = fuera.get(m["motivo"], 0) + 1
            continue
        m.update(simbolo=simbolo, origen=origen); ok.append(m)
        ultimo_detalle.append("%s (%s): máximo x%.2f · mínimo x%.2f · acaba x%.2f" % (simbolo, origen, m["x_max"], m["x_min"], m["x_fin"]))
    if not ok:
        return "No se ha podido medir ninguno (%s)." % ", ".join("%s: %d" % x for x in fuera.items())
    n = len(ok); pct = lambda k: 100.0 * k / n
    finales = sorted(m["x_fin"] for m in ok)
    return ("📏 MEDIDO SIN TRAMPA · ventana de %d horas desde que lo viste\n"
            "Medidos: %d · sin medir: %s\n\n"
            "• llegan a doblar: <b>%.0f %%</b> (%d)\n"
            "• doblan ANTES de caer a la mitad: <b>%.0f %%</b> (%d)\n"
            "• caen a la mitad en algún momento: <b>%.0f %%</b> (%d)\n"
            "• precio típico al final de la ventana: <b>x%.2f</b>\n\n"
            "La cuenta tramposa (contando desde 6 horas antes de verlo, o desde que nació): doblan el <b>%.0f %%</b>.\n"
            "Esa diferencia es la que hace que cualquier ranking parezca bueno." % (
                horas, n, ", ".join("%s %d" % x for x in fuera.items()) or "ninguno",
                pct(sum(m["x_max"] >= 2 for m in ok)), sum(m["x_max"] >= 2 for m in ok),
                pct(sum(m["dobla_antes_de_caer"] for m in ok)), sum(m["dobla_antes_de_caer"] for m in ok),
                pct(sum(m["x_min"] <= 0.5 for m in ok)), sum(m["x_min"] <= 0.5 for m in ok),
                finales[n // 2], pct(sum(m["x_max_tramposo"] >= 2 for m in ok))))


def escuchar_bot():
    desde = 0
    while True:
        r = telegram("getUpdates", offset=desde, timeout=50, allowed_updates=["message"])
        for u in r.get("result") or []:
            desde = u["update_id"] + 1
            m = u.get("message") or {}
            chat = (m.get("chat") or {}).get("id")
            quien = str((m.get("from") or {}).get("id"))
            p = (m.get("text") or "").strip().lower().split()
            if not chat or not p:
                continue
            if not MI_ID:
                telegram("sendMessage", chat_id=chat, text="Tu número de usuario es %s. Ponlo en TELEGRAM_MI_ID del .env y vuelve a arrancar." % quien)
                continue
            if quien != MI_ID:
                continue
            if p[0] == "/mide":
                horas = int(p[1]) if len(p) > 1 and p[1].isdigit() else 6
                threading.Thread(target=lambda: avisar(medir(horas)), daemon=True).start()
            elif p[0] == "/detalle":
                avisar("\n".join(ultimo_detalle) or "Primero pide /mide.")
            else:
                avisar("Órdenes: /mide · /mide 3 · /detalle")
        if not r:
            time.sleep(3)


def main():
    if not TOKEN:
        print("Falta TELEGRAM_BOT_TOKEN en el fichero .env"); return
    print("Medidor en marcha. Escríbele /mide a tu bot. (Ctrl+C para parar)")
    escuchar_bot()


if __name__ == "__main__":
    main()
