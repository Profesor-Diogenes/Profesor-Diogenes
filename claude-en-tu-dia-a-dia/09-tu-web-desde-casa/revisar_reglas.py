"""Lee las reglas del túnel una por una y te dice a qué apunta cada una y si hay algo escuchando en ese puerto.
Avisa también de los despistes típicos: un nombre repetido, una regla general por encima de una concreta
(la concreta no se usaría nunca) y que falte el 404 del final.

Uso:  python revisar_reglas.py               -> lee config.yml de esta carpeta
      python revisar_reglas.py otro.yml      -> lee otro archivo de reglas
"""
import socket
import sys
from fnmatch import fnmatch
from pathlib import Path
from urllib.parse import urlparse

import yaml

ARCHIVO = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent / "config.yml"


def escucha(host, puerto):
    with socket.socket() as s:
        s.settimeout(1)
        return s.connect_ex((host, puerto)) == 0


def main():
    reglas = (yaml.safe_load(ARCHIVO.read_text(encoding="utf-8")) or {}).get("ingress") or []
    if not reglas:
        sys.exit(f"{ARCHIVO.name} no tiene reglas (falta la sección ingress).")
    avisos, vistos = [], {}
    for i, r in enumerate(reglas):
        nombre, destino = r.get("hostname"), str(r.get("service", ""))
        etiqueta = nombre or "(todo lo demás)"
        if destino.startswith("http_status"):
            print(f"#{i} {etiqueta:22} -> {destino}")
        else:
            u = urlparse(destino)
            puerto = u.port or (443 if u.scheme == "https" else 80)
            vivo = escucha(u.hostname or "127.0.0.1", puerto)
            print(f"#{i} {etiqueta:22} -> {u.hostname}:{puerto}  {'OK, escucha' if vivo else 'NADIE ESCUCHA'}")
            if not vivo:
                avisos.append(f"#{i} '{etiqueta}' manda a un puerto donde no hay nada: a quien entre le saldrá un error.")
        if nombre:
            if nombre in vistos:
                avisos.append(f"'{nombre}' sale dos veces (#{vistos[nombre]} y #{i}): solo se usa la primera.")
            for anterior, j in vistos.items():
                if "*" in anterior and "*" not in nombre and fnmatch(nombre, anterior):
                    avisos.append(f"#{j} '{anterior}' está por encima de #{i} '{nombre}': la concreta no se usará nunca.")
            vistos.setdefault(nombre, i)
    if reglas[-1].get("hostname"):
        avisos.append("La última regla no es para todo lo demás: pon al final  - service: http_status:404")
    print("\n".join(["", "AVISOS:"] + ["  - " + a for a in avisos]) if avisos else "\nSin avisos: todo apunta a algo vivo y en buen orden.")


if __name__ == "__main__":
    main()
