#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mirar un contrato de Solana POR DENTRO, gratis y sin clave.
Canal de YouTube: Profesor Diógenes · sección "Bots de Solana", vídeo 2.

    python3 por_dentro.py <DIRECCION_DEL_CONTRATO>

Fuentes (todas públicas): pump.fun, DexScreener, GeckoTerminal y el NODO PÚBLICO de Solana.
Nada de esto pide registrarse ni pagar. A cambio, el nodo público es LENTO y te corta
si le pides muchas cosas seguidas desde la misma IP. Por eso va despacio a propósito.

Saca:
  1. Lo que solo dice pump.fun: el creador, el máximo histórico con su hora, si está bloqueado.
  2. La gráfica minuto a minuto: dónde estuvo el máximo, cuánto tardó y cuánto ha caído.
  3. El censo de holders contado en la propia cadena.
  4. Las PRIMERAS COMPRAS en orden, con los segundos que pasaron desde que nació.
  5. Seguir el dinero hacia atrás varios saltos: de dónde salió el dinero de los más gordos.
  6. (Opcional) Comparar con lo que dice GMGN.

Esto NO es consejo financiero. Es una herramienta para mirar.
"""
import os, sys, time, uuid
import requests


def cargar_env():
    """Lee el fichero .env de al lado (si existe) y mete sus valores en el entorno."""
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(ruta):
        for linea in open(ruta, encoding="utf-8"):
            if "=" in linea and not linea.strip().startswith("#"):
                k, v = linea.strip().split("=", 1)
                if v.strip():
                    os.environ.setdefault(k.strip(), v.strip())


cargar_env()

NODO = os.environ.get("SOLANA_RPC", "https://api.mainnet-beta.solana.com")
PAUSA_NODO = 1.1          # el nodo público aguanta más o menos 1 petición por segundo por IP (da igual cuántas conexiones abras desde esa IP)
SALTOS = 3                # cuántos saltos hacia atrás seguimos el dinero
_ultima = [0.0]


def nodo(metodo, params):
    """Una pregunta al nodo de Solana. Los avisos de 'vas muy rápido' vienen dentro de la respuesta."""
    for intento in range(4):
        espera = PAUSA_NODO - (time.time() - _ultima[0])
        if espera > 0:
            time.sleep(espera)
        _ultima[0] = time.time()
        try:
            r = requests.post(NODO, json={"jsonrpc": "2.0", "id": 1, "method": metodo, "params": params}, timeout=20)
            d = r.json()
        except Exception:
            time.sleep(2); continue
        if d.get("error"):
            if d["error"].get("code") in (429, -32429) or "rate" in str(d["error"]).lower():
                print("   (el nodo dice que vas muy rápido: espero 5 s)")
                time.sleep(5); continue
            return None
        return d.get("result")
    return None


def web(url, navegador=False):
    """navegador=True: pump.fun está detrás de Cloudflare y solo contesta si pareces un navegador."""
    if navegador:
        try:
            from curl_cffi import requests as cr
            r = cr.get(url, impersonate="chrome", timeout=20)
            return r.json() if r.status_code == 200 else None
        except Exception:
            return None
    try:
        r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


def num(x, d=0.0):
    try:
        return float(x)
    except Exception:
        return d


def dinero(x):
    x = abs(x)
    if x >= 1e6: return "%.2f M$" % (x / 1e6)
    if x >= 1e3: return "%.1f K$" % (x / 1e3)
    return "%.0f $" % x


def hora(ts):
    return time.strftime("%d/%m %H:%M", time.localtime(ts)) if ts else "?"


def corto(a):
    return (a or "?")[:10] + "…"


# ─────────────────────────────────────────────────────────────── el nodo
def firmas(direccion, antes=None, limite=1000):
    p = {"limit": limite}
    if antes:
        p["before"] = antes
    return nodo("getSignaturesForAddress", [direccion, p]) or []


def tx(firma):
    return nodo("getTransaction", [firma, {"encoding": "json", "maxSupportedTransactionVersion": 1}])


def claves(t):
    m = t["meta"]; k = list(t["transaction"]["message"]["accountKeys"])
    lk = m.get("loadedAddresses") or {}
    return k + (lk.get("writable") or []) + (lk.get("readonly") or [])


PAGINAS_ATRAS = 5         # para buscar el principio de una billetera: 5 páginas = 5.000 movimientos


def primer_pagador(w):
    """Quién le puso el primer SOL a una billetera: el que más SOL pierde en su operación más antigua.
    Devuelve (pagador, None) o (None, motivo)."""
    antes, ultima = None, None
    for _ in range(PAGINAS_ATRAS):
        s = firmas(w, antes)
        if not s:
            break
        ultima = s[-1]["signature"]; antes = ultima
        if len(s) < 1000:
            break
    else:
        return None, "más de %d.000 movimientos: billetera de máquina" % PAGINAS_ATRAS
    if not ultima:
        return None, "el nodo no contesta"
    t = tx(ultima)
    if not t or not t.get("meta"):
        return None, "el nodo no contesta"
    m = t["meta"]; k = claves(t)
    cambios = [(k[j], m["postBalances"][j] - m["preBalances"][j]) for j in range(min(len(k), len(m["preBalances"])))]
    pierden = [c for c in cambios if c[0] != w and c[1] < 0]
    return (min(pierden, key=lambda c: c[1])[0], None) if pierden else (None, "nació sin que nadie le mandara SOL")


def main(ca):
    t0 = time.time()
    print("═" * 72)
    print(" POR DENTRO: %s" % ca)
    print(" (gratis y sin clave; el nodo público es lento, paciencia)")
    print("═" * 72)

    # ── 1. PUMP.FUN ───────────────────────────────────────────────────
    print("\n[1] LO QUE SOLO DICE PUMP.FUN")
    pf = {}
    for intento in range(4):          # Cloudflare a veces dice que no a la primera; y la ruta cambia (17-nov-2026: coins-v3)
        for ruta in ("coins-v3", "coins-v2"):
            r = web("https://frontend-api-v3.pump.fun/%s/%s" % (ruta, ca), navegador=True) or {}
            if r.get("mint") == ca:
                pf = r; break
        if pf:
            break
        time.sleep(2)
    nacio = num(pf.get("created_timestamp")) / 1000 or None
    if pf:
        print("    %s (%s) · nació %s" % (pf.get("symbol"), pf.get("name"), hora(nacio)))
        print("    creador: %s" % pf.get("creator"))
        print("    máximo histórico: %s el %s" % (dinero(num(pf.get("ath_market_cap"))), hora(num(pf.get("ath_market_cap_timestamp")) / 1000)))
        print("    ¿ha salido ya de la curva de pump? %s · ¿bloqueado por pump.fun? %s" % (
            "sí" if pf.get("complete") else "no", "SÍ" if pf.get("is_banned") else "no"))
    else:
        print("    pump.fun no lo conoce (no nació allí)")
    maquinas = {pf.get("bonding_curve"), pf.get("associated_bonding_curve"), pf.get("pump_swap_pool"), pf.get("raydium_pool")}

    # ── 2. LA GRÁFICA ─────────────────────────────────────────────────
    print("\n[2] LA GRÁFICA MINUTO A MINUTO (GeckoTerminal)")
    pares = (web("https://api.dexscreener.com/latest/dex/tokens/" + ca) or {}).get("pairs") or []
    for p in pares:
        maquinas.add(p.get("pairAddress"))
    pools = (web("https://api.geckoterminal.com/api/v2/networks/solana/tokens/%s/pools" % ca) or {}).get("data") or []
    for p in pools:
        maquinas.add((p.get("attributes") or {}).get("address"))
    velas = []
    if pools:
        mejor = max(pools, key=lambda p: num((p.get("attributes") or {}).get("reserve_in_usd")))
        pool = (mejor.get("attributes") or {}).get("address")
        d = web("https://api.geckoterminal.com/api/v2/networks/solana/pools/%s/ohlcv/minute?aggregate=1&limit=1000&token=%s" % (pool, ca))
        velas = sorted((((d or {}).get("data") or {}).get("attributes") or {}).get("ohlcv_list") or [])
    if velas:
        alto = max(velas, key=lambda v: v[2])
        ahora = velas[-1][4]
        inicio = nacio or velas[0][0]
        print("    máximo de la gráfica: el %s, %.0f minutos después de nacer" % (hora(alto[0]), (alto[0] - inicio) / 60))
        print("    desde el máximo ha caído un %.0f%%" % (100 * (1 - ahora / alto[2])) if alto[2] else "")
        print("    (%d velas de un minuto)" % len(velas))
    else:
        print("    sin velas todavía")
    maquinas.discard(None)

    # ── 3. EL CENSO EN LA CADENA ──────────────────────────────────────
    print("\n[3] EL CENSO DE HOLDERS, CONTADO EN LA CADENA")
    holders = {}
    pagina = 1
    while pagina <= 10:
        r = nodo("getTokenAccounts", {"mintAddress": ca, "limit": 1000, "page": pagina})
        items = (r or {}).get("token_accounts") or []
        for it in items:
            q = int(it.get("amount") or 0)
            if q > 0 and it.get("owner"):
                holders[it["owner"]] = holders.get(it["owner"], 0) + q
        if len(items) < 1000:
            break
        pagina += 1
    total = sum(holders.values())
    personas = {w: q for w, q in holders.items() if w not in maquinas}
    top = sorted(personas.items(), key=lambda x: -x[1])
    if total:
        print("    %d billeteras con saldo · las 10 más gordas (sin contar pools) tienen el %.1f%%" % (
            len(holders), 100 * sum(q for _, q in top[:10]) / total))
        print("    (ojo: este censo del nodo público va con algo de retraso)")
    else:
        print("    el nodo no ha contestado al censo")

    # ── 4. LAS PRIMERAS COMPRAS ───────────────────────────────────────
    print("\n[4] LAS PRIMERAS COMPRAS, EN ORDEN")
    antes, todas = None, []
    llegamos = False
    for _ in range(40):                       # hasta 40.000 movimientos hacia atrás (unos 45 s)
        s = firmas(ca, antes)
        if not s:
            break
        todas += s; antes = s[-1]["signature"]
        if len(s) < 1000:
            llegamos = True
            break
    if not llegamos:
        print("    (tiene más de 40.000 movimientos: estas son las más antiguas que alcanzamos, NO las primeras)")
    primeras = [f for f in reversed(todas) if not f.get("err")][:40]
    origen = nacio or (primeras[0].get("blockTime") if primeras else None)
    vistos = []
    for f in primeras:
        if len(vistos) >= 10:
            break
        t = tx(f["signature"])
        if not t or not t.get("meta"):
            continue
        pre = {(b.get("owner"), b.get("mint")): int((b.get("uiTokenAmount") or {}).get("amount") or 0) for b in t["meta"].get("preTokenBalances") or []}
        post = {(b.get("owner"), b.get("mint")): int((b.get("uiTokenAmount") or {}).get("amount") or 0) for b in t["meta"].get("postTokenBalances") or []}
        for (dueno, mint), q in post.items():
            if mint == ca and q > pre.get((dueno, mint), 0) and dueno not in maquinas and dueno not in vistos:
                if len(vistos) >= 10:
                    break
                vistos.append(dueno)
                print("    %2d. %s  a los %3d s  %s" % (len(vistos), corto(dueno), int((t.get("blockTime") or origen) - origen),
                                                     "<- el creador" if dueno == pf.get("creator") else ""))
    if llegamos and vistos:
        print("    mira los segundos: una persona con el ratón no compra en el segundo cero")

    # ── 5. SEGUIR EL DINERO ───────────────────────────────────────────
    print("\n[5] SEGUIR EL DINERO HACIA ATRÁS (%d saltos) de los 8 más gordos" % SALTOS)
    raices = {}
    for w, q in top[:8]:
        cadena, actual, motivo = [w], w, None
        for _ in range(SALTOS):
            pag, motivo = primer_pagador(actual)
            if not pag or pag in cadena:
                break
            cadena.append(pag); actual = pag
        raices.setdefault(cadena[-1], []).append(w)
        print("    %s (%.1f%%): %s" % (corto(w), 100 * q / total if total else 0,
                                     " <- ".join(corto(x) for x in cadena[1:]) or ("no se sigue: " + (motivo or "?"))))
    juntos = {r: ws for r, ws in raices.items() if len(ws) > 1}
    for r, ws in juntos.items():
        print("    ⚠️  %d de los gordos salen del mismo dinero: %s" % (len(ws), corto(r)))

    # ── 6. ¿CUADRA CON GMGN? ──────────────────────────────────────────
    clave = os.environ.get("GMGN_API_KEY") or "gmgn_solbscbaseethmonadtron"   # la pública de pruebas
    print("\n[6] ¿CUADRA CON LO QUE DICE GMGN?")
    try:
        q = {"chain": "sol", "address": ca, "timestamp": int(time.time()), "client_id": str(uuid.uuid4())}
        info = requests.get("https://openapi.gmgn.ai/v1/token/info", params=q, timeout=20,
                            headers={"X-APIKEY": clave}).json().get("data") or {}
        hg = (info.get("stat") or {}).get("holder_count") or info.get("holder_count")
        print("    holders: GMGN dice %s · la cadena dice %d" % (hg, len(holders)))
        print("    creador: GMGN dice %s · pump.fun dice %s" % (
            corto((info.get("dev") or {}).get("creator_address")), corto(pf.get("creator"))))
    except Exception:
        print("    no se ha podido preguntar a GMGN")

    print("\n" + "─" * 72)
    print(" Hecho en %.0f s. Lento a propósito: el nodo público corta por IP si corres." % (time.time() - t0))
    print(" No es consejo financiero.")
    print("─" * 72)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 por_dentro.py <DIRECCION_DEL_CONTRATO>")
        sys.exit(1)
    main(sys.argv[1].strip())
