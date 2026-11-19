#!/usr/bin/env python3
"""Bots de Solana 27 · Por qué el modelo se engaña (y te engaña a ti).

El mismo modelo del vídeo 26, examinado de cuatro maneras. Solo una es honrada.
  1. memoria  -> se le examina con las mismas fichas con las que aprendió
  2. azar     -> se parte la tabla al azar, no por fecha
  3. trampa   -> se le deja una columna que mira el futuro (la del vídeo 25)
  4. fecha    -> se entrena con lo antiguo y se examina con lo nuevo: la única que vale

Uso:
  python3 engano.py            las cuatro, una detrás de otra
  python3 engano.py memoria    (o azar, trampa, fecha) solo una
Necesita al lado tabla.csv y tabla_trampa.csv (vídeo 25).
"""
import csv, os, random, sys, warnings

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
NO_SON_DATOS = ("t0", "contrato", "simbolo", "maximo_x", "final_x", "dobla")
ELIGE = 0.20


def num(v):
    try: return float(v)
    except (TypeError, ValueError): return float("nan")


def carga(nombre="tabla.csv"):
    filas = list(csv.DictReader(open(os.path.join(AQUI, nombre), encoding="utf-8")))
    filas.sort(key=lambda f: float(f["t0"]))
    return filas, [c for c in filas[0] if c not in NO_SON_DATOS]


def nota_del_examen(a, b, datos):
    """Entrena con a, examina con b: de los que el modelo pone arriba (el 20 %), cuántos doblan."""
    import lightgbm as lgb
    mod = lgb.LGBMClassifier(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=10, verbose=-1, random_state=0, n_jobs=2)
    mod.fit([[num(f[c]) for c in datos] for f in a], [int(f["dobla"]) for f in a])
    notas = mod.predict_proba([[num(f[c]) for c in datos] for f in b])[:, 1]
    k = max(1, int(len(b) * ELIGE))
    top = sorted(range(len(b)), key=lambda i: -notas[i])[:k]
    base = 100.0 * sum(int(f["dobla"]) for f in b) / len(b)
    return 100.0 * sum(int(b[i]["dobla"]) for i in top) / k, base, k


def memoria():
    f, d = carga()
    p, base, k = nota_del_examen(f, f, d)
    return ("1 · EXAMEN CON LAS MISMAS FICHAS CON LAS QUE APRENDIÓ\n"
            "De los %d que pone arriba, doblan el %.1f %% (la media es %.1f %%).\n"
            "No ha aprendido nada: se las sabe de memoria. Como el alumno que se aprende las respuestas del examen del año pasado.") % (k, p, base)


def azar():
    f, d = carga(); notas = []
    for s in range(5):
        x = f[:]; random.Random(s).shuffle(x); m = len(x) // 2
        notas.append(nota_del_examen(x[:m], x[m:], d))
    p = sum(n[0] for n in notas) / 5; base = sum(n[1] for n in notas) / 5
    return ("2 · PARTIENDO LA TABLA AL AZAR (media de 5 tiradas)\n"
            "Los que pone arriba doblan el %.1f %% (la media es %.1f %%).\n"
            "Parece mejor que partiendo por fecha. Pero mezcla días: aprende cómo estaba el mercado ese martes "
            "y luego le preguntas por ese mismo martes. En la vida real, mañana no te lo ha enseñado nadie.") % (p, base)


def trampa():
    f, d = carga("tabla_trampa.csv"); m = len(f) // 2
    p, base, k = nota_del_examen(f[:m], f[m:], d)
    return ("3 · CON LA COLUMNA QUE MIRA EL FUTURO (vídeo 25)\n"
            "Partiendo por fecha, como se debe, pero con la columna tramposa dentro: "
            "de los %d que pone arriba, doblan el %.1f %% (la media es %.1f %%).\n"
            "Un examen espectacular. En directo esa columna no existe, y el modelo se queda sin lo único que sabía mirar.") % (k, p, base)


def fecha():
    f, d = carga(); m = len(f) // 2
    p, base, k = nota_del_examen(f[:m], f[m:], d)
    return ("4 · LA HONRADA: ENTRENA CON LO ANTIGUO, SE EXAMINA CON LO NUEVO\n"
            "De los %d que pone arriba, doblan el %.1f %% (la media es %.1f %%).\n"
            "Este es el único número que se parece a lo que te pasaría a ti. Y aun así es el pasado: "
            "el examen de verdad es en directo.") % (k, p, base)


def main(a):
    que = {"memoria": memoria, "azar": azar, "trampa": trampa, "fecha": fecha}
    if a and a[0] in que:
        return que[a[0]]()
    if a:
        return __doc__
    return "\n\n".join(x() for x in (memoria, azar, trampa, fecha))


if __name__ == "__main__":
    print(main(sys.argv[1:]))
