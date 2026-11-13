"""Programa 1: dar el permiso (solo lectura) y guardar la sesión.

Paso A:  python conectar.py permiso
         -> te da un enlace. Ábrelo, entra en tu banco como siempre y di que sí.
            Al acabar, el navegador vuelve a tu REDIRECT_URL con ?code=ALGO en la dirección.
Paso B:  python conectar.py sesion ALGO
         -> guarda la sesión en datos/sesion.json

Para renovar el permiso cuando caduque, repite A y B.
"""
import secrets
import sys
from datetime import datetime, timedelta, timezone

import requests

import comun


def permiso():
    dias = int(comun.conf("DIAS_PERMISO", "90"))
    hasta = (datetime.now(timezone.utc) + timedelta(days=dias)).isoformat(timespec="seconds")
    cuerpo = {
        "access": {"valid_until": hasta},   # solo acceso de lectura: cuentas y movimientos
        "aspsp": {"name": comun.conf("BANCO_NOMBRE"), "country": comun.conf("BANCO_PAIS", "ES")},
        "state": secrets.token_hex(16),
        "redirect_url": comun.conf("REDIRECT_URL"),
        "psu_type": "personal",
    }
    r = requests.post(f"{comun.api()}/auth", json=cuerpo, headers=comun.cabeceras(), timeout=30)
    r.raise_for_status()
    print(f"Permiso pedido por {dias} días. Abre este enlace y acepta en tu banco:\n")
    print(r.json()["url"])
    print("\nLuego copia el valor de 'code=' de la dirección a la que vuelvas y ejecuta:")
    print("  python conectar.py sesion ESE_CODIGO")


def sesion(codigo):
    r = requests.post(f"{comun.api()}/sessions", json={"code": codigo}, headers=comun.cabeceras(), timeout=30)
    r.raise_for_status()
    d = r.json()
    s = {
        "session_id": d["session_id"],
        "valid_until": (d.get("access") or {}).get("valid_until", ""),
        "cuentas": comun.ids_cuentas(d.get("accounts")),
    }
    comun.guardar_sesion(s)
    print(f"Sesión guardada. Cuentas: {len(s['cuentas'])}. El permiso caduca: {s['valid_until'] or 'desconocido'}")


if __name__ == "__main__":
    if sys.argv[1:2] == ["permiso"]:
        permiso()
    elif sys.argv[1:2] == ["sesion"] and len(sys.argv) == 3:
        sesion(sys.argv[2])
    else:
        print(__doc__)
