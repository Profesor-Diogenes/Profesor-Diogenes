"""Lee el archivo de movimientos, quita repetidos, pone categorías y suma
dejando fuera los traspasos entre tus cuentas.

Uso:  python finanzas.py            (usa el archivo de MOVIMIENTOS del .env)
      python finanzas.py otro.csv
"""
import csv
import os
import sys
from pathlib import Path

CARPETA = Path(__file__).resolve().parent
TRASPASOS = "traspasos"
OTROS = "otros"


def cargar(ruta):
    """Devuelve la lista de movimientos sin repetidos.
    Repetido = misma referencia del banco; si no hay referencia,
    misma fecha, importe y concepto."""
    vistos, lista = set(), []
    with open(ruta, encoding="utf-8", newline="") as f:
        for m in csv.DictReader(f, delimiter=";"):
            ref = (m.get("referencia") or "").strip()
            clave = ref or (m["fecha"], m["importe"], m["concepto"])
            if clave in vistos:
                continue
            vistos.add(clave)
            m["importe"] = float(m["importe"])
            lista.append(m)
    return lista


def reglas(ruta=CARPETA / "categorias.txt"):
    """Lee categorias.txt -> {categoría: [PALABRAS]}"""
    r = {}
    with open(ruta, encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea or linea.startswith("#") or ":" not in linea:
                continue
            cat, palabras = linea.split(":", 1)
            r[cat.strip()] = [p.strip().upper() for p in palabras.split(",") if p.strip()]
    return r


def categoria(concepto, r):
    concepto = concepto.upper()
    for cat, palabras in r.items():
        if any(p in concepto for p in palabras):
            return cat
    return OTROS  # nada de inventar categorías


def eur(x):
    return f"{x:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def mes_de(m):
    return m["fecha"][:7]  # "2026-11"


def ultimo_mes(lista):
    return max(mes_de(m) for m in lista)


def gastos_por_categoria(lista, r, mes=None):
    """Gastos (en positivo) por categoría, sin traspasos."""
    tot = {}
    for m in lista:
        if mes and mes_de(m) != mes:
            continue
        c = categoria(m["concepto"], r)
        if c == TRASPASOS or m["importe"] >= 0:
            continue
        tot[c] = tot.get(c, 0) - m["importe"]
    return dict(sorted(tot.items(), key=lambda x: -x[1]))


def totales(lista, r, mes=None, con_traspasos=False):
    """(gastos, ingresos) del mes. Por defecto, sin traspasos."""
    g = i = 0.0
    for m in lista:
        if mes and mes_de(m) != mes:
            continue
        if not con_traspasos and categoria(m["concepto"], r) == TRASPASOS:
            continue
        if m["importe"] < 0:
            g -= m["importe"]
        else:
            i += m["importe"]
    return g, i


def ruta_movimientos():
    try:
        from dotenv import load_dotenv
        load_dotenv(CARPETA / ".env")
    except ImportError:
        pass
    ruta = Path(os.getenv("MOVIMIENTOS", "movimientos_ejemplo.csv"))
    return ruta if ruta.is_absolute() else CARPETA / ruta


if __name__ == "__main__":
    ruta = Path(sys.argv[1]) if len(sys.argv) > 1 else ruta_movimientos()
    with open(ruta, encoding="utf-8") as f:
        filas = sum(1 for _ in f) - 1
    lista, r = cargar(ruta), reglas()
    print(f"Archivo: {ruta.name}")
    print(f"Leídas {filas} filas, {len(lista)} tras quitar repetidos\n")
    for m in lista:
        print(f"{m['fecha']}  {m['concepto'][:30]:<30} {eur(m['importe']):>12}  -> {categoria(m['concepto'], r)}")
    mes = ultimo_mes(lista)
    g_mal, i_mal = totales(lista, r, mes, con_traspasos=True)
    g, i = totales(lista, r, mes)
    print(f"\nMes {mes}")
    print(f"  Contando traspasos (MAL): gastos {eur(g_mal)} · ingresos {eur(i_mal)}")
    print(f"  Sin traspasos (BIEN):     gastos {eur(g)} · ingresos {eur(i)}")
