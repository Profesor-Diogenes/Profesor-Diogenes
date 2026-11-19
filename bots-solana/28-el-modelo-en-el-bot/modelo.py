#!/usr/bin/env python3
"""Bots de Solana 28 · Enchufar el modelo al bot y medirlo en papel, en directo.

Tres piezas:
  1. ENTRENAR: con la tabla del vídeo 25 (tabla.csv), un modelo LightGBM aprende qué fichas doblaron.
     Solo con los datos que GMGN te da HOY gratis en su ranking: si el modelo usa un dato que en directo no tienes, no sirve.
  2. VIGILAR: cada 10 minutos lee el ranking de GMGN, le pone nota a cada token nuevo de pump.fun y lo apunta.
     Si la nota está entre las más altas, te avisa: "el modelo lo compraría".
  3. MEDIR: pasadas 6 horas, baja las velas de cada token apuntado (GeckoTerminal) y compara
     lo que eligió el modelo con todos los demás y con una moneda al aire.

Uso sin Telegram:
  python3 modelo.py entrena          entrena y guarda modelo.txt
  python3 modelo.py vigila           se queda vigilando (Ctrl+C para parar)
  python3 modelo.py balance          mide lo apuntado que ya tenga 6 horas
"""
import csv, json, os, random, sys, time, uuid
import requests

AQUI = os.path.dirname(os.path.abspath(__file__))


def cargar_env():
    ruta = os.path.join(AQUI, ".env")
    if os.path.exists(ruta):
        for linea in open(ruta, encoding="utf-8"):
            if "=" in linea and not linea.strip().startswith("#"):
                k, v = linea.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


cargar_env()
CLAVE_DE_PRUEBAS = "gmgn_solbscbaseethmonadtron"          # la clave pública de pruebas de GMGN (vídeo 1)
CLAVE = os.environ.get("GMGN_API_KEY") or CLAVE_DE_PRUEBAS
TABLA = os.environ.get("TABLA", os.path.join(AQUI, "tabla.csv"))
MODELO = os.path.join(AQUI, "modelo.txt")
APUNTES = os.path.join(AQUI, "apuntes.jsonl")
CADA = int(os.environ.get("CADA_MINUTOS", "10"))
VENTANA = 6
DOBLA = 2 / (0.97 * 0.97)                                 # x2 después de un 3 % de coste al entrar y otro al salir
GECKO = "https://api.geckoterminal.com/api/v2/networks/solana"

# Los datos que había en la tabla de agosto Y que el ranking gratis de GMGN da hoy. Los demás se quedan fuera.
DATOS = ["edad_min", "market_cap", "liquidity", "holder_count", "top_10_holder_rate", "dev_team_hold_rate",
         "rat_trader_amount_rate", "entrapment_ratio", "top70_sniper_hold_rate", "bot_degen_rate", "smart_degen_count",
         "renowned_count", "rug_ratio", "visiting_count", "twitter_rename_count"]


def num(v):
    try: return float(v)
    except (TypeError, ValueError): return float("nan")


# ---------------------------------------------------------------- 1. entrenar
def entrena():
    import lightgbm as lgb
    filas = list(csv.DictReader(open(TABLA, encoding="utf-8")))
    X = [[num(f[c]) for c in DATOS] for f in filas]
    y = [int(f["dobla"]) for f in filas]
    m = lgb.LGBMClassifier(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=10, verbose=-1, random_state=0, n_jobs=2)
    # El corte NO se saca de las fichas con las que ha aprendido (ahí se lo sabe todo de memoria y pone notas de 0,99).
    # Se saca de notas puestas a fichas que no ha visto: se parte la tabla en 5 trozos y cada trozo lo puntúa un modelo
    # entrenado con los otros cuatro.
    from sklearn.model_selection import cross_val_predict
    notas = sorted(cross_val_predict(m, X, y, cv=5, method="predict_proba")[:, 1])
    corte = notas[int(len(notas) * 0.8)]                  # la nota que separa el 20 % de arriba
    m.fit(X, y)
    m.booster_.save_model(MODELO)
    json.dump({"corte": corte, "datos": DATOS, "fichas": len(filas)}, open(MODELO + ".json", "w"))
    return "Modelo entrenado con %d fichas y %d datos. Te aviso cuando un token saque más de %.2f (el 20 %% de arriba)." % (len(filas), len(DATOS), corte)


_modelo = []


