#!/usr/bin/env python3
"""Bots de Solana 24 · Probar una regla contra el pasado, sin hacerse trampas.

Tienes una tabla de fichas (fichas.csv): una fila por token, con lo que se sabía AL VERLO y lo que hizo después.
Una regla es "este dato entre tanto y tanto" (por ejemplo: holder_count entre 150 y 400).

La trampa: si buscas la regla y la compruebas en las mismas fichas, siempre encuentras alguna que "funciona".
Por eso aquí la tabla se parte en dos POR FECHA: la primera mitad es para BUSCAR, la segunda para COMPROBAR.

Uso en la terminal:
  python3 reglas.py campos                     qué datos tiene la tabla
  python3 reglas.py regla holder_count 150 400 prueba una regla tuya
  python3 reglas.py mejor                      busca la mejor regla en la primera mitad y la comprueba en la segunda
  python3 reglas.py azar 500                   prueba 500 reglas AL AZAR: cuántas "funcionan" por pura suerte
"""
import csv, os, random, sys, datetime

AQUI = os.path.dirname(os.path.abspath(__file__))
TABLA = os.environ.get("FICHAS", os.path.join(AQUI, "fichas.csv"))
NO_SON_DATOS = ("t0", "contrato", "simbolo", "maximo_x", "final_x", "dobla")   # lo de después NO vale para decidir
MINIMO = 30          # con menos fichas que esto, una regla no dice nada
VENTAJA = 8.0        # puntos por encima de la media para decir que una regla "funciona"


