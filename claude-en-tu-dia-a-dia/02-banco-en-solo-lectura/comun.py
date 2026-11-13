"""Lo que comparten los tres programas: configuración, firma con la llave
privada, la sesión guardada y el aviso por Telegram."""
import json
import os
import sys
import time
from pathlib import Path

import jwt  # PyJWT
import requests
from dotenv import load_dotenv

CARPETA = Path(__file__).resolve().parent
DATOS = CARPETA / "datos"            # aquí van TUS datos (no se suben a ningún sitio)
SESION = DATOS / "sesion.json"
MOVIMIENTOS = DATOS / "movimientos.csv"
TELEGRAM_API = "https://api.telegram.org"

load_dotenv(CARPETA / ".env")


def conf(nombre, defecto=None):
    valor = os.getenv(nombre, defecto)
    if valor is None or valor == "" or "TU_" in str(valor):
        sys.exit(f"Falta {nombre} en el archivo .env (copia .env.ejemplo a .env y rellénalo).")
    return valor


def api():
    return conf("PROVEEDOR_API").rstrip("/")


def _llave():
    ruta = Path(conf("LLAVE_PRIVADA"))
    ruta = ruta if ruta.is_absolute() else CARPETA / ruta
    if not ruta.exists():
        sys.exit(f"No encuentro la llave privada en {ruta.name}. Ponla en esta carpeta y su nombre en LLAVE_PRIVADA.")
    return ruta.read_text(encoding="utf-8")


def cabeceras():
    """La llave privada firma cada petición (un JWT que caduca en 5 minutos).
    La llave se LEE del archivo: nunca va escrita en el código."""
    app_id = conf("APP_ID")
    ahora = int(time.time())
    carga = {"iss": conf("JWT_EMISOR"), "aud": conf("JWT_AUDIENCIA"),
             "iat": ahora, "exp": ahora + 300, "sub": app_id}
    token = jwt.encode(carga, _llave(), algorithm="RS256", headers={"kid": app_id})
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def leer_sesion():
    if not SESION.exists():
        sys.exit("Todavía no hay permiso. Primero: python conectar.py permiso")
    return json.loads(SESION.read_text(encoding="utf-8"))


def guardar_sesion(s):
    DATOS.mkdir(exist_ok=True)
    SESION.write_text(json.dumps(s, indent=2, ensure_ascii=False), encoding="utf-8")


def ids_cuentas(lista):
    """El proveedor puede dar las cuentas como textos o como objetos con 'uid'."""
    return [c["uid"] if isinstance(c, dict) else c for c in (lista or [])]


def avisa(texto):
    """Manda un aviso por Telegram. Si no hay Telegram en el .env, solo lo escribe."""
    print(texto)
    token = os.getenv("TELEGRAM_TOKEN", "")
    chat = os.getenv("TELEGRAM_CHAT_ID", "")
    if not token or not chat or "TU_" in token + chat:
        print("(Telegram sin configurar en el .env: aviso solo en pantalla)")
        return
    url = f"{TELEGRAM_API}/bot{token}/sendMessage"
    requests.post(url, data={"chat_id": chat, "text": texto}, timeout=20).raise_for_status()
