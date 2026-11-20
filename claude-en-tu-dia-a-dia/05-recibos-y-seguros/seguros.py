"""Busca en tus movimientos los seguros, las devoluciones y las anulaciones.

1. Se queda con los movimientos que llevan alguna palabra de palabras.txt.
2. Tapa los números de cuenta ANTES de enseñar nada: pone [IBAN].
3. Lo ordena por fecha (+ lo que entra, - lo que sale).
4. Marca aparte cada devolución o anulación (nunca la suma con lo cobrado).
5. Saca los recibos que no reconoces (ni en palabras.txt ni en conocidos.txt).
6. Te dice qué recibos se acaban y cuáles se renuevan.

Uso:  python seguros.py                 (usa el archivo de MOVIMIENTOS del .env)
      python seguros.py otro.csv
"""
import csv
import os
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

CARPETA = Path(__file__).resolve().parent

# Cómo suele empezar un recibo domiciliado en el concepto del banco
PALABRAS_RECIBO = ["RECIBO", "ADEUDO", "DOMICILIACION", "CARGO"]
DEVOLUCION = ["DEVOLUCION", "ANULACION", "RETROCESION", "EXTORNO"]

# IBAN seguido (ES7600001111...) o en grupos de 4 (ES76 0000 1111 ...)
IBAN = re.compile(r"\b[A-Z]{2}\d{2}(?:[0-9A-Z]{11,30}|(?: [0-9A-Z]{4})(?: \d{4}){1,6}(?: \d{1,3})?)\b")
NUMERO_LARGO = re.compile(r"\b\d{10,}\b")  # números de cuenta o de tarjeta sueltos


def tapa(texto):
    return NUMERO_LARGO.sub("[NUMERO]", IBAN.sub("[IBAN]", texto))


def limpio(texto):
    t = unicodedata.normalize("NFD", texto.upper())
    return "".join(c for c in t if unicodedata.category(c) != "Mn").strip()


def numero(texto):
    t = str(texto).strip().replace("€", "").replace(" ", "")
    if "," in t:
        t = t.replace(".", "").replace(",", ".")
    return float(t)


def eur(x):
    return f"{x:+,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def leer_lista(nombre):
    archivo = CARPETA / nombre
    if not archivo.exists():
        return []
    with open(archivo, encoding="utf-8") as f:
        return [limpio(l.split("#", 1)[0]) for l in f if l.split("#", 1)[0].strip()]


def leer_movimientos(archivo):
    """Sin repetidos (misma referencia del banco o misma fecha, importe y concepto).
    Tapa los números de cuenta nada más leer. Acepta ';' o ','."""
    with open(archivo, encoding="utf-8-sig", newline="") as f:
        muestra = f.read(2048)
        f.seek(0)
        separador = ";" if muestra.count(";") >= muestra.count(",") else ","
        vistos, lista = set(), []
        for m in csv.DictReader(f, delimiter=separador):
            ref = (m.get("referencia") or "").strip()
            clave = ref or (m["fecha"], m["importe"], m["concepto"])
            if clave in vistos:
                continue
            vistos.add(clave)
            lista.append({"fecha": m["fecha"].strip(), "concepto": tapa(limpio(m["concepto"])),
                          "importe": numero(m["importe"])})
    return sorted(lista, key=lambda m: m["fecha"])


def es_devolucion(concepto):
    return any(p in concepto for p in DEVOLUCION)


def nombre_recibo(concepto):
    """'DEVOLUCION RECIBO HOGAR ASEG. EJEMPLO A [IBAN]' -> 'HOGAR ASEG. EJEMPLO A'"""
    t = concepto.replace("[IBAN]", "").replace("[NUMERO]", "")
    quitar = DEVOLUCION + PALABRAS_RECIBO + ["SEGURO", "ANUAL", "MENSUAL", "DE"]
    palabras = [p for p in t.split() if p not in quitar]
    return " ".join(palabras) or t.strip()


def mas_meses(fecha, meses):
    a, m, d = (int(x) for x in fecha.split("-"))
    m += meses
    a, m = a + (m - 1) // 12, (m - 1) % 12 + 1
    while True:
        try:
            return date(a, m, d).isoformat()
        except ValueError:
            d -= 1


