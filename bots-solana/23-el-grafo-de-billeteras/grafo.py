#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
El grafo de billeteras: el mapa de quién pagó a quién dentro de un token, dibujado.
Canal de YouTube: Profesor Diógenes · sección "Bots de Solana", vídeo 23.

    python3 grafo.py <contrato>          (o con el bot: python3 bot.py, que te manda la imagen)

Qué hace:
  1. Pide a GMGN los 100 mayores holders del token (vale la clave pública de pruebas). GMGN dice, de cada
     uno, quién le puso el primer SOL.
  2. Junta a los holders que tienen el mismo pagador: eso es un GRUPO. Si el pagador es un exchange con
     nombre, no cuenta (paga a miles de personas).
  3. Un paso más atrás, con el nodo público de Solana: si a dos pagadores los pagó la misma billetera,
     sus grupos se juntan en uno.
  4. Lo dibuja: cada holder es un círculo (más grande cuanto más tiene), cada pagador un rombo, y una
     línea del pagador a cada billetera que pagó. Arriba los grupos, cada uno de un color; abajo, en gris,
     los holders que van por su cuenta.

Cómo se lee: muchos círculos grises sueltos = cada uno ha venido por su lado (o han pasado por un exchange
antes de entrar). Un racimo de color con círculos gordos = un bolsillo con mucho token.

