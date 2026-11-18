#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analizar una billetera de Solana: ¿quién es, cómo juega y de dónde le viene el dinero?
Canal de YouTube: Profesor Diógenes · sección "Bots de Solana", vídeo 3.

    python3 billetera.py <DIRECCION_DE_LA_BILLETERA>

Fuentes: GMGN (con tu clave o con la pública de pruebas), DexScreener y el nodo público de Solana.
Todo gratis. Va despacio a propósito para no pasarse de los límites.

Saca:
  1. La ficha: desde cuándo existe, saldo, etiquetas que le pone GMGN, cuántos tokens ha creado.
  2. Cómo le va: lo ganado, el porcentaje de aciertos y el reparto de resultados.
  3. Cómo juega: cuánto aguanta, cuántas operaciones hace por token.
  4. Sus últimos tokens: cuántos están muertos HOY y en cuántos de esos salió ganando.
  5. De dónde le vino el dinero, y comprobarlo en la propia cadena.
  6. El veredicto: normal, bot, víctima, sospechosa o tumbadora.

Esto NO es consejo financiero. Es una herramienta para mirar.
"""
import os, sys, time, uuid, statistics
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
CLAVE = os.environ.get("GMGN_API_KEY") or "gmgn_solbscbaseethmonadtron"   # la pública de pruebas de GMGN
NODO = os.environ.get("SOLANA_RPC", "https://api.mainnet-beta.solana.com")
COMPROBAR = 25             # cuántas de sus últimas compras/ventas se comprueban una a una en la cadena
WSOL = "So11111111111111111111111111111111111111112"   # la moneda SOL "envuelta" (dirección pública)  # pragma: allowlist secret
PAGINAS = 4                 # 4 páginas de 50 = sus últimas 200 operaciones
MUERTO_LIQUIDEZ = 1000      # un token con menos de 1.000 $ de liquidez lo damos por muerto
_ultima = {"gmgn": 0.0, "nodo": 0.0}


def esperar(quien, pausa):
    falta = pausa - (time.time() - _ultima[quien])
    if falta > 0:
        time.sleep(falta)
    _ultima[quien] = time.time()


def gmgn(ruta, **p):
    """Una pregunta a GMGN. Con la clave gratis, unas 5 por segundo; vamos más despacio."""
    for intento in range(3):
        esperar("gmgn", 1.0)
        q = {"chain": "sol", "timestamp": int(time.time()), "client_id": str(uuid.uuid4()), **p}
        try:
            r = requests.get("https://openapi.gmgn.ai" + ruta, params=q, headers={"X-APIKEY": CLAVE}, timeout=20)
        except Exception:
            continue
        if r.status_code == 429:
            print("   (GMGN dice que vas muy rápido: espero 10 s)"); time.sleep(10); continue
        try:
            return r.json().get("data")
        except Exception:
            return None
    return None


def nodo(metodo, params):
    for intento in range(4):
        esperar("nodo", 1.1)
        try:
            d = requests.post(NODO, json={"jsonrpc": "2.0", "id": 1, "method": metodo, "params": params}, timeout=20).json()
        except Exception:
            continue
        if d.get("error"):
            if d["error"].get("code") in (429, -32429) or "rate" in str(d["error"]).lower():
                time.sleep(5); continue          # vas muy rápido: espera y repite
            return None                          # otro error: no insistir
        return d.get("result")
    return None


def num(x, d=0.0):
    try:
        return float(x)
    except Exception:
        return d


def dinero(x):
    s = "-" if x < 0 else ""
    x = abs(x)
    if x >= 1e6: return s + "%.2f M$" % (x / 1e6)
    if x >= 1e3: return s + "%.1f K$" % (x / 1e3)
    return s + "%.0f $" % x


def fecha(ts):
    return time.strftime("%d/%m/%Y", time.localtime(ts)) if ts else "?"


def duracion(s):
    if s is None: return "?"
    if s < 120: return "%d segundos" % s
    if s < 7200: return "%d minutos" % (s / 60)
    if s < 172800: return "%.1f horas" % (s / 3600)
    return "%.1f días" % (s / 86400)


def corto(a):
    return (a or "?")[:10] + "…"


def primer_pagador_en_cadena(w):
    """Comprobación en la propia cadena: quién le puso el primer SOL (si tiene menos de 5.000 movimientos)."""
    antes, ultima = None, None
    for _ in range(5):
        p = {"limit": 1000}
        if antes: p["before"] = antes
        s = nodo("getSignaturesForAddress", [w, p]) or []
        if not s: break
        ultima = s[-1]["signature"]; antes = ultima
        if len(s) < 1000: break
    else:
        return None, "más de 5.000 movimientos"
    if not ultima:
        return None, "el nodo no contesta"
    t = nodo("getTransaction", [ultima, {"encoding": "json", "maxSupportedTransactionVersion": 1}])
    if not t or not t.get("meta"):
        return None, "el nodo no contesta"
    m = t["meta"]; k = list(t["transaction"]["message"]["accountKeys"])
    k += (m.get("loadedAddresses") or {}).get("writable") or []
    k += (m.get("loadedAddresses") or {}).get("readonly") or []
    pierden = [(k[j], m["postBalances"][j] - m["preBalances"][j]) for j in range(min(len(k), len(m["preBalances"])))]
    pierden = [c for c in pierden if c[0] != w and c[1] < 0]
    return (min(pierden, key=lambda c: c[1])[0], None) if pierden else (None, "nadie le mandó SOL al empezar")


def dinero_en_cadena(tx, w, moneda):
    """Cuánto dinero (en la moneda con la que pagó: SOL, USDC...) entró o salió de verdad en esa operación,
    leído en la propia cadena. Positivo = le entró. Le sumamos la comisión de la red para comparar como GMGN."""
    t = nodo("getTransaction", [tx, {"encoding": "json", "maxSupportedTransactionVersion": 1}])
    if not t or not t.get("meta"):
        return None
    m = t["meta"]; k = list(t["transaction"]["message"]["accountKeys"])
    k += (m.get("loadedAddresses") or {}).get("writable") or []
    k += (m.get("loadedAddresses") or {}).get("readonly") or []

    def fichas(lista):
        return sum(num((b.get("uiTokenAmount") or {}).get("uiAmountString")) for b in lista or []
                   if b.get("owner") == w and b.get("mint") == moneda)
    cambio = fichas(m.get("postTokenBalances")) - fichas(m.get("preTokenBalances"))
    if moneda == WSOL and w in k:
        j = k.index(w)
        cambio += (m["postBalances"][j] - m["preBalances"][j] + (m.get("fee", 0) if j == 0 else 0)) / 1e9
    return cambio


def main(w):
    t0 = time.time()
    print("═" * 64)
    print(" BILLETERA: %s" % w)
    print("═" * 64)

    # ── 1. LA FICHA ───────────────────────────────────────────────────
    s = gmgn("/v1/user/wallet_stats", wallet_address=w, period="30d") or {}
    c = s.get("common") or {}
    ps = s.get("pnl_stat") or {}
    print("\n[1] LA FICHA (GMGN)")
    print("    existe desde: %s · saldo: %.2f SOL" % (fecha(c.get("created_at")), num(s.get("native_balance"))))
    print("    etiquetas: %s" % (", ".join(t for t in (c.get("tags") or []) if t) or "ninguna"))
    print("    tokens creados por ella: %s" % (c.get("created_token_count") or 0))

    # ── 2. CÓMO LE VA ─────────────────────────────────────────────────
    print("\n[2] CÓMO LE VA (últimos 30 días, según GMGN)")
    print("    ganado: %s sobre %s metidos" % (dinero(num(s.get("realized_profit"))), dinero(num(s.get("bought_cost")))))
    if ps.get("winrate") is not None:
        print("    tokens: %s · acierta en el %.0f%%" % (ps.get("token_num"), 100 * num(ps.get("winrate"))))
        print("    reparto: pierde más de la mitad %s · pierde algo %s · gana hasta x2 %s · x2 a x5 %s · más de x5 %s" % (
            ps.get("pnl_lt_nd5_num"), ps.get("pnl_nd5_0x_num"), ps.get("pnl_0x_2x_num"), ps.get("pnl_2x_5x_num"), ps.get("pnl_gt_5x_num")))

    # ── 3 y 4. SUS ÚLTIMAS OPERACIONES ────────────────────────────────
    ops, cursor = [], None
    for _ in range(PAGINAS):
        p = {"wallet_address": w, "limit": 50}
        if cursor: p["cursor"] = cursor
        d = gmgn("/v1/user/wallet_activity", **p) or {}
        ops += d.get("activities") or []
        cursor = d.get("next")
        if not cursor or not d.get("activities"):
            break
    tokens = {}
    for o in ops:
        tk = (o.get("token") or {}).get("address")
        if not tk or o.get("event_type") not in ("buy", "sell"):
            continue
        t = tokens.setdefault(tk, {"compra": 0.0, "venta": 0.0, "coste_vendido": 0.0, "ts": [], "n": 0, "simbolo": (o.get("token") or {}).get("symbol")})
        t["n"] += 1; t["ts"].append(o.get("timestamp") or 0)
        if o["event_type"] == "buy":
            t["compra"] += num(o.get("cost_usd"))
        else:
            t["venta"] += num(o.get("cost_usd")); t["coste_vendido"] += num(o.get("buy_cost_usd"))
    print("\n[3] CÓMO JUEGA (sus últimas %d operaciones)" % len(ops))
    if ops:
        aguantes = [max(t["ts"]) - min(t["ts"]) for t in tokens.values() if t["venta"] and t["compra"]]
        print("    %d tokens distintos · %.1f operaciones por token" % (len(tokens), len(ops) / max(1, len(tokens))))
        print("    aguante medio (de la primera compra a la última venta): %s" % (duracion(statistics.median(aguantes)) if aguantes else "?"))
        print("    según GMGN, en 30 días aguanta de media: %s" % duracion(num(ps.get("avg_holding_period"), None)))

    # ¿cuáles están muertos hoy? DexScreener, 30 de una vez
    vivos = {}
    cas = list(tokens)
    for i in range(0, len(cas), 30):
        try:
            pares = requests.get("https://api.dexscreener.com/latest/dex/tokens/" + ",".join(cas[i:i + 30]), timeout=20).json().get("pairs") or []
        except Exception:
            pares = []
        for p in pares:
            ca = (p.get("baseToken") or {}).get("address")
            vivos[ca] = max(vivos.get(ca, 0), num((p.get("liquidity") or {}).get("usd")))
        time.sleep(0.6)
    print("\n[4] SUS ÚLTIMOS TOKENS: ¿CUÁNTOS ESTÁN MUERTOS HOY?")
    muertos = [t for ca, t in tokens.items() if vivos.get(ca, 0) < MUERTO_LIQUIDEZ]
    gano_muertos = [t for t in muertos if t["venta"] > 0 and t["venta"] > t["coste_vendido"]]
    print("    %d de %d tokens están muertos (menos de %d $ de liquidez)" % (len(muertos), len(tokens), MUERTO_LIQUIDEZ))
    if muertos:
        print("    en %d de esos muertos salió GANANDO (%.0f%%)" % (len(gano_muertos), 100 * len(gano_muertos) / len(muertos)))
        print("    (vendió antes de que se hundieran)")

    # ── 4b. ¿CUADRA EL PNL DE GMGN CON LA CADENA? ─────────────────────
    print("\n[4b] ¿LO QUE DICE GMGN ES VERDAD? (sus últimas %d compras y ventas en SOL, una a una en la cadena)" % COMPROBAR)
    en_sol = [o for o in ops if o.get("event_type") in ("buy", "sell") and o.get("tx_hash")
              and ((o.get("quote_token") or {}).get("symbol") == "SOL" or o.get("quote_address") == WSOL)][:COMPROBAR]
    cuadran = mirar = 0; neto_gmgn = neto_cadena = 0.0; raras = []
    for o in en_sol:
        dice = num(o.get("quote_amount")) * (1 if o["event_type"] == "sell" else -1)
        real = dinero_en_cadena(o["tx_hash"], w, WSOL)
        if real is None:
            continue
        mirar += 1; neto_gmgn += dice; neto_cadena += real
        if abs(real - dice) <= max(0.05 * abs(dice), 0.002):
            cuadran += 1
        else:
            raras.append((o["event_type"], (o.get("token") or {}).get("symbol"), dice, real))
    if mirar:
        print("    en %d de %d la cadena da lo mismo que GMGN (con un 5%% de margen por comisiones y propinas)" % (cuadran, mirar))
        for tipo, sim, dice, real in raras[:5]:
            print("    no cuadra: %s de %s · GMGN dice %+.2f SOL · la cadena dice %+.2f SOL" % ("compra" if tipo == "buy" else "venta", sim, dice, real))
        if raras:
            print("    (suelen ser operaciones con varios saltos en una: GMGN las parte y la cadena las ve juntas)")
    elif not en_sol:
        print("    no tiene operaciones recientes pagadas en SOL")
    else:
        print("    el nodo no ha contestado")

    # ── 5. EL DINERO ──────────────────────────────────────────────────
    print("\n[5] DE DÓNDE LE VINO EL DINERO")
    print("    GMGN dice: %s le mandó %s SOL el %s" % (corto(c.get("fund_from_address")), ("%.2f" % num(c.get("fund_amount"))) if c.get("fund_amount") else "?", fecha(c.get("fund_from_ts"))))
    pag, motivo = primer_pagador_en_cadena(w)
    if pag:
        print("    la cadena dice: %s %s" % (corto(pag), "· CUADRA" if pag == c.get("fund_from_address") else "· NO CUADRA, mira las dos"))
    else:
        print("    en la cadena no se comprueba: %s" % motivo)

    # ── 6. EL VEREDICTO ───────────────────────────────────────────────
    v = []
    if len(tokens) >= 10 and len(muertos) >= 5:
        q = len(gano_muertos) / len(muertos)
        if q >= 0.5: v.append("TUMBADORA: gana en la mayoría de los que se mueren")
        elif q >= 0.35: v.append("SOSPECHOSA: gana en muchos de los que se mueren")
    if ops and len(ops) / max(1, len(tokens)) >= 100: v.append("BOT: demasiadas operaciones por token")
    if ps.get("avg_holding_period") is not None and num(ps.get("avg_holding_period")) < 60: v.append("BOT: aguanta menos de un minuto")
    if not v and len(tokens) >= 10 and len(muertos) / len(tokens) >= 0.8 and len(gano_muertos) / max(1, len(muertos)) <= 0.15:
        v.append("VÍCTIMA: casi todo lo que toca se muere y no sale a tiempo")
    print("\n[6] VEREDICTO: %s" % (" · ".join(v) if v else "normal (con lo que se ve aquí)"))

    print("\n" + "─" * 64)
    print(" Hecho en %.0f s. No es consejo financiero." % (time.time() - t0))
    print("─" * 64)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 billetera.py <DIRECCION_DE_LA_BILLETERA>"); sys.exit(1)
    main(sys.argv[1].strip())
