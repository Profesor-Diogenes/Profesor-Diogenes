#!/usr/bin/env python3
"""Bots de Solana 25 · Preparar la tabla para que la lea una máquina (y cazar la columna tramposa).

Junta dos ficheros de nuestros datos:
  libreta.jsonl.gz  = cada vez que vimos un token, su ficha EN ESE MOMENTO
  curvas.jsonl.gz   = qué hizo el precio después, vela a vela
y saca tabla.csv: UNA fila por token, con lo que se sabía al verlo por primera vez y lo que pasó en las 6 horas siguientes.

Reglas para no hacerse trampas (las mismas del vídeo 16):
  · la ficha es la PRIMERA vez que lo vimos; nada de fotos posteriores
  · se entra en la vela siguiente a verlo
  · solo tokens de pump.fun con más de 1.000 $ de volumen
  · "dobla" = llegar a x2 después de un 3 % de coste al entrar y otro al salir (x2,13 de precio), en 6 horas

Uso:
  python3 tabla.py hacer           hace tabla.csv (si no tienes los datos, los baja de nuestro GitHub)
  python3 tabla.py trampa          hace tabla_trampa.csv: igual, pero con una columna que mira el futuro sin que se note
  python3 tabla.py revisa FICHERO  busca columnas sospechosas: las que aciertan demasiado
"""
import csv, gzip, json, os, sys, urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.environ.get("DATOS", os.path.join(AQUI, "datos"))
WEB = "https://github.com/Profesor-Diogenes/Profesor-Diogenes/raw/datos/"
VENTANA = 6 * 3600
DOBLA = 2 / (0.97 * 0.97)
CAMPOS = ["edad_min", "market_cap", "liquidity", "volume_24h", "swaps_24h", "buys_24h", "sells_24h", "net_buy_24h", "holder_count",
          "top_10_holder_rate", "dev_team_hold_rate", "creator_balance_rate", "creator_created_count", "creator_created_open_ratio",
          "bundler_trader_amount_rate", "rat_trader_amount_rate", "entrapment_ratio", "top70_sniper_hold_rate", "fresh_wallet_rate",
          "suspected_insider_hold_rate", "bot_degen_rate", "smart_degen_count", "renowned_count", "rug_ratio", "progress",
          "x_user_follower", "tg_call_count", "visiting_count", "twitter_rename_count"]
RESULTADO = ("maximo_x", "final_x", "dobla")


def fichero(nombre):
    os.makedirs(DATOS, exist_ok=True)
    p = os.path.join(DATOS, nombre)
    if not os.path.exists(p):
        print("Bajando %s de nuestro GitHub (puede tardar)…" % nombre, flush=True)
        urllib.request.urlretrieve(WEB + nombre, p)
    return p


def lineas(nombre):
    with gzip.open(fichero(nombre), "rt", encoding="utf-8") as f:
        for l in f:
            try: yield json.loads(l)
            except ValueError: pass


def num(v):
    try: return float(v)
    except (TypeError, ValueError): return ""