Lo que NO ve: los grupos que se pagan a través de un exchange. Un mapa limpio no es un token limpio.
Esto NO es consejo financiero. Es una herramienta para mirar.
"""
import os, sys, time, uuid
from collections import defaultdict
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
FILTRA = os.environ.get("SIN_FILTRO", "") != "1"        # SIN_FILTRO=1 dibuja el mapa ingenuo, creyéndose a todos los pagadores
ATRAS = int(os.environ.get("PAGADORES_ATRAS", "8"))     # a cuántos pagadores se les busca su propio pagador
AQUI = os.path.dirname(os.path.abspath(__file__))
COLORES = ["#e7b24a", "#5ad1a4", "#f0707a", "#6aa9ff", "#c58bf2", "#ff9f5a", "#7fd8e6", "#d4e157"]
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
                time.sleep(10); q.update(timestamp=int(time.time()), client_id=str(uuid.uuid4())); continue
            d = r.json()
            if str(d.get("code")) not in ("0", "None"):
                return None
            return d.get("data")
        except Exception:
            time.sleep(2)
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


def primer_pagador(w):
    """Quién le puso el primer SOL a una billetera (nodo público). Si tiene más de 2.000 movimientos, no se sigue."""
    antes, ultima = None, None
    for _ in range(2):
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
        return None
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


def corto(a):
    return a[:4] + "…" + a[-3:]


def num(x):
    try:
        return float(x or 0)
    except Exception:
        return 0.0


# ───────────────────────────────────────────────── el análisis
def analiza(ca, atras=None):
    """Devuelve el mapa: holders, quién pagó a cada uno y los grupos. No dibuja nada."""
    atras = ATRAS if atras is None else atras
    info = gmgn("/v1/token/info", peso=1, chain="sol", address=ca) or {}
    datos = gmgn("/v1/market/token_top_holders", chain="sol", address=ca, limit=100)
    H = (datos.get("list") if isinstance(datos, dict) else datos) or []
    personas = [h for h in H if not (h.get("exchange") or h.get("addr_type") not in (0, None) or "pool" in " ".join(h.get("tags") or []).lower())]
    holders, paga, exchange = {}, {}, {}
    for h in personas:
        a = h.get("address")
        if not a:
            continue
        holders[a] = 100 * num(h.get("amount_percentage"))
        nt = h.get("native_transfer") or {}
        p = nt.get("from_address") or nt.get("address")
        if p and p != a:
            paga[a] = p
            if nt.get("name"):
                exchange[p] = nt["name"]
    hijos = defaultdict(list)
    for a, p in paga.items():
        if p not in exchange:
            hijos[p].append(a)
    ingenuo = sum(holders[x] for p in hijos if len(hijos[p]) >= 2 for x in hijos[p])    # lo que saldría creyéndose a todos
    # un pagador con miles de movimientos es un repartidor o un exchange sin nombre: paga a medio mundo y NO hace grupo
    repartidor = set()
    for p in sorted([p for p in hijos if len(hijos[p]) >= 2], key=lambda p: -len(hijos[p]))[:15] if FILTRA else []:
        if len(nodo("getSignaturesForAddress", [p, {"limit": 1000}]) or []) >= 1000:
            repartidor.add(p)
    for p in repartidor:
        exchange[p] = "repartidor"; hijos.pop(p)
    # un paso más atrás: pagadores con 2 o más holders, y de esos, los que más token mueven
    raiz = {p: p for p in hijos}
    candidatos = sorted([p for p in hijos if len(hijos[p]) >= 2], key=lambda p: -sum(holders[a] for a in hijos[p]))[:atras]
    abuelos = {}
    for p in candidatos:
        g = primer_pagador(p)
        if g and g not in exchange:
            abuelos[p] = g
    por_abuelo = defaultdict(list)
    for p, g in abuelos.items():
        por_abuelo[g].append(p)
    for g, ps in por_abuelo.items():
        if len(ps) >= 2 or g in hijos:                    # el mismo abuelo junta dos grupos (o el abuelo es otro pagador)
            for p in ps:
                raiz[p] = raiz.get(g, g)
    grupos = defaultdict(list)
    for p, hs in hijos.items():
        grupos[raiz[p]] += hs
    grupos = {r: sorted(hs, key=lambda a: -holders[a]) for r, hs in grupos.items() if len(hs) >= 2}
    orden = sorted(grupos, key=lambda r: -sum(holders[a] for a in grupos[r]))
    return {"ca": ca, "simbolo": info.get("symbol") or ca[:6], "holders": holders, "paga": paga, "exchange": exchange,
            "abuelos": {p: g for p, g in abuelos.items() if raiz[p] != p}, "grupos": [(r, grupos[r]) for r in orden],
            "pct_grupos": sum(holders[a] for r in grupos for a in grupos[r]), "pct_top": sum(holders.values()), "pct_ingenuo": ingenuo,
            "repartidores": {p: [a for a, q in paga.items() if q == p] for p in repartidor}}


def dibuja(m, salida):
    """Pinta el mapa en una imagen: arriba los grupos (cada uno alrededor de quien lo pagó), abajo los sueltos."""
    import math
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(10.8, 10.8), dpi=100, facecolor="#14110d")
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_facecolor("#14110d"); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    tam = lambda a: 60 + 380 * min(m["holders"][a], 6)                 # el círculo crece con lo que tiene
    grupos = m["grupos"][:6]
    en_grupo = {a for r, hs in grupos for a in hs}
    columnas = 3 if len(grupos) > 2 else max(1, len(grupos))
    filas = math.ceil(len(grupos) / columnas) if grupos else 0
    alto_grupos = 0.54 if filas == 2 else (0.34 if filas == 1 else 0.0)
    for i, (raiz, hs) in enumerate(grupos):
        col = COLORES[i % len(COLORES)]
        cx = (i % columnas + 0.5) / columnas
        cy = 0.86 - alto_grupos * ((i // columnas) + 0.5) / max(1, filas)
        radio = min(0.115, 0.42 / columnas) * (0.75 if filas == 2 else 1)
        pagadores = sorted({m["paga"][a] for a in hs})
        if pagadores == [raiz]:                                            # un pagador y sus holders alrededor
            sitio = {raiz: (cx, cy)}
            for k, a in enumerate(hs):
                ang = 2 * math.pi * k / len(hs) + math.pi / 2
                sitio[a] = (cx + radio * math.cos(ang), cy + radio * math.sin(ang)); ax.plot([cx, sitio[a][0]], [cy, sitio[a][1]], color=col, lw=1.4, alpha=0.7, zorder=1)
        else:                                                              # el de arriba pagó a varios pagadores, y cada uno a los suyos
            sitio = {raiz: (cx, cy)}; k = 0
            for p in pagadores:
                suyos = [a for a in hs if m["paga"][a] == p]
                medio = 2 * math.pi * (k + len(suyos) / 2 - 0.5) / len(hs) + math.pi / 2
                if p != raiz:
                    sitio[p] = (cx + 0.45 * radio * math.cos(medio), cy + 0.45 * radio * math.sin(medio))
                    ax.plot([cx, sitio[p][0]], [cy, sitio[p][1]], color=col, lw=1.4, alpha=0.7, zorder=1)
                for a in suyos:
                    ang = 2 * math.pi * k / len(hs) + math.pi / 2; k += 1
                    sitio[a] = (cx + radio * math.cos(ang), cy + radio * math.sin(ang))
                    ax.plot([sitio[p][0], sitio[a][0]], [sitio[p][1], sitio[a][1]], color=col, lw=1.4, alpha=0.7, zorder=1)
        for n, (x, y) in sitio.items():
            if n in m["holders"] and n in hs:
                ax.scatter([x], [y], s=tam(n), color=col, edgecolors="#14110d", linewidths=1.2, zorder=3)
            else:
                ax.scatter([x], [y], s=170, color=col, marker="D", edgecolors="#ffffff", linewidths=1.5, zorder=4)
        ax.text(cx, cy - radio - 0.035, "GRUPO %d · %d billeteras · %.1f %% del token" % (i + 1, len(hs), sum(m["holders"][a] for a in hs)),
                color=col, fontsize=11, ha="center", va="top", fontweight="bold")
        ax.text(cx, cy - radio - 0.058, "las pagó %s" % corto(raiz), color="#9a8f7c", fontsize=9.5, ha="center", va="top")
    # los sueltos, abajo, de mayor a menor
    sueltos = sorted([a for a in m["holders"] if a not in en_grupo], key=lambda a: -m["holders"][a])
    techo = 0.86 - alto_grupos - (0.10 if grupos else 0.0)
    por_fila = 14; nf = math.ceil(len(sueltos) / por_fila) or 1
    paso = min(0.058, (techo - 0.06) / nf)
    ax.text(0.04, techo + 0.012, "%d holders sin grupo: van por su cuenta, o vienen de un exchange (el mayor tiene el %.1f %%)" % (len(sueltos), m["holders"][sueltos[0]] if sueltos else 0), color="#9a8f7c", fontsize=11, va="bottom")
    for k, a in enumerate(sueltos):
        x = 0.06 + (k % por_fila) * (0.88 / (por_fila - 1)); y = techo - 0.03 - (k // por_fila) * paso
        ax.scatter([x], [y], s=tam(a) * 0.8, color="#6f6a60", edgecolors="#14110d", linewidths=1.0, zorder=3)
    fig.text(0.04, 0.955, "%s · quién pagó a quién" % m["simbolo"], color="#e7b24a", fontsize=24, fontweight="bold")
    resumen = "%d holders mirados (%.1f %% del token) · %d grupo%s · %.1f %% del token en grupos" % (
        len(m["holders"]), m["pct_top"], len(m["grupos"]), "" if len(m["grupos"]) == 1 else "s", m["pct_grupos"])
    fig.text(0.04, 0.922, resumen, color="#e9dfcc", fontsize=13)
    fig.text(0.04, 0.898, "círculo = holder (más grande, más token) · rombo = quien le puso el primer SOL", color="#9a8f7c", fontsize=10.5)
    fig.savefig(salida, facecolor=fig.get_facecolor()); plt.close(fig)
    return salida


def main(ca):
    t0 = time.time()
    m = analiza(ca)
    if not m["holders"]:
        print("GMGN no da holders de este contrato."); return None
    print("EL MAPA DE %s" % m["simbolo"])
    print("%s\n" % ca)
    print("%d holders mirados: tienen el %.1f %% del token." % (len(m["holders"]), m["pct_top"]))
    if not m["grupos"]:
        print("No sale ningún grupo: a cada holder lo pagó una billetera distinta, o vienen de un exchange.")
    for i, (r, hs) in enumerate(m["grupos"], 1):
        print("\nGRUPO %d · %d billeteras · %.2f %% del token" % (i, len(hs), sum(m["holders"][a] for a in hs)))
        print("   las pagó %s%s" % (r, "  (a través de pagadores intermedios)" if any(m["paga"].get(a) != r for a in hs) else ""))
        for a in hs[:6]:
            print("     %6.2f %%  %s" % (m["holders"][a], a))
        if len(hs) > 6:
            print("     … y %d más" % (len(hs) - 6))
    if m["grupos"]:
        print("\nEn total, el %.1f %% del token está en billeteras que comparten pagador." % m["pct_grupos"])
    de_exchange = sum(1 for a, p in m["paga"].items() if p in m["exchange"])
    print("%d de los %d holders vienen directamente de un exchange o de un repartidor: ahí no se puede seguir el hilo." % (de_exchange, len(m["holders"])))
    for p, hs in m["repartidores"].items():
        print("   ojo: %s pagó a %d de estos holders, pero tiene miles de movimientos. Parece un grupo y no lo es." % (corto(p), len(hs)))
    print("\nUn mapa limpio no es un token limpio: quien pasa por un exchange no sale en el dibujo.")
    print("(%d s · GMGN + nodo público de Solana · no es consejo financiero)" % (time.time() - t0))
    return dibuja(m, os.path.join(AQUI, "grafo_%s.png" % ca[:8]))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 grafo.py <contrato>"); sys.exit(1)
    f = main(sys.argv[1])
    if f:
        print("Imagen: %s" % f)
