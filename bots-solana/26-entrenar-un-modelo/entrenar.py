#!/usr/bin/env python3
"""Bots de Solana 26 · Entrenar un modelo y compararlo con una moneda al aire.

Coge la tabla del vídeo 25 (tabla.csv: una fila por token, lo que se sabía al verlo y si dobló en 6 horas),
la parte en dos POR FECHA, entrena un modelo LightGBM con la primera parte y lo examina con la segunda,
que no ha visto nunca. Y lo compara con lo único honrado: elegir los mismos tokens a cara o cruz.

Uso:
  python3 entrenar.py                 entrena con el 50 % más antiguo y examina con el resto
  python3 entrenar.py 60              entrena con el 60 % más antiguo
"""
import csv, os, random, sys, warnings

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
TABLA = os.environ.get("TABLA", os.path.join(AQUI, "tabla.csv"))
NO_SON_DATOS = ("t0", "contrato", "simbolo", "maximo_x", "final_x", "dobla")   # lo de después no se le enseña al modelo
ELIGE = 0.20                                                                   # el modelo "compra" el 20 % con mejor nota


def num(v):
    try: return float(v)
    except (TypeError, ValueError): return float("nan")


def carga():
    filas = list(csv.DictReader(open(TABLA, encoding="utf-8")))
    filas.sort(key=lambda f: float(f["t0"]))
    datos = [c for c in filas[0] if c not in NO_SON_DATOS]
    return filas, datos


def ganancia(f, coste=0.03):
    """Compras al entrar. Si llega a doblar lo que pusiste (después de costes), vendes ahí; si no, a las 6 horas.
    coste = lo que pierdes al comprar y otra vez al vender (comisiones y lo que se mueve el precio contra ti)."""
    objetivo = 2 / ((1 - coste) ** 2)
    return 1.0 if float(f["maximo_x"]) >= objetivo else float(f["final_x"]) * (1 - coste) ** 2 - 1


def resumen(nombre, fs):
    d = sum(int(f["dobla"]) for f in fs)
    return "%s: doblan %d de %d (%.1f %%) · ganancia media %+.1f %%" % (nombre, d, len(fs), 100.0 * d / len(fs), 100.0 * sum(map(ganancia, fs)) / len(fs))


def modelo():
    import lightgbm as lgb
    return lgb.LGBMClassifier(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=10,
                              verbose=-1, random_state=0, n_jobs=2)


def entrena(porcentaje=50):
    filas, datos = carga()
    m = int(len(filas) * porcentaje / 100)
    a, b = filas[:m], filas[m:]
    mod = modelo()
    mod.fit([[num(f[c]) for c in datos] for f in a], [int(f["dobla"]) for f in a])
    notas = mod.predict_proba([[num(f[c]) for c in datos] for f in b])[:, 1]
    k = max(1, int(len(b) * ELIGE))
    elegidos = [b[i] for i in sorted(range(len(b)), key=lambda i: -notas[i])[:k]]
    r = random.Random(1)
    monedas = sorted(100.0 * sum(int(f["dobla"]) for f in r.sample(b, k)) / k for _ in range(2000))
    t = "Entrena con %d tokens (los más antiguos) y se examina con %d que no ha visto nunca.\n\n" % (len(a), len(b))
    t += "En el examen:\n· " + resumen("Comprándolos todos", b) + "\n"
    t += "· " + resumen("Los %d que elige el modelo" % k, elegidos) + "\n"
    t += "· Una moneda eligiendo %d: doblan entre %.1f %% y %.1f %% en 9 de cada 10 tiradas.\n" % (k, monedas[100], monedas[1900])
    t += "\nY si comprar y vender te cuesta más (en memes, lo normal), lo que ganan los elegidos:\n"
    t += "   " + " · ".join("%d %% a cada lado: %+.1f %%" % (round(100 * c), 100.0 * sum(ganancia(f, c) for f in elegidos) / k)
                          for c in (0.03, 0.05, 0.08, 0.10)) + "\n"
    imp = sorted(zip(mod.feature_importances_, datos), reverse=True)[:5]
    t += "\nEn lo que más se fija: " + ", ".join(c for _, c in imp) + "."
    t += "\n\nAunque gane a la moneda, esto es un examen con datos del pasado, y el máximo de una vela no es un precio al que te vendan seguro. La prueba de verdad es en directo (vídeo 28)."
    return t


def main(a):
    if a and a[0] in ("-h", "--help", "ayuda"):
        return __doc__
    return entrena(int(a[0]) if a else 50)


if __name__ == "__main__":
    print(main(sys.argv[1:]))
