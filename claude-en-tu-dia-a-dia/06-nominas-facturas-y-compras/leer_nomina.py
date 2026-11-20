"""Paso 1 y 2: lee tus nóminas en PDF y las apunta SOLO si cuadran al céntimo.

Uso:  python leer_nomina.py                 (todas las de la carpeta nominas/)
      python leer_nomina.py una.pdf otra.pdf
"""
import csv
import re
import sys
from pathlib import Path

from pypdf import PdfReader

from comun import CARPETA, eur

APUNTES = CARPETA / "apuntes_nominas.csv"
IMPORTE = r"(-?\d{1,3}(?:\.\d{3})*,\d{2})"


def num(s):
    return round(float(s.replace(".", "").replace(",", ".")), 2)


def leer(pdf):
    """Devuelve (mes, conceptos, totales) leyendo el texto del PDF."""
    # "layout" respeta las columnas: cada concepto, en la misma línea que su importe
    texto = "\n".join(p.extract_text(extraction_mode="layout") or "" for p in PdfReader(pdf).pages)
    mes = re.search(r"(20\d\d-\d\d)", texto) or re.search(r"(20\d\d-\d\d)", Path(pdf).name)
    seccion, conceptos, tot = None, {"devengos": [], "deducciones": []}, {}
    for linea in texto.splitlines():
        linea = linea.strip()
        m = re.match(r"(.+?)\s+" + IMPORTE + r"$", linea)
        mayus = linea.upper()
        if mayus.startswith("DEVENGOS"):
            seccion = "devengos"
        elif mayus.startswith("DEDUCCIONES"):
            seccion = "deducciones"
        elif m and mayus.startswith("TOTAL DEVENGADO"):
            tot["bruto"] = num(m.group(2))
        elif m and mayus.startswith("TOTAL A DEDUCIR"):
            tot["descuentos"] = num(m.group(2))
        elif m and mayus.startswith(("LÍQUIDO", "LIQUIDO")):
            tot["liquido"] = num(m.group(2))
        elif m and seccion:
            conceptos[seccion].append((m.group(1).strip(), num(m.group(2))))
    return (mes.group(1) if mes else None), conceptos, tot


def meses_apuntados():
    if not APUNTES.exists():
        return set()
    with open(APUNTES, encoding="utf-8", newline="") as f:
        return {r["mes"] for r in csv.DictReader(f, delimiter=";")}


def apuntar(mes, conceptos, liquido):
    nuevo = not APUNTES.exists()
    with open(APUNTES, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        if nuevo:
            w.writerow(["mes", "tipo", "concepto", "importe"])
        for tipo in ("devengos", "deducciones"):
            for c, v in conceptos[tipo]:
                w.writerow([mes, tipo, c, f"{v:.2f}"])
        w.writerow([mes, "liquido", "LÍQUIDO", f"{liquido:.2f}"])


def main(pdfs):
    ya = meses_apuntados()
    for pdf in pdfs:
        mes, c, t = leer(pdf)
        print(f"\n{Path(pdf).name}  (mes {mes or '?'})")
        if not mes or set(t) != {"bruto", "descuentos", "liquido"}:
            print("   -> NO encuentro el mes o los totales: no se apunta. Revisa la lectura.")
            continue
        bruto = round(sum(v for _, v in c["devengos"]), 2)
        desc = round(sum(v for _, v in c["deducciones"]), 2)
        pruebas = [
            ("conceptos", bruto, "bruto", t["bruto"]),
            ("descuentos", desc, "total descontado", t["descuentos"]),
            ("bruto - descuentos", round(bruto - desc, 2), "líquido", t["liquido"]),
        ]
        ok = True
        for nombre, calc, que, pdf_v in pruebas:
            bien = calc == pdf_v
            ok &= bien
            print(f"   {nombre:<19} {eur(calc):>10}  = {que} {eur(pdf_v):>10}   {'OK' if bien else 'NO CUADRA'}")
        if not ok:
            print("   -> NO cuadra al céntimo: no se apunta. Ha leído mal algún número.")
        elif mes in ya:
            print("   -> cuadra, pero ese mes ya estaba apuntado: no lo repito.")
        else:
            apuntar(mes, c, t["liquido"])
            ya.add(mes)
            print("   -> cuadra al céntimo: APUNTADA en apuntes_nominas.csv")


if __name__ == "__main__":
    lista = sys.argv[1:] or sorted(str(p) for p in (CARPETA / "nominas").glob("*.pdf"))
    if not lista:
        sys.exit("No hay PDFs. Pon tus nóminas en la carpeta nominas/.")
    main(lista)
