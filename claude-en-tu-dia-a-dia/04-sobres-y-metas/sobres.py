"""Sobres dentro de UNA cuenta de ahorro, sin abrir ni una cuenta más.

Lee los movimientos de la cuenta desde la fecha de corte, los reparte en sobres
con TUS reglas (reglas.txt), suma los ajustes a mano (ajustes.csv) y te dice
cuánto hay en cada sobre, el total y lo que puedes gastar.

Uso:  python sobres.py                    -> el informe en pantalla
      python sobres.py --saldo 750,00     -> además lo compara con el saldo real del banco
      python sobres.py --saldo 750 --telegram   -> y te lo manda por Telegram
"""
import argparse
import calendar
import csv
import json
import os
import sys
import unicodedata
from pathlib import Path

CARPETA = Path(__file__).resolve().parent
API = None  # se rellena con tu clave en enviar_telegram()


def leer_env():
    try:
        from dotenv import load_dotenv
        load_dotenv(CARPETA / ".env")
    except ImportError:
        pass


def ruta(nombre_variable, por_defecto):
    r = Path(os.getenv(nombre_variable, por_defecto))
    return r if r.is_absolute() else CARPETA / r


def limpio(texto):
    """Mayúsculas y sin tildes, para comparar conceptos del banco."""
    t = unicodedata.normalize("NFD", texto.upper())
    return "".join(c for c in t if unicodedata.category(c) != "Mn").strip()


def numero(texto):
    """'1.234,56' o '1234.56' -> 1234.56"""
    t = str(texto).strip().replace("€", "").replace(" ", "")
    if "," in t:
        t = t.replace(".", "").replace(",", ".")
    return float(t)


def eur(x):
    return f"{x:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


# ---------- lo que tú decides ----------

def leer_reglas(archivo):
    """reglas.txt -> lista de reglas en orden y el sobre por defecto (línea '*')."""
    reglas, defecto = [], None
    with open(archivo, encoding="utf-8") as f:
        for n, linea in enumerate(f, 1):
            linea = linea.split("#", 1)[0].strip()
            if not linea:
                continue
            if "=" not in linea:
                sys.exit(f"reglas.txt, línea {n}: falta el '='")
            palabras, destino = (x.strip() for x in linea.split("=", 1))
            cada_mes = False
            if "|" in destino:
                destino, marca = (x.strip() for x in destino.split("|", 1))
                cada_mes = limpio(marca) == "CADA MES"
            partes = []
            for trozo in destino.split(","):
                trozo = trozo.split()
                if not trozo:
                    continue
                sobre = trozo[0]
                cantidad = "resto" if len(trozo) == 1 or trozo[1].lower() == "resto" else numero(trozo[1])
                partes.append((sobre, cantidad))
            if sum(1 for _, c in partes if c == "resto") != 1:
                sys.exit(f"reglas.txt, línea {n}: tiene que haber un (y solo un) sobre que se lleve el resto")
            if palabras == "*":
                defecto = partes
            else:
                reglas.append({"palabras": limpio(palabras), "partes": partes, "cada_mes": cada_mes})
    if defecto is None:
        sys.exit("reglas.txt: falta la línea '* = sobre' para lo que no encaje en ninguna regla")
    return reglas, defecto


def repartir(importe, partes):
    """Cantidades fijas primero; el resto, al sobre marcado como resto."""
    fijo = sum(c for _, c in partes if c != "resto")
    return {s: (importe - fijo if c == "resto" else c) for s, c in partes}


# ---------- los datos ----------

def leer_movimientos(archivo, cuenta=""):
    """Movimientos sin repetidos (misma referencia del banco o, si no hay,
    misma fecha, importe y concepto). Acepta ';' o ','."""
    with open(archivo, encoding="utf-8-sig", newline="") as f:
        muestra = f.read(2048)
        f.seek(0)
        separador = ";" if muestra.count(";") >= muestra.count(",") else ","
        vistos, lista = set(), []
        for m in csv.DictReader(f, delimiter=separador):
            if cuenta and m.get("cuenta", "").strip() != cuenta:
                continue
            ref = (m.get("referencia") or "").strip()
            clave = ref or (m["fecha"], m["importe"], m["concepto"])
            if clave in vistos:
                continue
            vistos.add(clave)
            lista.append({"fecha": m["fecha"].strip(), "concepto": m["concepto"].strip(),
                          "importe": numero(m["importe"])})
    return sorted(lista, key=lambda m: m["fecha"])


def leer_ajustes(archivo):
    if not archivo.exists():
        return []
    ajustes = []
    with open(archivo, encoding="utf-8-sig", newline="") as f:
        for n, a in enumerate(csv.DictReader(f, delimiter=";"), 2):
            if not (a.get("motivo") or "").strip():
                sys.exit(f"ajustes.csv, línea {n}: cada ajuste lleva fecha y MOTIVO")
            ajustes.append({"fecha": a["fecha"].strip(), "sobre": a["sobre"].strip(),
                            "importe": numero(a["importe"]), "motivo": a["motivo"].strip()})
    return ajustes


def meses_completos(desde, hasta):
    """Meses enteros entre la fecha de corte y el último movimiento (AAAA-MM)."""
    a, m = int(desde[:4]), int(desde[5:7])
    salida = []
    while f"{a:04d}-{m:02d}" <= hasta[:7]:
        ultimo_dia = f"{a:04d}-{m:02d}-{calendar.monthrange(a, m)[1]:02d}"
        if f"{a:04d}-{m:02d}-01" >= desde and ultimo_dia <= hasta:
            salida.append(f"{a:04d}-{m:02d}")
        a, m = (a + 1, 1) if m == 12 else (a, m + 1)
    return salida


