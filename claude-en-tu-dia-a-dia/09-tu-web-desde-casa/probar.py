"""Prueba la web con un navegador sin pantalla: abre las tres páginas, mira que responden bien
y saca una captura de cada una en la carpeta capturas/.

Uso:  python probar.py                          -> prueba http://127.0.0.1:8099/
      python probar.py https://web.tudominio.es/ -> prueba otra dirección (por ejemplo, la del túnel)
"""
import sys
from pathlib import Path

from playwright.sync_api import Error, sync_playwright

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8099/").rstrip("/") + "/"
PAGINAS = ["index.html", "privacidad.html", "condiciones.html"]
CAPTURAS = Path(__file__).resolve().parent / "capturas"


def main():
    CAPTURAS.mkdir(exist_ok=True)
    fallos = 0
    with sync_playwright() as p:
        nav = p.chromium.launch()  # sin pantalla
        pagina = nav.new_page(viewport={"width": 800, "height": 500})
        for nombre in PAGINAS:
            try:
                r = pagina.goto(BASE + nombre, timeout=15000)
            except Error:
                print(f"{nombre:18} NO RESPONDE  ¿Está arrancado el servidor web en {BASE}?")
                fallos += 1
                continue
            foto = CAPTURAS / nombre.replace(".html", ".png")
            pagina.screenshot(path=str(foto))
            ok = r is not None and r.status == 200
            fallos += not ok
            print(f"{nombre:18} {r.status if r else '???'}  {pagina.title():35} captura: capturas/{foto.name}")
        nav.close()
    print("Todo bien: tres páginas, tres capturas." if not fallos else f"OJO: {fallos} página(s) con problemas.")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