def nota(ficha):
    import lightgbm as lgb
    if not _modelo:
        _modelo.append(lgb.Booster(model_file=MODELO))
        _modelo.append(json.load(open(MODELO + ".json"))["corte"])
    return float(_modelo[0].predict([[num(ficha.get(c)) for c in DATOS]])[0]), _modelo[1]



# ---------------------------------------------------------------- 2. vigilar
def ranking():
    """Los tokens con más movimiento de la última hora y de las últimas 24 h según GMGN (dos preguntas)."""
    vistos = {}
    for intervalo in ("1h", "24h"):
        q = {"chain": "sol", "interval": intervalo, "limit": 100, "timestamp": int(time.time()), "client_id": str(uuid.uuid4())}
        try:
            d = requests.get("https://openapi.gmgn.ai/v1/market/rank", params=q, timeout=25,
                             headers={"X-APIKEY": CLAVE, "User-Agent": "profesor-diogenes"}).json()
            lista = ((d.get("data") or {}).get("data") or d.get("data") or {}).get("rank") or []
        except Exception:
            lista = []
        for t in lista:
            vistos.setdefault(t.get("address"), t)
        time.sleep(2)
    return list(vistos.values())


def ficha_de(t, ahora):
    nacio = num(t.get("creation_timestamp") or t.get("open_timestamp"))
    f = {c: t.get(c) for c in DATOS if c != "edad_min"}
    f["edad_min"] = (ahora - nacio) / 60 if nacio == nacio else None
    return f


def apuntados():
    if not os.path.exists(APUNTES):
        return []
    return [json.loads(l) for l in open(APUNTES, encoding="utf-8") if l.strip()]


def una_vuelta(avisar=None):
    ya = {a["ca"] for a in apuntados()}
    ahora = time.time(); nuevos = 0
    for t in ranking():
        ca = t.get("address")
        plataforma = ("%s %s" % (t.get("launchpad") or "", t.get("launchpad_platform") or "")).lower()
        if not ca or ca in ya or "pump" not in plataforma:
            continue
        f = ficha_de(t, ahora)
        n, corte = nota(f)
        a = {"ca": ca, "simbolo": t.get("symbol"), "visto": int(ahora), "market_cap": num(t.get("market_cap")),
             "nota": round(n, 4), "elegido": n >= corte, "ficha": f}
        with open(APUNTES, "a", encoding="utf-8") as o:
            o.write(json.dumps(a, ensure_ascii=False) + "\n")
        nuevos += 1
        if a["elegido"] and avisar:
            avisar("🎯 El modelo lo compraría (en papel): %s\n%s\nNota %.2f · capitalización %s $" % (a["simbolo"], ca, n, int(a["market_cap"] or 0)))
    return nuevos


def vigila(avisar=None):
    while True:
        try:
            n = una_vuelta(avisar)
            print(time.strftime("%H:%M"), "nuevos apuntados:", n, flush=True)
        except Exception as e:
            print("fallo:", e, flush=True)
        time.sleep(CADA * 60)


# ---------------------------------------------------------------- 3. medir
_ultima = [0.0]


def gecko(ruta, **p):
    """GeckoTerminal gratis: unas 10 preguntas por minuto. Una cada 6,5 segundos."""
    for _ in range(8):
        espera = 6.5 - (time.time() - _ultima[0])
        if espera > 0: time.sleep(espera)
        _ultima[0] = time.time()
        try:
            r = requests.get(GECKO + ruta, params=p, timeout=25, headers={"Accept": "application/json"})
            if r.status_code == 429: time.sleep(30); continue
            return r.json() if r.status_code == 200 else None
        except Exception:
            time.sleep(3)
    return None


def pools_gordos(contratos):
    """El pool con más liquidez de cada token (DexScreener, de 30 en 30; las dos preguntas, como en el vídeo 16)."""
    out = {}
    for i in range(0, len(contratos), 30):
        pares = []
        for url in ("https://api.dexscreener.com/latest/dex/tokens/", "https://api.dexscreener.com/tokens/v1/solana/"):
            try:
                d = requests.get(url + ",".join(contratos[i:i + 30]), timeout=15).json()
                pares += d if isinstance(d, list) else (d.get("pairs") or [])
            except Exception:
                pass
        for par in sorted(pares, key=lambda x: float((x.get("liquidity") or {}).get("usd") or 0)):
            ca = (par.get("baseToken") or {}).get("address")
            if ca in contratos and par.get("pairAddress"):
                out[ca] = par["pairAddress"]
        time.sleep(0.3)
    return out


