"""Paso 3: compara dos nóminas apuntadas y busca en el banco el ingreso de cada una.

Uso:  python comparar.py 2026-09 2026-10
"""
import csv
import sys

from comun import CARPETA, banco, eur


def main(a, b):
    if not (CARPETA / "apuntes_nominas.csv").exists():
        sys.exit("Aún no hay nóminas apuntadas. Primero: python leer_nomina.py")
    with open(CARPETA / "apuntes_nominas.csv", encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f, delimiter=";"))
    n = {}
    for r in filas:
        n.setdefault(r["mes"], {})[r["concepto"]] = round(float(r["importe"]), 2)
    for mes in (a, b):
        if mes not in n:
            sys.exit(f"El mes {mes} no está apuntado. Pasa antes su nómina por leer_nomina.py.")

    print(f"Qué ha cambiado de {a} a {b}:")
    cambios = 0
    for c in sorted(set(n[a]) | set(n[b]), key=lambda c: (c == "LÍQUIDO", c)):
        x, y = n[a].get(c), n[b].get(c)
        if x is None:
            print(f"   NUEVO    {c:<24} {eur(y):>10}")
        elif y is None:
            print(f"   QUITADO  {c:<24} {eur(x):>10}")
        elif x != y:
            print(f"   CAMBIA   {c:<24} {eur(x):>10} -> {eur(y)}")
        else:
            continue
        cambios += 1
    if not cambios:
        print("   nada")

    print("\nEl líquido, en el banco:")
    movs = banco()
    for mes in (a, b):
        liq = n[mes]["LÍQUIDO"]
        ingresos = [m for m in movs if m["importe"] > 0 and m["fecha"].isoformat()[:7] == mes]
        igual = [m for m in ingresos if m["importe"] == liq]
        if igual:
            m = igual[0]
            print(f"   {mes}: líquido {eur(liq)} -> en el banco el {m['fecha']} ({m['concepto']})  OK")
        else:
            otros = ", ".join(f"{eur(m['importe'])} el {m['fecha']}" for m in ingresos) or "ninguno"
            print(f"   {mes}: líquido {eur(liq)} -> NO está ese importe. Ingresos del mes: {otros}")
            print("            PREGUNTA: ¿te la pagaron otro mes, en otra cuenta, o el PDF está mal leído?")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Uso: python comparar.py MES_ANTERIOR MES_NUEVO   (por ejemplo 2026-09 2026-10)")
    main(sys.argv[1], sys.argv[2])
