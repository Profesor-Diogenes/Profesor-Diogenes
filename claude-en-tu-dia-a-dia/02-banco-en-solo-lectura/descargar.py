"""Programa 2: descargar los movimientos (SOLO LECTURA) a datos/movimientos.csv, sin repetidos.

Uso:  python descargar.py
Pensado para lanzarlo una vez al día (la norma solo deja unas pocas consultas
al día sin que tú estés delante).
"""
import csv
from datetime import date, timedelta

import requests

import comun

COLUMNAS = ["fecha", "referencia", "concepto", "importe", "cuenta"]
SOLAPE_DIAS = 3        # empieza unos días antes, por si el banco apuntó algo tarde
PRIMERA_VEZ_DIAS = 90  # la primera vez, cuántos días hacia atrás


def cuentas_actuales(s):
    """No damos por hecho que los identificadores no cambian: se piden en cada conexión."""
    r = requests.get(f"{comun.api()}/sessions/{s['session_id']}", headers=comun.cabeceras(), timeout=30)
    r.raise_for_status()
    nuevas = comun.ids_cuentas(r.json().get("accounts"))
    if sorted(nuevas) != sorted(s.get("cuentas", [])):
        comun.avisa("⚠️ Banco: los identificadores de las cuentas han cambiado. "
                    "Uso los nuevos; revisa que los movimientos sigan llegando bien.")
        s["cuentas"] = nuevas
        comun.guardar_sesion(s)
    return nuevas


def a_fila(tx, cuenta):
    importe = float((tx.get("transaction_amount") or {}).get("amount", 0))
    if tx.get("credit_debit_indicator") == "DBIT":
        importe = -abs(importe)
    info = tx.get("remittance_information") or []
    concepto = " ".join(info) if isinstance(info, list) else str(info)
    if not concepto:
        otro = tx.get("creditor") or tx.get("debtor") or {}
        concepto = otro.get("name", "") if isinstance(otro, dict) else str(otro)
    return {
        "fecha": tx.get("booking_date") or tx.get("value_date") or tx.get("transaction_date") or "",
        "referencia": tx.get("entry_reference") or tx.get("transaction_id") or "",
        "concepto": " ".join(concepto.split()),
        "importe": f"{importe:.2f}",
        "cuenta": cuenta,
    }


def clave(f):
    """Repetido = misma referencia del banco; sin referencia, misma fecha, importe y concepto.
    (No se usa la cuenta: si el banco cambia sus identificadores, saldrían repetidos.)"""
    if f["referencia"]:
        return f["referencia"]
    return (f["fecha"], f["importe"], f["concepto"])


def leer_csv():
    if not comun.MOVIMIENTOS.exists():
        return []
    with open(comun.MOVIMIENTOS, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def descargar_cuenta(cuenta, desde):
    filas, params = [], {"date_from": desde.isoformat()}
    while True:
        r = requests.get(f"{comun.api()}/accounts/{cuenta}/transactions",
                         params=params, headers=comun.cabeceras(), timeout=60)
        r.raise_for_status()
        d = r.json()
        filas += [a_fila(tx, cuenta) for tx in d.get("transactions", [])]
        if not d.get("continuation_key"):
            return filas
        params["continuation_key"] = d["continuation_key"]


def main():
    s = comun.leer_sesion()
    viejas = leer_csv()
    vistos = {clave(f) for f in viejas}
    nuevas = []
    for cuenta in cuentas_actuales(s):
        fechas = [f["fecha"] for f in viejas if f["cuenta"] == cuenta and f["fecha"]]
        if fechas:
            desde = date.fromisoformat(max(fechas)) - timedelta(days=SOLAPE_DIAS)
        else:
            desde = date.today() - timedelta(days=PRIMERA_VEZ_DIAS)
        bajadas = descargar_cuenta(cuenta, desde)
        n = 0
        for f in bajadas:
            if clave(f) not in vistos:
                vistos.add(clave(f))
                nuevas.append(f)
                n += 1
        print(f"Cuenta ...{cuenta[-4:]}: {len(bajadas)} bajados desde {desde}, {n} nuevos")
    todas = sorted(viejas + nuevas, key=lambda f: f["fecha"])
    comun.DATOS.mkdir(exist_ok=True)
    with open(comun.MOVIMIENTOS, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS, delimiter=";")
        w.writeheader()
        w.writerows(todas)
    print(f"Guardado: datos/movimientos.csv ({len(todas)} movimientos, {len(nuevas)} nuevos)")


if __name__ == "__main__":
    main()