# ---------- el cálculo ----------

def calcular(partida, movimientos, reglas, defecto, ajustes):
    corte = partida["fecha_corte"]
    sobres = {s: float(x) for s, x in partida["sobres"].items()}
    entradas = {}  # (mes, regla) -> nº de movimientos
    usados = 0
    for m in movimientos:
        if m["fecha"] <= corte:
            continue  # el día de corte ya está en el punto de partida
        usados += 1
        regla = next((r for r in reglas if r["palabras"] in limpio(m["concepto"])), None)
        partes = regla["partes"] if regla else defecto
        for sobre, euros in repartir(m["importe"], partes).items():
            sobres[sobre] = sobres.get(sobre, 0.0) + euros
        if regla:
            clave = (m["fecha"][:7], regla["palabras"])
            entradas[clave] = entradas.get(clave, 0) + 1
    for a in ajustes:
        if a["fecha"] > corte:
            sobres[a["sobre"]] = sobres.get(a["sobre"], 0.0) + a["importe"]
    avisos = []
    if movimientos:
        for mes in meses_completos(corte, movimientos[-1]["fecha"]):
            for r in reglas:
                if r["cada_mes"] and (mes, r["palabras"]) not in entradas:
                    avisos.append(f"AVISO: la regla '{r['palabras']}' no ha entrado nada en {mes}")
    for s, x in sobres.items():
        if round(x, 2) < 0:
            avisos.append(f"AVISO: el sobre '{s}' está en negativo ({eur(x)}): falta un ajuste o sobra una regla")
    for a in ajustes:
        if a["fecha"] <= corte:
            avisos.append(f"AVISO: el ajuste del {a['fecha']} ({a['motivo']}) es anterior al corte y no cuenta")
    return {s: round(x, 2) for s, x in sobres.items()}, usados, avisos


def informe(partida, sobres, usados, avisos, saldo=None):
    total = round(sum(sobres.values()), 2)
    lineas = [f"SOBRES desde el {partida['fecha_corte']} ({usados} movimientos después del corte)"]
    ancho = max(len(s) for s in sobres) + 2
    for s, x in sobres.items():
        lineas.append(f"  {s:<{ancho}}{eur(x):>14}")
    lineas.append(f"  {'TOTAL':<{ancho}}{eur(total):>14}")
    if saldo is None:
        lineas.append("\nPara comprobarlo, pásale el saldo real del banco: python sobres.py --saldo 750,00")
    else:
        dif = round(saldo - total, 2)
        lineas.append(f"\nSaldo real del banco: {eur(saldo)}")
        if dif == 0:
            lineas.append("CUADRA al céntimo. Todo tiene dueño: gastable 0,00 €")
        elif dif > 0:
            lineas.append(f"Gastable (sin sobre): {eur(dif)}. Si no esperabas dinero suelto, falta una regla o un ajuste.")
        else:
            lineas.append(f"NO CUADRA: los sobres suman {eur(-dif)} más que el saldo. Falta un ajuste o sobra una regla.")
    lineas += [""] + avisos if avisos else []
    return "\n".join(lineas)


def enviar_telegram(texto):
    global API
    import requests
    token = os.getenv("TELEGRAM_TOKEN", "").strip()
    chat = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or "AQUI" in token or not chat or "AQUI" in chat:
        sys.exit("Para Telegram, rellena TELEGRAM_TOKEN y TELEGRAM_CHAT_ID en el .env (copia .env.ejemplo)")
    API = API or f"https://api.telegram.org/bot{token}/"
    r = requests.post(API + "sendMessage", data={"chat_id": chat, "text": texto}, timeout=20)
    if not r.ok:
        sys.exit(f"Telegram dice que no: {r.json().get('description', r.status_code)}. "
                 "¿Están bien TELEGRAM_TOKEN y TELEGRAM_CHAT_ID en el .env?")
    print("Enviado por Telegram.")


def main():
    p = argparse.ArgumentParser(description="Sobres dentro de una cuenta de ahorro")
    p.add_argument("--saldo", help="saldo real de la cuenta hoy, según tu banco (p. ej. 750,00)")
    p.add_argument("--telegram", action="store_true", help="mandar el informe por Telegram")
    args = p.parse_args()
    leer_env()
    with open(ruta("PARTIDA", "partida_ejemplo.json"), encoding="utf-8") as f:
        partida = json.load(f)
    if not partida.get("comprobado_a_mano"):
        print("OJO: el punto de partida no está marcado como comprobado a mano (\"comprobado_a_mano\": true).\n")
    reglas, defecto = leer_reglas(ruta("REGLAS", "reglas.txt"))
    movimientos = leer_movimientos(ruta("MOVIMIENTOS", "movimientos_ejemplo.csv"),
                                   os.getenv("CUENTA_AHORRO", "").strip())
    ajustes = leer_ajustes(ruta("AJUSTES", "ajustes_ejemplo.csv"))
    sobres, usados, avisos = calcular(partida, movimientos, reglas, defecto, ajustes)
    texto = informe(partida, sobres, usados, avisos, numero(args.saldo) if args.saldo else None)
    print(texto)
    if args.telegram:
        enviar_telegram(texto)


if __name__ == "__main__":
    main()