def frecuencia(fechas):
    """Mensual, trimestral, anual... a partir de la distancia entre cobros."""
    if len(fechas) < 2:
        return None
    dias = [(date.fromisoformat(b) - date.fromisoformat(a)).days for a, b in zip(fechas, fechas[1:])]
    media = sum(dias) / len(dias)
    for nombre, meses, lo, hi in (("mensual", 1, 25, 35), ("trimestral", 3, 80, 100),
                                  ("semestral", 6, 170, 195), ("anual", 12, 350, 380)):
        if lo <= media <= hi:
            return nombre, meses
    return None


def main():
    try:
        from dotenv import load_dotenv
        load_dotenv(CARPETA / ".env")
    except ImportError:
        pass
    if len(sys.argv) > 1:
        archivo = Path(sys.argv[1])
    else:
        archivo = Path(os.getenv("MOVIMIENTOS", "movimientos_ejemplo.csv"))
        archivo = archivo if archivo.is_absolute() else CARPETA / archivo
    palabras = leer_lista("palabras.txt")
    se_acaban = leer_lista("se_acaban.txt")
    conocidos = leer_lista("conocidos.txt")
    if not palabras:
        sys.exit("palabras.txt está vacío: pon ahí SEGURO, DEVOLUCION, ANULACION y el nombre de tus aseguradoras")

    todo = leer_movimientos(archivo)
    filas = [m for m in todo if any(p in m["concepto"] for p in palabras)]
    print(f"Archivo: {archivo.name} · {len(todo)} movimientos, {len(filas)} con tus palabras\n")

    print("SEGUROS, DEVOLUCIONES Y ANULACIONES (por fecha)")
    for m in filas:
        marca = "  <-- DEVUELTO" if es_devolucion(m["concepto"]) else ""
        print(f"  {m['fecha']} {eur(m['importe']):>10}  {m['concepto']}{marca}")

    devueltos = [m for m in filas if es_devolucion(m["concepto"])]
    print(f"\nDEVOLUCIONES Y ANULACIONES: {len(devueltos)} (aparte: no se suman con lo cobrado)")
    por_recibo = {}
    for m in devueltos:
        por_recibo.setdefault(nombre_recibo(m["concepto"]), []).append(m["fecha"])
    for nombre, fechas in por_recibo.items():
        veces = "1 vez" if len(fechas) == 1 else f"{len(fechas)} veces"
        print(f"  {nombre}: {veces} ({', '.join(fechas)})")
    if devueltos:
        print("  -> Un recibo devuelto deja el saldo igual, pero no la póliza.")
        print("     Pide POR ESCRITO a la aseguradora que la póliza está al corriente.")

    print("\nRECIBOS QUE NO RECONOCES (ni en palabras.txt ni en conocidos.txt)")
    raros = [m for m in todo if m["importe"] < 0
             and any(m["concepto"].startswith(p) for p in PALABRAS_RECIBO)
             and not any(p in m["concepto"] for p in palabras + conocidos)]
    for m in raros:
        print(f"  {m['fecha']} {eur(m['importe']):>10}  {m['concepto']}")
    if raros:
        print("  -> Si no lo reconoces, devolverlo no basta: vuelve el mes siguiente. Bloquea a ese")
        print("     emisor en la app de tu banco y pide por escrito que anulen la orden de cobro.")
        print("     (Antes, pregunta en casa: un cargo raro no siempre es malo.)")
    else:
        print("  (ninguno)")

    print("\nQUÉ SE ACABA Y QUÉ SE RENUEVA")
    cobros = {}
    for m in filas:
        if m["importe"] < 0 and not es_devolucion(m["concepto"]):
            cobros.setdefault(nombre_recibo(m["concepto"]), []).append(m["fecha"])
    for nombre, fechas in cobros.items():
        ultimo = fechas[-1]
        if any(p in nombre for p in se_acaban):
            estado = "se acaba (está en se_acaban.txt)"
        else:
            f = frecuencia(fechas)
            if f:
                estado = f"{f[0]}, se renueva: próximo hacia el {mas_meses(ultimo, f[1])}"
            else:
                estado = f"un solo cobro: si es anual, se renueva hacia el {mas_meses(ultimo, 12)}"
        print(f"  {nombre:<28} último {ultimo}  {estado}")
    print("\nAntes de cada renovación: compara lo que pagas, lo que cubre y lo que te ofrecen otros.")
    print("Y lo que cubre tu póliza no lo sabe este programa: lee las condiciones (la letra pequeña).")


if __name__ == "__main__":
    main()