def medir_uno(pool, visto):
    if not pool:
        return None
    hasta = visto + VENTANA * 3600
    d = gecko("/pools/%s/ohlcv/minute" % pool, aggregate=1, limit=1000, before_timestamp=hasta + 60)
    if d is None:
        return None
    v = sorted([[int(x[0])] + [float(y) for y in x[1:]] for x in ((d.get("data") or {}).get("attributes") or {}).get("ohlcv_list") or []
                if visto < x[0] <= hasta], key=lambda x: x[0])
    if len(v) < 2 or sum(x[5] for x in v) < 1000 or not v[0][1]:
        return None                                        # sin velas o sin volumen: no se mide
    entrada = v[0][1]                                      # se entra en la vela siguiente a verlo
    maximo = max(x[2] for x in v) / entrada
    return {"dobla": maximo >= DOBLA, "x_fin": v[-1][4] / entrada, "x_max": maximo}


def ganancia(m, coste=0.03):
    """Compras al entrar. Si llega a doblar lo que pusiste (después de costes), vendes ahí; si no, a las 6 horas.
    coste = lo que pierdes al comprar y otra vez al vender (comisiones y lo que se mueve el precio contra ti)."""
    return 1.0 if m["x_max"] >= 2 / ((1 - coste) ** 2) else m["x_fin"] * (1 - coste) ** 2 - 1


def balance():
    medidas = os.path.join(AQUI, "medidas.json")
    hechas = json.load(open(medidas)) if os.path.exists(medidas) else {}
    listos = [a for a in apuntados() if time.time() - a["visto"] >= VENTANA * 3600 and a["ca"] not in hechas]
    pools = pools_gordos([a["ca"] for a in listos])
    for a in listos:
        m = medir_uno(pools.get(a["ca"]), a["visto"])
        hechas[a["ca"]] = {"medida": m, "elegido": a["elegido"]}
        json.dump(hechas, open(medidas, "w"))
    corte = json.load(open(MODELO + ".json"))["corte"]
    nota_de = {a["ca"]: a["nota"] for a in apuntados()}
    med = [(nota_de.get(ca, 0) >= corte, h["medida"]) for ca, h in hechas.items() if h["medida"]]
    if not med:
        return "Todavía no hay nada que lleve %d horas apuntado y se pueda medir." % VENTANA
    todos = [m for _, m in med]; elegidos = [m for e, m in med if e]
    pct = lambda l: 100.0 * sum(m["dobla"] for m in l) / len(l) if l else 0
    gan = lambda l: 100.0 * sum(ganancia(m) for m in l) / len(l) if l else 0
    r = random.Random(1); k = len(elegidos)
    monedas = sorted(pct(r.sample(todos, k)) for _ in range(2000)) if 0 < k < len(todos) else [0, 0]
    t = "Apuntados: %d. Medibles (con velas y volumen): %d. Sin medir: %d.\n\n" % (len(hechas), len(med), len(hechas) - len(med))
    t += "· Todos: doblan %d de %d (%.1f %%). Comprándolos todos: %+.1f %% de media.\n" % (sum(m["dobla"] for m in todos), len(todos), pct(todos), gan(todos))
    t += "· Los que eligió el modelo: doblan %d de %d (%.1f %%). Comprándolos: %+.1f %% de media.\n" % (sum(m["dobla"] for m in elegidos), k, pct(elegidos), gan(elegidos))
    if k:
        t += "· Una moneda al aire eligiendo %d: entre %.1f %% y %.1f %% en 9 de cada 10 tiradas.\n" % (k, monedas[100], monedas[1900])
        t += "\nLo mismo según lo que te cueste entrar y salir (a cada lado):\n"
        for coste in (0.03, 0.05, 0.08, 0.10):
            g = lambda l: 100.0 * sum(ganancia(m, coste) for m in l) / len(l)
            t += "· %d %%: los del modelo %+.1f %% · todos %+.1f %%\n" % (coste * 100, g(elegidos), g(todos))
    return t


def main(a):
    if not a:
        return __doc__
    if a[0] == "entrena":
        return entrena()
    if a[0] == "vigila":
        vigila(); return ""
    if a[0] == "balance":
        return balance()
    return __doc__


if __name__ == "__main__":
    print(main(sys.argv[1:]))
