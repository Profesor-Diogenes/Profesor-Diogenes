"""Cosas que usan todos los programas: los ajustes del .env, leer el banco y escribir euros."""
import csv
import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

CARPETA = Path(__file__).resolve().parent
load_dotenv(CARPETA / ".env")


def ajuste(nombre, defecto):
    return os.getenv(nombre, defecto).strip()


def palabras(nombre, defecto):
    """'LUZ, GAS' -> ['LUZ', 'GAS']"""
    return [p.strip().upper() for p in ajuste(nombre, defecto).split(",") if p.strip()]


def ruta(nombre, defecto):
    r = Path(ajuste(nombre, defecto))
    return r if r.is_absolute() else CARPETA / r


def banco():
    """Movimientos del banco (mismo formato que los capítulos 2 y 3), sin repetidos."""
    vistos, lista = set(), []
    with open(ruta("MOVIMIENTOS", "movimientos_ejemplo.csv"), encoding="utf-8", newline="") as f:
        for m in csv.DictReader(f, delimiter=";"):
            ref = (m.get("referencia") or "").strip()
            clave = ref or (m["fecha"], m["importe"], m["concepto"])
            if clave in vistos:
                continue
            vistos.add(clave)
            m["importe"] = round(float(m["importe"]), 2)
            m["fecha"] = date.fromisoformat(m["fecha"])
            m["concepto"] = m["concepto"].upper()
            lista.append(m)
    return lista


def eur(x):
    return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
