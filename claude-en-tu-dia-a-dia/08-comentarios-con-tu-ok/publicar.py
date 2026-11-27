"""Una pasada de publicación: solo lo que TÚ has aprobado, uno a uno, con espera de 1 a 3 minutos.

Te abre el post en tu navegador y te enseña el comentario aprobado. Lo pegas tú y confirmas.
Al confirmar se apunta en la memoria y no se vuelve a ofrecer: así nunca sale dos veces.

Uso:  python publicar.py
"""
import os
import random
import time
import webbrowser

import comentarios as cm

ESPERA_MIN = int(os.getenv("ESPERA_MIN_SEG", "60"))
ESPERA_MAX = int(os.getenv("ESPERA_MAX_SEG", "180"))


def main():
    estado = cm.leer_estado()
    cola = [(pid, e) for pid, e in estado.items() if e["estado"] == "aprobado"]
    if not cola:
        print("No hay nada aprobado. Solo se publica lo que apruebas con los botones de Telegram.")
        return
    for n, (pid, e) in enumerate(cola):
        if n:
            espera = random.randint(ESPERA_MIN, ESPERA_MAX)
            print(f"Espero {espera} segundos antes del siguiente...")
            time.sleep(espera)
        print(f"\nPost de {e['cuenta']} ({e['red']}): {e['enlace'] or '(sin enlace)'}")
        print(f"Comentario aprobado:\n\n    {e['aprobada']}\n")
        if e["enlace"]:
            webbrowser.open(e["enlace"])
        r = input("Pégalo en el post. ¿Publicado? [s = sí / n = déjalo para otra pasada / f = fuera]: ").strip().lower()
        if r == "s":
            e["estado"] = "publicado"
            cm.apuntar_en_memoria(e["aprobada"])
            print("Apuntado. Entra en el post y mira que hay UNA sola respuesta tuya.")
        elif r == "f":
            e["estado"] = "descartado"
        cm.guardar_estado(estado)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nParado. Lo que no confirmaste sigue aprobado para la próxima pasada.")
