"""Pasos 4, 5 y 6: empareja el historial de la tienda con el banco,
por importe y con margen de días. Lo que no casa, es una pregunta.

Uso:  python cruzar.py        (margen del .env, 5 días si no pones nada)
      python cruzar.py 0      (sin margen: verás que casi nada cuadra)
"""
import csv
import sys
from datetime import date

from comun import ajuste, banco, eur, palabras, ruta


def pedidos():
    with open(ruta("PEDIDOS", "pedidos_tienda_ejemplo.csv"), encoding="utf-8", newline="") as f:
        lista = list(csv.DictReader(f, delimiter=";"))
    for p in lista:
        p["fecha"] = date.fromisoformat(p["fecha"])
        p["importe"] = round(float(p["importe"]), 2)
        p["tipo"] = (p.get("tipo") or "pedido").strip().lower()
    return lista


def main(margen):
    tienda = palabras("PALABRAS_TIENDA", "TIENDA ONLINE")
    cargos = [m for m in banco() if any(p in m["concepto"] for p in tienda)]
    usados, dudas, bien = set(), [], 0
    print(f"Tienda <-> banco, por importe y con margen de {margen} días:")
    for p in pedidos():
        # Un pedido es un cargo (importe negativo en el banco); un reembolso, un ingreso.
        buscado = -p["importe"] if p["tipo"] == "pedido" else p["importe"]
        candidatos = [i for i, m in enumerate(cargos)
                      if i not in usados and m["importe"] == buscado
                      and 0 <= (m["fecha"] - p["fecha"]).days <= margen]
        if not candidatos:
            dudas.append(p)
            continue
        i = min(candidatos, key=lambda i: cargos[i]["fecha"])
        usados.add(i)
        bien += 1
        m = cargos[i]
        dias = (m["fecha"] - p["fecha"]).days
        print(f"   {p['pedido']} {p['tipo']:<9} {p['fecha']} {eur(p['importe']):>8}  <->  banco {m['fecha']}  (+{dias} días)")
    print(f"Emparejados: {bien} de {bien + len(dudas)}")

    for p in dudas:
        print(f"PREGUNTA: {p['pedido']} ({p['tipo']}) del {p['fecha']}, {eur(p['importe'])} €, no está en el banco. "
              "¿Otra tarjeta, saldo regalo, otra persona, o se cobra más tarde?")
    sueltos = [m for i, m in enumerate(cargos) if i not in usados]
    for m in sueltos:
        print(f"PREGUNTA: el banco tiene {eur(m['importe'])} € el {m['fecha']} ({m['concepto']}) y no hay pedido. "
              "¿Falta en el historial que descargaste?")

    gastado = -sum(m["importe"] for m in cargos)
    pedido = sum(p["importe"] if p["tipo"] == "pedido" else -p["importe"] for p in pedidos())
    print(f"\nPedidos menos reembolsos: {eur(pedido)} €   Banco (cargos menos devoluciones): {eur(gastado)} €")


if __name__ == "__main__":
    margen = int(sys.argv[1]) if len(sys.argv) > 1 else int(ajuste("MARGEN_DIAS", "5"))
    main(margen)