def carga():
    filas = []
    with open(TABLA, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            d = {}
            for k, v in r.items():
                if k in ("contrato", "simbolo"):
                    d[k] = v
                else:
                    try: d[k] = float(v)
                    except ValueError: d[k] = None
            filas.append(d)
    filas.sort(key=lambda x: x["t0"])
    m = len(filas) // 2
    return filas[:m], filas[m:]


def campos(filas):
    return [k for k in filas[0] if k not in NO_SON_DATOS]


def nota(filas, campo=None, lo=None, hi=None):
    """cuántas fichas cumplen la regla y qué porcentaje dobló"""
    if campo:
        filas = [f for f in filas if f.get(campo) is not None and lo <= f[campo] <= hi]
    n = len(filas)
    return n, (100.0 * sum(f["dobla"] for f in filas) / n if n else 0.0)


def dia(t):
    return datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%d-%m %H:%M")


def cabecera(a, b):
    na, pa = nota(a); nb, pb = nota(b)
    return ("Tabla: %d fichas.\n"
            "· Para BUSCAR:    %d fichas (%s → %s). Doblan el %.1f %%.\n"
            "· Para COMPROBAR: %d fichas (%s → %s). Doblan el %.1f %%.\n") % (
        na + nb, na, dia(a[0]["t0"]), dia(a[-1]["t0"]), pa, nb, dia(b[0]["t0"]), dia(b[-1]["t0"]), pb)


def prueba_regla(campo, lo, hi):
    a, b = carga()
    if campo not in campos(a):
        return "No conozco el dato «%s». Mira la lista con: campos" % campo
    _, pa = nota(a); _, pb = nota(b)
    n1, p1 = nota(a, campo, lo, hi); n2, p2 = nota(b, campo, lo, hi)
    t = cabecera(a, b) + "\nRegla: %s entre %g y %g\n" % (campo, lo, hi)
    t += "· Donde la buscaste:   %d fichas, doblan el %.1f %% (%+.1f sobre la media)\n" % (n1, p1, p1 - pa)
    t += "· Donde se comprueba:  %d fichas, doblan el %.1f %% (%+.1f sobre la media)\n" % (n2, p2, p2 - pb)
    if n2 < MINIMO:
        t += "\nOjo: en la parte de comprobar solo hay %d fichas. Con menos de %d, el número baila solo." % (n2, MINIMO)
    elif p2 - pb >= VENTAJA:
        t += "\nAguanta fuera de donde la buscaste. No es una prueba de nada todavía: es una regla que merece más datos."
    elif p2 - pb > 0:
        t += "\nFuera de donde la buscaste se queda a medias. Con %d fichas, esa diferencia no se distingue de la suerte." % n2
    else:
        t += "\nFuera de donde la buscaste, se desinfla."
    return t


def cortes(filas, campo):
    v = sorted(f[campo] for f in filas if f.get(campo) is not None)
    if len(v) < 5 * MINIMO or v[0] == v[-1]:
        return []
    return sorted(set(v[int(len(v) * q / 10)] for q in range(0, 10)) | {v[-1]})


def reglas_posibles(filas):
    for c in campos(filas):
        k = cortes(filas, c)
        for i in range(len(k)):
            for j in range(i + 1, len(k)):
                yield c, k[i], k[j]


def mejor():
    a, b = carga()
    _, pa = nota(a); _, pb = nota(b)
    cand = []
    total = 0
    for c, lo, hi in reglas_posibles(a):
        total += 1
        n, p = nota(a, c, lo, hi)
        if n >= MINIMO:
            cand.append((p - pa, c, lo, hi, n, p))
    cand.sort(reverse=True)
    t = cabecera(a, b) + "\nHe probado %d reglas en la parte de buscar. Las cinco mejores, y lo que hacen donde se comprueba:\n" % total
    for d, c, lo, hi, n, p in cand[:5]:
        n2, p2 = nota(b, c, lo, hi)
        t += "\n· %s entre %g y %g\n    buscar: %d fichas, %.1f %% (%+.1f)   →   comprobar: %d fichas, %.1f %% (%+.1f)" % (
            c, lo, hi, n, p, d, n2, p2, p2 - pb)
    return t


def azar(cuantas=500, semilla=None):
    """Reglas que nadie ha pensado (dato y números al azar): cuántas 'funcionan' por pura suerte."""
    a, b = carga()
    rnd = random.Random(semilla)
    _, pa = nota(a); _, pb = nota(b)
    cs = [c for c in campos(a) if cortes(a, c)]
    ganan = aguantan = validas = 0
    for _ in range(cuantas):
        c = rnd.choice(cs); k = cortes(a, c)
        i, j = sorted(rnd.sample(range(len(k)), 2))
        n, p = nota(a, c, k[i], k[j])
        if n < MINIMO:
            continue
        validas += 1
        if p - pa >= VENTAJA:
            ganan += 1
            n2, p2 = nota(b, c, k[i], k[j])
            if n2 >= MINIMO and p2 - pb >= VENTAJA:
                aguantan += 1
    t = cabecera(a, b)
    t += "\n%d reglas elegidas A CIEGAS (un dato cualquiera, entre dos números cualesquiera), %d con fichas suficientes.\n" % (cuantas, validas)
    t += "· «Funcionan» donde se buscan (+%g puntos o más): %d\n" % (VENTAJA, ganan)
    t += "· De esas, siguen funcionando donde se comprueba: %d\n" % aguantan
    t += "\nNadie pensó esas reglas. Las que salen bien, salen bien de casualidad. Por eso una regla que «funciona» en tus datos no vale nada hasta que la compruebas en otros."
    return t


def main(a):
    if not a or a[0] == "campos":
        x, _ = carga()
        return "Datos de cada ficha (lo que se sabía al ver el token):\n" + ", ".join(campos(x))
    if a[0] == "regla" and len(a) == 4:
        return prueba_regla(a[1], float(a[2].replace(",", ".")), float(a[3].replace(",", ".")))
    if a[0] == "mejor":
        return mejor()
    if a[0] == "azar":
        return azar(int(a[1]) if len(a) > 1 else 500)
    return __doc__


if __name__ == "__main__":
    print(main(sys.argv[1:]))
