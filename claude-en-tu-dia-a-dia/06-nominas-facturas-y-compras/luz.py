"""Paso 7: suma la luz y el gas por mes (todas las compañías) y pregunta por cada hueco."""
from comun import banco, eur, palabras


def meses_entre(a, b):
    y, m = a.year, a.month
    while (y, m) <= (b.year, b.month):
        yield f"{y}-{m:02d}"
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def main():
    claves = palabras("PALABRAS_LUZ", "LUZ, GAS")
    movs = banco()
    recibos = [m for m in movs if m["importe"] < 0 and any(p in m["concepto"] for p in claves)]
    if not recibos:
        print("No encuentro recibos. Mira las palabras de PALABRAS_LUZ en el .env.")
        return
    por_mes = {}
    for r in recibos:
        por_mes.setdefault(r["fecha"].isoformat()[:7], []).append(r)
    primero = min(m["fecha"] for m in movs)
    ultimo = max(m["fecha"] for m in movs)
    print("Luz y gas por mes:")
    for mes in meses_entre(primero, ultimo):
        rs = por_mes.get(mes, [])
        if not rs:
            print(f"   {mes}        —    PREGUNTA: ¿no hubo recibo, o se pagó por otra vía?")
            continue
        total = -sum(r["importe"] for r in rs)
        nota = ""
        if len(rs) > 1:
            nota = "   " + " + ".join(f"{eur(-r['importe'])} ({r['concepto']})" for r in rs)
            if len({r["concepto"] for r in rs}) > 1:
                nota += "   <- dos compañías: se suman las dos"
            else:
                nota += "   <- dos recibos este mes"
        print(f"   {mes} {eur(total):>10}{nota}")


if __name__ == "__main__":
    main()