def hacer(trampa=False):
    fotos = {}
    for t in lineas("libreta.jsonl.gz"):
        a = t.get("address")
        if a: fotos.setdefault(a, []).append(t)
    filas = []
    for c in lineas("curvas.jsonl.gz"):
        v = sorted(c.get("velas") or [], key=lambda x: x[0])
        fs = sorted(fotos.get(c["ca"], []), key=lambda x: x["t0"])
        if len(v) < 2 or not fs or sum(x[5] for x in v) < 1000:
            continue
        t = fs[0]                                   # la PRIMERA foto: lo que se sabía al verlo
        plataforma = ((t.get("launchpad") or "") + " " + (t.get("launchpad_platform") or "")).lower()
        if "pump" not in plataforma or not v[1][1]:
            continue
        entrada = v[1][1]                           # se entra en la vela siguiente
        despues = [x for x in v[1:] if x[0] - c["t0"] <= VENTANA]
        if not despues:
            continue
        f = {"t0": c["t0"], "contrato": c["ca"], "simbolo": t.get("symbol", "")}
        for k in CAMPOS:
            f[k] = num(t.get(k))
        if trampa:
            # LA TRAMPA: cuánto ha subido la capitalización entre la primera foto y la última que sacamos
            # en las 6 horas siguientes. Parece un dato más de la ficha. Pero esa última foto es del FUTURO.
            luego = [x for x in fs if c["t0"] < x["t0"] <= c["t0"] + VENTANA]
            mc0, mc1 = num(t.get("market_cap")), num((luego or fs)[-1].get("market_cap"))
            f["subida_market_cap"] = round(mc1 / mc0, 3) if mc0 and mc1 else ""
        maximo = max(x[2] for x in despues) / entrada
        f["maximo_x"] = round(maximo, 4)
        f["final_x"] = round(despues[-1][4] / entrada, 4)
        f["dobla"] = 1 if maximo >= DOBLA else 0
        filas.append(f)
    filas.sort(key=lambda f: f["t0"])
    salida = os.path.join(AQUI, "tabla_trampa.csv" if trampa else "tabla.csv")
    with open(salida, "w", newline="", encoding="utf-8") as o:
        w = csv.DictWriter(o, fieldnames=list(filas[0].keys()))
        w.writeheader(); w.writerows(filas)
    d = sum(f["dobla"] for f in filas)
    return salida, ("Tabla hecha: %d tokens, una fila por token, %d datos de cada uno.\n"
                    "Doblan %d (%.1f %%). Ese es el número a batir: cualquier regla o modelo tiene que acertar más que esto.\n"
                    "Fichero: %s") % (len(filas), len(filas[0]) - 6, d, 100.0 * d / len(filas), os.path.basename(salida))


def revisa(ruta):
    """Una columna que acierta demasiado casi siempre está mirando el futuro."""
    filas = list(csv.DictReader(open(ruta, encoding="utf-8")))
    base = 100.0 * sum(int(f["dobla"]) for f in filas) / len(filas)
    res = []
    for k in filas[0]:
        if k in ("t0", "contrato", "simbolo") + RESULTADO:
            continue
        v = sorted((num(f[k]), int(f["dobla"])) for f in filas if num(f[k]) != "")
        if len(v) < 90:
            continue
        corte = v[2 * len(v) // 3][0]
        alto = [x for x in v if x[0] > corte]          # el tercio con el valor más alto (o lo que quede por encima si hay muchos empates)
        if len(alto) < 30 or len(alto) == len(v):
            continue
        p = 100.0 * sum(d for _, d in alto) / len(alto)
        res.append((p - base, k, p, len(alto)))
    res.sort(reverse=True)
    t = "Base: dobla el %.1f %% de %d tokens.\nLos tokens con el valor más alto de cada columna (el tercio de arriba):\n\n" % (base, len(filas))
    for d, k, p, n in res[:6]:
        marca = "   ⚠️ SOSPECHOSA" if d >= 20 else ""
        t += "· %s: %d tokens, dobla el %.1f %% (%+.1f)%s\n" % (k, n, p, d, marca)
    if res and res[0][0] >= 20:
        t += ("\nUna columna que separa tanto, en memes, no es un descubrimiento: casi siempre se ha colado algo del futuro. "
              "Antes de entrenar nada, pregúntate a qué hora se sabía ese dato.")
    else:
        t += "\nNinguna columna separa de forma sospechosa. Lo normal: de lo que se sabía al verlo, nada separa mucho."
    return t


def main(a):
    if not a:
        return __doc__
    if a[0] == "hacer":
        return hacer()[1]
    if a[0] == "trampa":
        ruta, texto = hacer(trampa=True)
        return texto + "\n\n" + revisa(ruta)
    if a[0] == "revisa":
        return revisa(a[1] if len(a) > 1 else os.path.join(AQUI, "tabla.csv"))
    return __doc__


if __name__ == "__main__":
    print(main(sys.argv[1:]))
