#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Radiografía de los holders de un token de Solana: granjas (muchas billeteras con el mismo dueño),
supply escondido (billeteras que tienen el token sin haberlo comprado) y repartos calcados.
Canal de YouTube: Profesor Diógenes · sección "Bots de Solana", vídeo 7.

    python3 radiografia.py <contrato>          (o con el bot: python3 bot.py)

Qué mira:
  1. Los 100 mayores holders, con GMGN (vale la clave pública de pruebas).
  2. GRANJAS: los holders a los que les mandó el primer SOL la MISMA billetera. Un bolsillo detrás.
     Y un paso más atrás, con el nodo público de Solana: si dos de esos "pagadores" los pagó a su vez
     la misma billetera, se juntan en la misma banda.
  3. SUPPLY ESCONDIDO: tienen el token y no lo han comprado nunca (se lo pasaron), o lo han ido
     sacando a otras billeteras para que no se les vea el tamaño.
  4. REPARTOS CALCADOS: varias billeteras con exactamente el mismo % del supply. Eso es un reparto a mano.

Lo que NO ve: los que compraron y ya se fueron del todo (GMGN solo da los holders de ahora).
Esto NO es consejo financiero. Es una herramienta para mirar.
"""
import os, sys, time, uuid
from collections import defaultdict, Counter
import requests

HOST = "https://openapi.gmgn.ai"
CLAVE_DE_PRUEBAS = "gmgn_solbscbaseethmonadtron"   # la pública de GMGN, solo para probar


def cargar_env(ruta=None):
    ruta = ruta or os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(ruta):
        return
    for linea in open(ruta, encoding="utf-8"):
        linea = linea.strip()
        if linea and not linea.startswith("#") and "=" in linea:
            k, v = linea.split("=", 1)
            if v.strip():
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


cargar_env()
CLAVE = os.environ.get("GMGN_API_KEY") or CLAVE_DE_PRUEBAS
NODO = os.environ.get("SOLANA_RPC", "https://api.mainnet-beta.solana.com")
PASO_ATRAS = int(os.environ.get("PASO_ATRAS", "12"))   # a cuántos pagadores les buscamos su propio pagador en el nodo
_ultima_gmgn, _ultima_nodo = [0.0], [0.0]


# ───────────────────────────────────────────────── las fuentes
def gmgn(ruta, peso=5, **parametros):
    """GMGN gratis: un cubo de 5 unidades que se rellena a 5 por segundo. Los holders pesan 5."""
    espera = peso / 5.0 - (time.time() - _ultima_gmgn[0])
    if espera > 0:
        time.sleep(espera)
    q = dict(parametros, timestamp=int(time.time()), client_id=str(uuid.uuid4()))
    for intento in range(3):
        try:
            r = requests.get(HOST + ruta, params=q, timeout=25, headers={"X-APIKEY": CLAVE, "User-Agent": "profesor-diogenes"})
            _ultima_gmgn[0] = time.time()
            if r.status_code == 429:
                print("   (GMGN pide calma: espero 10 s)"); time.sleep(10)
                q.update(timestamp=int(time.time()), client_id=str(uuid.uuid4())); continue
            d = r.json()
            if str(d.get("code")) not in ("0", "None"):
                print("   (GMGN contesta %s: %s)" % (d.get("code"), d.get("message") or d.get("error")))
                return None
            return d.get("data")
        except Exception as e:
            print("   (fallo de red: %s)" % str(e)[:60]); time.sleep(2)
    return None


def nodo(metodo, params):
    """El nodo público de Solana: más o menos una pregunta por segundo por IP."""
    for intento in range(4):
        espera = 1.1 - (time.time() - _ultima_nodo[0])
        if espera > 0:
            time.sleep(espera)
        _ultima_nodo[0] = time.time()
        try:
            d = requests.post(NODO, json={"jsonrpc": "2.0", "id": 1, "method": metodo, "params": params}, timeout=20).json()
        except Exception:
            time.sleep(2); continue
        if d.get("error"):
            if d["error"].get("code") in (429, -32429) or "rate" in str(d["error"]).lower():
                time.sleep(5); continue
            return None
        return d.get("result")
    return None


def primer_pagador(w, paginas=3):
    """Quién le puso el primer SOL a una billetera (su operación más antigua). Hasta 3.000 movimientos atrás."""
    antes, ultima = None, None
    for _ in range(paginas):
        p = {"limit": 1000}
        if antes:
            p["before"] = antes
        s = nodo("getSignaturesForAddress", [w, p]) or []
        if not s:
            break
        ultima = antes = s[-1]["signature"]
        if len(s) < 1000:
            break
    else:
        return None                        # demasiados movimientos: es una máquina o un exchange
    if not ultima:
        return None
    t = nodo("getTransaction", [ultima, {"encoding": "json", "maxSupportedTransactionVersion": 1}])
    if not t or not t.get("meta"):
        return None
    m = t["meta"]; k = list(t["transaction"]["message"]["accountKeys"])
    k += ((m.get("loadedAddresses") or {}).get("writable") or []) + ((m.get("loadedAddresses") or {}).get("readonly") or [])
    pierden = [(k[j], m["postBalances"][j] - m["preBalances"][j]) for j in range(min(len(k), len(m["preBalances"])))
               if k[j] != w and m["postBalances"][j] < m["preBalances"][j]]
    return min(pierden, key=lambda c: c[1])[0] if pierden else None


# ───────────────────────────────────────────────── ayudas
def num(x, d=0.0):
    try:
        return float(x)
    except Exception:
        return d


def corto(a):
    return (a or "?")[:6] + "…" + (a or "?")[-4:]


def es_maquina(h):
    """La curva de pump.fun, el pool o un exchange no son personas."""
    return bool(h.get("exchange")) or h.get("addr_type") not in (0, None) or "pool" in " ".join(h.get("tags") or []).lower()


def pagador(h):
    """Quién le mandó el primer SOL según GMGN. Si es un exchange con nombre, no cuenta: paga a miles."""
    nt = h.get("native_transfer") or {}
    a = nt.get("from_address") or nt.get("address")
    return (a, nt.get("name")) if a else (None, None)


# ───────────────────────────────────────────────── el análisis
def main(ca):
    t0 = time.time()
    info = gmgn("/v1/token/info", peso=1, chain="sol", address=ca) or {}
    datos = gmgn("/v1/market/token_top_holders", chain="sol", address=ca, limit=100)
    H = (datos.get("list") if isinstance(datos, dict) else datos) or []
    if not H:
        print("GMGN no da holders de este contrato."); return
    simbolo = info.get("symbol") or ca[:6]
    print("RADIOGRAFÍA DE HOLDERS · %s" % simbolo)
    print("%s\n" % ca)

    personas = [h for h in H if not es_maquina(h)]
    pct = lambda h: 100 * num(h.get("amount_percentage"))
    total_top = sum(pct(h) for h in personas)
    print("Los %d mayores holders que son billeteras (sin la curva ni el pool) tienen el %.1f %% del supply." % (len(personas), total_top))

    # ── 1. GRANJAS: mismo pagador
    grupos, exchanges = defaultdict(list), Counter()
    for h in personas:
        a, nombre = pagador(h)
        if not a:
            continue
        if nombre:                       # lo fondeó un exchange (Binance, OKX…): no es una banda
            exchanges[nombre] += 1
            continue
        grupos[a].append(h)

    # un paso más atrás, con el nodo: ¿quién pagó a los pagadores?
    bandas = {a: [a] for a in grupos}
    pagadores = sorted(grupos, key=lambda a: -sum(pct(h) for h in grupos[a]))[:PASO_ATRAS]
    if pagadores:
        print("\n(mirando en el nodo de Solana quién pagó a los %d pagadores principales: 1-2 s cada uno)" % len(pagadores))
    abuelo = {}
    for a in pagadores:
        ab = primer_pagador(a)
        if ab:
            abuelo[a] = ab
    por_abuelo = defaultdict(list)
    for a, ab in abuelo.items():
        por_abuelo[ab].append(a)
    juntas = []
    for ab, hijos in por_abuelo.items():
        if len(hijos) > 1:               # dos pagadores distintos pagados por el mismo: misma banda
            juntas.append((ab, hijos))
    banda_de = {a: a for a in grupos}
    for ab, hijos in juntas:
        for hj in hijos:
            banda_de[hj] = ab
    final = defaultdict(list)
    for a, hs in grupos.items():
        final[banda_de[a]] += hs
    granjas = {k: v for k, v in final.items() if len(v) > 1}

    print("\n[1] GRANJAS · billeteras que salen del mismo dinero")
    if not granjas:
        print("    Ninguna: cada holder grande tiene su propio pagador.")
    en_granjas = 0.0
    for k, v in sorted(granjas.items(), key=lambda x: -sum(pct(h) for h in x[1]))[:6]:
        p = sum(pct(h) for h in v); en_granjas += p
        via = " (juntando a varios pagadores que pagó él)" if k in por_abuelo and len(por_abuelo[k]) > 1 else ""
        print("    %s pagó a %d holders que juntos tienen el %.2f %%%s" % (corto(k), len(v), p, via))
        for h in sorted(v, key=lambda h: -pct(h))[:4]:
            print("       · %s  %.2f %%" % (corto(h.get("address")), pct(h)))
    if exchanges:
        print("    (%d holders los fondeó un exchange: %s. Eso no cuenta como banda.)" % (
            sum(exchanges.values()), ", ".join("%s %d" % x for x in exchanges.most_common(3))))

    # ── 2. SUPPLY ESCONDIDO
    print("\n[2] SUPPLY ESCONDIDO")
    sin_comprar = [h for h in personas if pct(h) >= 0.3 and num(h.get("buy_tx_count_cur")) == 0
                   and num(h.get("history_bought_cost")) == 0]
    recibieron = [h for h in personas if h not in sin_comprar and pct(h) >= 0.3
                  and (h.get("transfer_in") or num(h.get("history_transfer_in_amount")) > 0)]
    sacan = [h for h in personas if num(h.get("transfer_out_count")) > 0 and num(h.get("history_transfer_out_amount")) > 0]
    escondido = sum(pct(h) for h in sin_comprar)
    if sin_comprar:
        print("    Tienen el token y NO lo han comprado nunca (se lo pasaron): %d, con el %.2f %%" % (len(sin_comprar), escondido))
        for h in sorted(sin_comprar, key=lambda h: -pct(h))[:5]:
            print("       · %s  %.2f %%" % (corto(h.get("address")), pct(h)))
    if recibieron:
        print("    Compraron algo pero también les llegó por transferencia: %d" % len(recibieron))
    if sacan:
        print("    Han ido sacando tokens a otras billeteras: %d" % len(sacan))
        for h in sorted(sacan, key=lambda h: -num(h.get("transfer_out_count")))[:3]:
            print("       · %s  %d envíos  (le queda el %.2f %%)" % (corto(h.get("address")), int(num(h.get("transfer_out_count"))), pct(h)))
    if not (sin_comprar or recibieron or sacan):
        print("    Nada: todos los holders grandes compraron lo que tienen.")

    # ── 3. REPARTOS CALCADOS
    print("\n[3] REPARTOS CALCADOS · el mismo % exacto en varias billeteras")
    iguales = Counter(round(pct(h), 3) for h in personas if pct(h) >= 0.05)   # a 3 decimales: casualidad, casi nunca
    calcados = [(p, n) for p, n in iguales.items() if n >= 3]
    if calcados:
        for p, n in sorted(calcados, key=lambda x: -x[1])[:4]:
            print("    %d billeteras con exactamente el %.3f %%" % (n, p))
    else:
        print("    Ninguno.")

    # ── resumen
    print("\nRESUMEN")
    print("    en granjas: %.1f %% del supply · sin haberlo comprado: %.1f %% · repartos calcados: %s" % (
        en_granjas, escondido, "sí" if calcados else "no"))
    print("    Esto te dice QUIÉN puede tirarte el precio encima, no si el token va a subir.")
    print("\n(%.0f s · GMGN + nodo público de Solana · no es consejo financiero)" % (time.time() - t0))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("uso: python3 radiografia.py <contrato>"); sys.exit(1)
    main(sys.argv[1])
