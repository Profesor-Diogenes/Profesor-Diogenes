"""Crea en nominas/ dos nóminas en PDF INVENTADAS para probar (septiembre y octubre).
Cuando tengas las tuyas, bórralas y pon las tuyas en esa carpeta."""
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from comun import CARPETA, eur

NOMINAS = {
    "2026-09": {"devengos": [("Salario base", 1650.00), ("Plus transporte", 90.00), ("Plus nocturnidad", 120.00)],
                "deducciones": [("Contingencias comunes", 87.42), ("Desempleo", 29.76),
                                ("Formación profesional", 1.12), ("Retención IRPF", 223.20)]},
    "2026-10": {"devengos": [("Salario base", 1650.00), ("Plus transporte", 90.00), ("Plus nocturnidad", 80.00),
                             ("Atrasos convenio", 145.50)],
                "deducciones": [("Contingencias comunes", 92.29), ("Desempleo", 31.42),
                                ("Formación profesional", 1.18), ("Retención IRPF", 235.80)]},
}


def crear(mes, n, ruta):
    c = canvas.Canvas(str(ruta), pagesize=A4)
    y = 780

    def linea(texto, importe=None, negrita=False, x=60):
        nonlocal y
        c.setFont("Helvetica-Bold" if negrita else "Helvetica", 11)
        c.drawString(x, y, texto)
        if importe is not None:
            c.drawRightString(480, y, eur(importe))
        y -= 16

    c.setFont("Helvetica-Bold", 15)
    c.drawString(60, y, "NÓMINA DE EJEMPLO - DATOS INVENTADOS")
    y -= 24
    linea(f"Empresa Ejemplo S.L.   Periodo: {mes}")
    y -= 20
    bruto = round(sum(v for _, v in n["devengos"]), 2)
    desc = round(sum(v for _, v in n["deducciones"]), 2)
    linea("DEVENGOS", negrita=True)
    for k, v in n["devengos"]:
        linea(k, v, x=70)
    linea("TOTAL DEVENGADO", bruto, negrita=True)
    y -= 14
    linea("DEDUCCIONES", negrita=True)
    for k, v in n["deducciones"]:
        linea(k, v, x=70)
    linea("TOTAL A DEDUCIR", desc, negrita=True)
    y -= 14
    linea("LÍQUIDO A PERCIBIR", round(bruto - desc, 2), negrita=True)
    c.save()


if __name__ == "__main__":
    carpeta = CARPETA / "nominas"
    carpeta.mkdir(exist_ok=True)
    for mes, n in NOMINAS.items():
        ruta = carpeta / f"nomina_{mes}_ejemplo.pdf"
        crear(mes, n, ruta)
        print(f"Creada {ruta.relative_to(CARPETA)}")
