"""El vigilante del permiso: mira cuántos días le quedan y, si quedan pocos,
avisa por Telegram para que lo renueves a tiempo.

Uso:  python vigilante.py      (una vez al día)
"""
import os
import re
from datetime import datetime, timezone

import comun


def main():
    umbral = int(os.getenv("AVISO_DIAS", "20"))
    s = comun.leer_sesion()
    if not s.get("valid_until"):
        comun.avisa("⚠️ Banco: no sé cuándo caduca el permiso. Míralo en el portal de tu proveedor.")
        return
    texto = re.sub(r"\.\d+", "", s["valid_until"]).replace("Z", "+00:00")  # sin fracciones de segundo
    caduca = datetime.fromisoformat(texto)
    if caduca.tzinfo is None:
        caduca = caduca.replace(tzinfo=timezone.utc)
    dias = (caduca - datetime.now(timezone.utc)).days
    print(f"Caduca {caduca:%d-%m-%Y} -> quedan {dias} días")
    if dias < umbral:
        comun.avisa(f"🟠 Renueva el permiso del banco: caduca el {caduca:%d-%m-%Y}, quedan {dias} días.\n"
                    "Repite: python conectar.py permiso")
    else:
        print("Sin aviso (queda margen).")


if __name__ == "__main__":
    main()
