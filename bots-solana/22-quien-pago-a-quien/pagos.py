#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quién pagó a quién: sigue el dinero de una billetera de Solana hacia atrás y hacia los lados.
Canal de YouTube: Profesor Diógenes · sección "Bots de Solana", vídeo 22.

    python3 pagos.py <billetera>          (o con el bot: python3 bot.py)

Qué mira, todo en el nodo público de Solana (gratis y sin clave):
  1. HACIA ATRÁS: quién le puso el primer SOL a esta billetera, quién se lo puso a esa, y así hasta 6 saltos.
     Se para cuando llega a una billetera con miles de movimientos: un exchange o un repartidor.
     Ahí se pierde el rastro: de un exchange sale el dinero de miles de personas.
  2. HERMANAS: a quién más ha mandado SOL su pagador hace poco. Si el pagador es una persona y no un
     exchange, esas billeteras son muy probablemente del mismo bolsillo.
  3. HIJAS: a quién ha mandado SOL esta billetera, y si esas billeteras estaban recién hechas.

Lo que NO ve: el dinero que pasa por un exchange o por un mezclador, y las billeteras que se pagan con
tokens en vez de con SOL. Que dos billeteras salgan del mismo pagador NO prueba que sean de la misma
persona: es una pista.

Esto NO es consejo financiero. Es una herramienta para mirar.
"""
import os, sys, time, datetime
import requests


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
NODO = os.environ.get("SOLANA_RPC", "https://api.mainnet-beta.solana.com")
SALTOS = int(os.environ.get("SALTOS", "6"))                 # cuántos pasos hacia atrás como mucho
OPERACIONES = int(os.environ.get("OPERACIONES", "30"))      # cuántas operaciones recientes se leen de cada billetera
MINIMO = float(os.environ.get("MINIMO_SOL", "0.01"))        # envíos más pequeños que esto no cuentan
MAQUINA = 3000                                              # con más movimientos que esto, es un exchange o un repartidor
LAM = 1e9
_ultima = [0.0]


def nodo(metodo, params):
    """El nodo público de Solana: más o menos una pregunta por segundo por IP."""
    for intento in range(4):
        espera = 1.1 - (time.time() - _ultima[0])
        if espera > 0:
            time.sleep(espera)
        _ultima[0] = time.time()
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


def corto(a):
    return a[:6] + "…" + a[-4:]


def fecha(ts):
    return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%d-%m-%Y") if ts else "?"


def primer_pago(w):
    """Quién le puso el primer SOL a una billetera, cuánto y cuándo. Devuelve también cuántos movimientos tiene.
    Si tiene más de 3.000, no se sigue: es una máquina."""
    antes, ultima, total = None, None, 0
    for _ in range(MAQUINA // 1000):
        p = {"limit": 1000}
        if antes:
            p["before"] = antes
        s = nodo("getSignaturesForAddress", [w, p]) or []
        total += len(s)
        if not s:
            break
        ultima = s[-1]; antes = ultima["signature"]
        if len(s) < 1000:
            break
    else:
        return None, 0, None, total, True
    if not ultima:
        return None, 0, None, total, False
    t = nodo("getTransaction", [ultima["signature"], {"encoding": "json", "maxSupportedTransactionVersion": 1}])
    if not t or not t.get("meta"):
        return None, 0, ultima.get("blockTime"), total, False
    m = t["meta"]; k = list(t["transaction"]["message"]["accountKeys"])
    k += ((m.get("loadedAddresses") or {}).get("writable") or []) + ((m.get("loadedAddresses") or {}).get("readonly") or [])
    pierden = [(k[j], m["postBalances"][j] - m["preBalances"][j]) for j in range(min(len(k), len(m["preBalances"])))
               if k[j] != w and m["postBalances"][j] < m["preBalances"][j]]
    if not pierden:
        return None, 0, t.get("blockTime"), total, False
    quien = min(pierden, key=lambda c: c[1])[0]
    recibido = next((m["postBalances"][j] - m["preBalances"][j] for j in range(min(len(k), len(m["preBalances"]))) if k[j] == w), 0)
    return quien, recibido / LAM, t.get("blockTime"), total, False


def envios(w, limite):
    """A quién ha mandado SOL esta billetera en sus últimas operaciones (solo envíos directos)."""
    salen = {}
    for s in nodo("getSignaturesForAddress", [w, {"limit": limite}]) or []:
        if s.get("err"):
            continue
        t = nodo("getTransaction", [s["signature"], {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 1}])
        if not t or not t.get("meta"):
            continue
        for i in ((t.get("transaction") or {}).get("message") or {}).get("instructions") or []:
            p = i.get("parsed") if isinstance(i, dict) else None
            if not isinstance(p, dict) or i.get("program") != "system" or p.get("type") != "transfer":
                continue
            inf = p.get("info") or {}
            if inf.get("source") == w and int(inf.get("lamports") or 0) >= MINIMO * LAM:
                d = salen.setdefault(inf["destination"], [0.0, t.get("blockTime")])
                d[0] += int(inf["lamports"]) / LAM
    return salen


def movimientos(w):
    return len(nodo("getSignaturesForAddress", [w, {"limit": 1000}]) or [])


def main(w):
    t0 = time.time()
    print("QUIÉN PAGÓ A QUIÉN · %s" % w)
    print()
    # ── 1. hacia atrás
    print("[1] HACIA ATRÁS: de dónde le vino el primer SOL")
    cadena, actual, padre, final = [w], w, None, None
    for salto in range(1, SALTOS + 1):
        quien, sol, cuando, total, maquina = primer_pago(actual)
        if maquina:
            final = "    ⛔ %s tiene más de %d movimientos: es un exchange o un repartidor.\n       Aquí se pierde el rastro: de ahí sale el dinero de miles de personas." % (corto(actual), MAQUINA)
            break
        if not quien:
            final = "    (no encuentro quién pagó a %s)" % corto(actual)
            break
        if quien in cadena:
            final = "    🔁 %s ya había salido: el dinero da vueltas entre las mismas billeteras." % corto(quien)
            break
        cuanto = "le puso %.3f SOL" % sol if sol >= 0.001 else "le pagó su primera operación (sin mandarle SOL)"
        print("    %d. a %s (%d movimientos) %s\n       %s  el %s" % (salto, corto(actual), total, cuanto, quien, fecha(cuando)))
        if salto == 1:
            padre = quien
        cadena.append(quien); actual = quien
    else:
        final = "    … y sigue. Paro a los %d saltos (se cambia con SALTOS en el .env)." % SALTOS
    print(final)
    print()
    # ── 2. hermanas
    print("[2] HERMANAS: a quién más ha pagado su pagador")
    if not padre:
        print("    (sin pagador conocido, no hay hermanas que buscar)")
    elif movimientos(padre) >= 1000:
        print("    Su pagador %s tiene más de 1.000 movimientos: paga a demasiada gente para sacar nada." % corto(padre))
    else:
        h = {d: v for d, v in envios(padre, OPERACIONES).items() if d != w}
        if not h:
            print("    En sus últimas %d operaciones, su pagador no ha mandado SOL a nadie más." % OPERACIONES)
        else:
            print("    Su pagador %s ha mandado SOL a %s (últimas %d operaciones):" % (corto(padre), "otra billetera" if len(h) == 1 else "otras %d billeteras" % len(h), OPERACIONES))
            for d, (sol, cuando) in sorted(h.items(), key=lambda kv: -kv[1][0])[:10]:
                print("       %8.3f SOL  %s  el %s" % (sol, d, fecha(cuando)))
            print("    ⚠️  Mismo pagador = misma pista. Pégame cualquiera de ellas y sigo el hilo.")
    print()
    # ── 3. hijas
    print("[3] HIJAS: a quién ha pagado esta billetera")
    hijas = envios(w, OPERACIONES)
    if not hijas:
        print("    En sus últimas %d operaciones no ha mandado SOL a nadie." % OPERACIONES)
    else:
        nuevas = 0
        for d, (sol, cuando) in sorted(hijas.items(), key=lambda kv: -kv[1][0])[:8]:
            n = movimientos(d)
            que = "recién hecha (%d movimientos)" % n if n <= 5 else ("%d movimientos" % n if n < 1000 else "más de 1.000 movimientos")
            nuevas += n <= 5
            print("       %8.3f SOL  %s  %s" % (sol, d, que))
        if nuevas >= 2:
            print("    ⚠️  Ha pagado a %d billeteras recién hechas: está repartiendo el dinero en billeteras nuevas." % nuevas)
    print()
    print("Mismo pagador no prueba mismo dueño: es una pista, no una sentencia.")
    print("(%d s · nodo público de Solana · no es consejo financiero)" % (time.time() - t0))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 pagos.py <billetera>"); sys.exit(1)
    main(sys.argv[1])
