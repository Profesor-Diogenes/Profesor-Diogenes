#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
El creador (dev) de un token de pump.fun, mirado en la cadena: de dónde le viene el dinero, a dónde lo manda,
si se compra su propio token y si ha pagado a billeteras que luego aparecen como holders.
Canal de YouTube: Profesor Diógenes · sección "Bots de Solana", vídeo 8.

    python3 dev.py <contrato>          (o con el bot: python3 bot.py)

De dónde sale cada cosa (todo gratis):
  - el creador, con su dirección completa, y la curva y el pool del token -> pump.fun
  - quién le mandó SOL al creador y a quién se lo mandó él, con cantidades  -> nodo público de Solana
  - los mayores holders del token -> GMGN (vale la clave pública de pruebas)

Lo que NO ve: los movimientos más antiguos que las últimas operaciones que miramos (OPERACIONES, 40 por defecto)
ni los saltos de más de una billetera de distancia.
Esto NO es consejo financiero. Es una herramienta para mirar.
"""
import os, sys, time, uuid
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
OPERACIONES = int(os.environ.get("OPERACIONES", "40"))   # cuántas operaciones del creador leemos
LAM = 1e9
_ultima_nodo = [0.0]


# ───────────────────────────────────────────────── las fuentes
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


def pump(ca):
    """pump.fun está detrás de Cloudflare: con curl_cffi se hace pasar por un navegador normal.
    Cloudflare a veces dice que no a la primera, así que se insiste unas pocas veces.
    Y pump.fun cambia la ruta de vez en cuando (el 17-nov-2026 pasó de coins-v2 a coins-v3): se prueban las dos."""
    from curl_cffi import requests as cr
    for intento in range(6):
        for ruta in ("coins-v3", "coins-v2"):
            try:
                r = cr.get("https://frontend-api-v3.pump.fun/%s/%s" % (ruta, ca), impersonate="chrome", timeout=20)
                if r.status_code == 200 and r.json().get("mint") == ca:
                    return r.json()
            except Exception:
                pass
        time.sleep(2)
    return None


def holders(ca, n=20):
    q = dict(chain="sol", address=ca, limit=max(n, 40), timestamp=int(time.time()), client_id=str(uuid.uuid4()))
    try:
        d = requests.get(HOST + "/v1/market/token_top_holders", params=q, timeout=25,
                         headers={"X-APIKEY": CLAVE, "User-Agent": "profesor-diogenes"}).json().get("data")
    except Exception:
        return []
    l = (d.get("list") if isinstance(d, dict) else d) or []
    return [(h.get("address"), 100 * float(h.get("amount_percentage") or 0)) for h in l[:n]]


# ───────────────────────────────────────────────── el dinero del creador
def movimientos(w, limite):
    """Todo el SOL que le entra y le sale en sus últimas operaciones, y de/para quién."""
    firmas = nodo("getSignaturesForAddress", [w, {"limit": limite}]) or []
    entra, sale = {}, {}
    for s in firmas:
        t = nodo("getTransaction", [s["signature"], {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 1}])
        if not t or not t.get("meta"):
            continue
        ins = list(((t.get("transaction") or {}).get("message") or {}).get("instructions") or [])
        for inner in t["meta"].get("innerInstructions") or []:
            ins += inner.get("instructions") or []
        for i in ins:
            p = i.get("parsed") if isinstance(i, dict) else None
            if not isinstance(p, dict) or i.get("program") != "system" or not str(p.get("type", "")).startswith("transfer"):
                continue
            inf = p.get("info") or {}
            lam = int(inf.get("lamports") or 0)
            if lam <= 0:
                continue
            if inf.get("destination") == w:
                entra[inf["source"]] = entra.get(inf["source"], 0) + lam
            elif inf.get("source") == w:
                sale[inf["destination"]] = sale.get(inf["destination"], 0) + lam
    return entra, sale, len(firmas)


def perfil(w):
    """Para saber si una billetera es 'de paso' bastan dos preguntas: cuántos movimientos tiene y qué saldo le queda."""
    n = len(nodo("getSignaturesForAddress", [w, {"limit": 1000}]) or [])
    saldo = ((nodo("getBalance", [w]) or {}).get("value") or 0) / LAM
    return n, saldo


def etiqueta(w):
    n, saldo = perfil(w)
    if n >= 1000:
        return "más de 1.000 movimientos y %.2f SOL de saldo: cartera de paso o exchange" % saldo
    if n <= 5:
        return "casi virgen (%d movimientos): billetera recién hecha" % n
    return "%d movimientos, %.2f SOL de saldo" % (n, saldo)


def corto(a):
    return (a or "?")[:6] + "…" + (a or "?")[-4:]


# ───────────────────────────────────────────────── el análisis
def main(ca):
    t0 = time.time()
    p = pump(ca)
    if not p or not p.get("creator"):
        print("pump.fun no conoce este contrato (¿no es de pump.fun?)."); return
    dev = p["creator"]
    maquinas = {p.get("bonding_curve"), p.get("associated_bonding_curve"), p.get("pool_address"), p.get("pump_swap_pool")} - {None, ""}
    print("EL DEV EN LA CADENA · %s (%s)" % (p.get("symbol"), p.get("name")))
    print("contrato %s" % ca)
    print("creador  %s" % dev)
    print("%s · capitalización máxima %.0f $%s\n" % (
        "ya salió de la curva" if p.get("complete") else "sigue en la curva de pump.fun",
        float(p.get("ath_market_cap") or 0), " · ⚠ BANEADO EN PUMP.FUN" if p.get("is_banned") else ""))

    print("(leyendo en el nodo las últimas %d operaciones del creador: 1 por segundo)" % OPERACIONES)
    entra, sale, n = movimientos(dev, OPERACIONES)
    te, ts = sum(entra.values()) / LAM, sum(sale.values()) / LAM
    print("\n[1] LA CAJA DEL CREADOR (sus últimas %d operaciones)" % n)
    print("    le entraron %.3f SOL · sacó %.3f SOL · saldo de las transferencias %+.3f SOL" % (te, ts, ts - te))
    print("    (las compras y ventas de tokens no salen aquí: solo el SOL que manda y recibe)")

    print("\n[2] QUIÉN LE MANDA EL DINERO A ÉL")
    if not entra:
        print("    Nadie en estas operaciones (se fondeó antes).")
    for k, v in sorted(entra.items(), key=lambda x: -x[1])[:4]:
        print("    %s  %.3f SOL  · %s" % (corto(k), v / LAM, etiqueta(k)))

    print("\n[3] A QUIÉN LE MANDA ÉL EL DINERO")
    if not sale:
        print("    A nadie todavía.")
    autocompra = 0.0
    for k, v in sorted(sale.items(), key=lambda x: -x[1])[:6]:
        if k in maquinas:
            autocompra += v / LAM
            print("    %s  %.3f SOL  · ES LA CURVA DE SU PROPIO TOKEN: se está comprando a sí mismo" % (corto(k), v / LAM))
            continue
        print("    %s  %.3f SOL  · %s" % (corto(k), v / LAM, etiqueta(k)))
    if autocompra:
        print("    >>> %.3f SOL metidos por el creador en su propio token" % autocompra)

    print("\n[4] LOS MAYORES HOLDERS, Y SI EL CREADOR LES PAGÓ")
    cruce = []
    for w, pc in holders(ca, 15):
        marca = ""
        if w in maquinas:
            marca = "  [la curva o el pool]"
        elif w == dev:
            marca = "  [EL CREADOR]"
        elif w in sale:
            marca = "  <<< EL CREADOR LE MANDÓ %.3f SOL" % (sale[w] / LAM)
            cruce.append(w)
        print("    %6.2f %%  %s%s" % (pc, corto(w), marca))

    print("\n[5] EL CRUCE")
    if cruce:
        print("    SÍ: %d holders grandes recibieron SOL del creador. Eso no es un mercado: es el creador comprándose a sí mismo con otras billeteras." % len(cruce))
    else:
        print("    Ningún holder grande recibió SOL directamente del creador (a un salto más de distancia no lo vemos).")
    print("\n(%.0f s · pump.fun + nodo público de Solana + GMGN · no es consejo financiero)" % (time.time() - t0))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("uso: python3 dev.py <contrato>"); sys.exit(1)
    main(sys.argv[1])
