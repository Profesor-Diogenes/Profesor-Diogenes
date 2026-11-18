#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
La libreta: una base de datos donde tu bot apunta cada contrato que ves, con su foto de ESE momento
(precio, capitalización, liquidez, volumen), y le va haciendo fotos nuevas cada 15 minutos durante dos días.
Sin esto no se puede medir nada después.
Canal de YouTube: Profesor Diógenes · sección "Bots de Solana", vídeo 15.

    python3 libreta.py

Cómo se usa, desde tu bot:
  - Le pegas un contrato (y una nota detrás si quieres: "lo vi en tal grupo", "me gusta", "no me fío")
  - /libreta            -> cuántos contratos y cuántas fotos llevas
  - /ver <contrato>     -> su historia: la primera foto, la última, el máximo y el mínimo
  - /importa            -> mete en la libreta los ficheros .csv que haya en esta carpeta (los de los otros bots:
                           llamadas.csv, senales.csv, cribados.csv). Necesitan las columnas "hora" y "contrato".
  - /exporta            -> te manda la libreta entera en un fichero .csv

Cómo funciona por dentro:
  - Una base de datos SQLite (un solo fichero, "libreta.db", no hay que instalar nada) con dos tablas:
    "contratos" (cuándo lo viste, tu nota y la foto de ese momento) y "fotos" (una fila por cada mirada).
  - Los precios salen de DexScreener (gratis y sin clave), de 30 en 30 contratos por pregunta.
  - Se sigue cada contrato 48 horas o hasta que muere (liquidez por debajo de 1.000 $ en un token que ya salió de la curva).
Esto NO es consejo financiero. Es una herramienta para mirar.
"""
import os, re, csv, glob, time, sqlite3, threading
import requests


def cargar_env():
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(ruta):
        for linea in open(ruta, encoding="utf-8"):
            if "=" in linea and not linea.strip().startswith("#"):
                k, v = linea.strip().split("=", 1)
                if v.strip():
                    os.environ.setdefault(k.strip(), v.strip())


cargar_env()
AQUI = os.path.dirname(os.path.abspath(__file__))
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
MI_ID = os.environ.get("TELEGRAM_MI_ID", "").strip()
BOT = "https://api.telegram.org/bot%s/" % TOKEN
BASE = os.path.join(AQUI, "libreta.db")
CADA = int(os.environ.get("CADA_MINUTOS", "15"))
HORAS = int(os.environ.get("HORAS_DE_SEGUIMIENTO", "48"))
DIRECCION = re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b")
cerrojo = threading.Lock()


def base():
    b = sqlite3.connect(BASE)
    b.execute("""CREATE TABLE IF NOT EXISTS contratos (
        contrato TEXT PRIMARY KEY, simbolo TEXT, visto INTEGER, nota TEXT, origen TEXT,
        precio REAL, capitalizacion REAL, liquidez REAL, volumen_24h REAL, vivo INTEGER DEFAULT 1)""")
    b.execute("""CREATE TABLE IF NOT EXISTS fotos (
        contrato TEXT, hora INTEGER, precio REAL, capitalizacion REAL, liquidez REAL, volumen_24h REAL)""")
    b.execute("CREATE INDEX IF NOT EXISTS fotos_contrato ON fotos (contrato, hora)")
    return b


def telegram(metodo, **datos):
    try:
        return requests.post(BOT + metodo, json=datos, timeout=60).json()
    except Exception:
        return {}


def avisar(texto):
    telegram("sendMessage", chat_id=MI_ID, text=texto, parse_mode="HTML", disable_web_page_preview=True)


def dinero(x):
    x = x or 0
    if x >= 1e6: return "%.2f M$" % (x / 1e6)
    if x >= 1e3: return "%.1f K$" % (x / 1e3)
    return "%.0f $" % x


def fotos_ahora(contratos):
    """La foto de hasta 30 contratos por pregunta: precio en dólares, capitalización, liquidez y volumen de 24 h."""
    out = {}
    for i in range(0, len(contratos), 30):
        try:
            pares = requests.get("https://api.dexscreener.com/latest/dex/tokens/" + ",".join(contratos[i:i + 30]), timeout=15).json().get("pairs") or []
        except Exception:
            pares = []
        # Ojo: esa pregunta devuelve como mucho 30 PARES en total, no 30 tokens. Si en el lote hay un token con
        # muchos pools, se come el cupo y los demás no salen. Esta otra devuelve un par de cada token: no falta ninguno.
        try:
            uno = requests.get("https://api.dexscreener.com/tokens/v1/solana/" + ",".join(contratos[i:i + 30]), timeout=15).json()
            pares += uno if isinstance(uno, list) else []
        except Exception:
            pass
        for p in sorted(pares, key=lambda p: float((p.get("liquidity") or {}).get("usd") or 0)):     # gana el par con más liquidez
            b = p.get("baseToken") or {}
            if b.get("address") in contratos and p.get("priceUsd"):
                out[b["address"]] = {"simbolo": b.get("symbol") or "?", "precio": float(p["priceUsd"]),
                                     "mc": float(p.get("marketCap") or p.get("fdv") or 0),
                                     "liq": float((p.get("liquidity") or {}).get("usd") or 0),
                                     "vol": float((p.get("volume") or {}).get("h24") or 0)}
        time.sleep(0.3)
    return out


def apuntar(ca, nota="", origen="a mano", visto=None):
    """Apunta un contrato nuevo con su foto de AHORA. Si ya estaba, no se toca: la primera vez es la que cuenta."""
    with cerrojo:
        b = base()
        if b.execute("SELECT 1 FROM contratos WHERE contrato=?", (ca,)).fetchone():
            return None
        f = fotos_ahora([ca]).get(ca)
        if not f:
            return False
        ahora = int(time.time())
        b.execute("INSERT INTO contratos VALUES (?,?,?,?,?,?,?,?,?,1)", (ca, f["simbolo"], visto or ahora, nota, origen, f["precio"], f["mc"], f["liq"], f["vol"]))
        b.execute("INSERT INTO fotos VALUES (?,?,?,?,?,?)", (ca, ahora, f["precio"], f["mc"], f["liq"], f["vol"]))
        b.commit()
        return f


def seguimiento():
    """Cada 15 minutos, una foto nueva de todo lo que sigue vivo y tiene menos de 48 horas."""
    while True:
        time.sleep(CADA * 60)
        with cerrojo:
            b = base(); ahora = int(time.time())
            vivos = [r[0] for r in b.execute("SELECT contrato FROM contratos WHERE vivo=1 AND visto>?", (ahora - HORAS * 3600,))]
            f = fotos_ahora(vivos)
            for ca in vivos:
                x = f.get(ca)
                if not x:
                    continue
                b.execute("INSERT INTO fotos VALUES (?,?,?,?,?,?)", (ca, ahora, x["precio"], x["mc"], x["liq"], x["vol"]))
                if 0 < x["liq"] < 1000:                                   # ya salió de la curva y no queda liquidez: muerto
                    b.execute("UPDATE contratos SET vivo=0 WHERE contrato=?", (ca,))
            b.execute("UPDATE contratos SET vivo=0 WHERE visto<=?", (ahora - HORAS * 3600,))
            b.commit()


def importar():
    """Mete en la libreta los .csv de los otros bots que haya en esta carpeta."""
    nuevos = 0
    for fichero in glob.glob(os.path.join(AQUI, "*.csv")):
        if os.path.basename(fichero) == "libreta_exportada.csv":
            continue
        for fila in csv.DictReader(open(fichero, encoding="utf-8")):
            ca = fila.get("contrato")
            if not ca:
                continue
            try:
                visto = int(time.mktime(time.strptime(fila.get("hora", ""), "%Y-%m-%d %H:%M:%S")))
            except ValueError:
                visto = None
            if apuntar(ca, nota=fila.get("grupo") or fila.get("senal") or "", origen=os.path.basename(fichero), visto=visto):
                nuevos += 1
                mc = float(fila.get("capitalizacion_al_llamar") or fila.get("capitalizacion_disparo") or fila.get("capitalizacion") or 0)
                if visto and mc:
                    with cerrojo:                                           # la capitalización buena es la del momento en que se vio, no la de hoy
                        b = base(); b.execute("UPDATE contratos SET capitalizacion=? WHERE contrato=?", (mc, ca)); b.commit()
    return nuevos


def resumen():
    b = base()
    n, vivos = b.execute("SELECT count(*), sum(vivo) FROM contratos").fetchone()
    f = b.execute("SELECT count(*) FROM fotos").fetchone()[0]
    por = b.execute("SELECT origen, count(*) FROM contratos GROUP BY origen").fetchall()
    return "📒 Libreta: %d contratos (%d en seguimiento) · %d fotos\n%s" % (n, vivos or 0, f, "\n".join("• %s: %d" % x for x in por))


def ver(ca):
    b = base()
    c = b.execute("SELECT simbolo, visto, nota, origen, capitalizacion FROM contratos WHERE contrato=?", (ca,)).fetchone()
    if not c:
        return "Ese contrato no está en la libreta."
    fs = b.execute("SELECT hora, capitalizacion FROM fotos WHERE contrato=? ORDER BY hora", (ca,)).fetchall()
    mcs = [x[1] for x in fs if x[1]]
    base_mc = c[4] or (mcs[0] if mcs else 0) or 1
    return ("📒 <b>%s</b> · visto el %s (%s)%s\n   al verlo: %s\n   %d fotos · máximo %s (x%.2f) · mínimo %s (x%.2f) · ahora %s (x%.2f)" % (
        c[0], time.strftime("%d/%m %H:%M", time.localtime(c[1])), c[3], " · nota: " + c[2] if c[2] else "", dinero(base_mc), len(fs),
        dinero(max(mcs)), max(mcs) / base_mc, dinero(min(mcs)), min(mcs) / base_mc, dinero(mcs[-1]), mcs[-1] / base_mc)) if mcs else "Sin fotos todavía."


def exportar():
    ruta = os.path.join(AQUI, "libreta_exportada.csv")
    b = base()
    with open(ruta, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["contrato", "simbolo", "hora", "precio", "capitalizacion", "liquidez", "volumen_24h"])
        for r in b.execute("SELECT f.contrato, c.simbolo, f.hora, f.precio, f.capitalizacion, f.liquidez, f.volumen_24h FROM fotos f JOIN contratos c USING (contrato) ORDER BY f.contrato, f.hora"):
            w.writerow([r[0], r[1], time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(r[2]))] + list(r[3:]))
    try:
        requests.post(BOT + "sendDocument", data={"chat_id": MI_ID}, files={"document": open(ruta, "rb")}, timeout=120)
    except Exception:
        pass


def escuchar_bot():
    desde = 0
    while True:
        r = telegram("getUpdates", offset=desde, timeout=50, allowed_updates=["message"])
        for u in r.get("result") or []:
            desde = u["update_id"] + 1
            m = u.get("message") or {}
            chat = (m.get("chat") or {}).get("id")
            quien = str((m.get("from") or {}).get("id"))
            texto = (m.get("text") or "").strip()
            if not chat:
                continue
            if not MI_ID:
                telegram("sendMessage", chat_id=chat, text="Tu número de usuario es %s. Ponlo en TELEGRAM_MI_ID del .env y vuelve a arrancar." % quien)
                continue
            if quien != MI_ID:
                continue
            if texto.startswith("/libreta"):
                avisar(resumen())
            elif texto.startswith("/ver") and DIRECCION.search(texto):
                avisar(ver(DIRECCION.search(texto).group(0)))
            elif texto.startswith("/importa"):
                avisar("Importando… (un momento)"); n = importar(); avisar("Hecho: %d contratos nuevos.\n%s" % (n, resumen()))
            elif texto.startswith("/exporta"):
                exportar()
            elif DIRECCION.search(texto):
                ca = DIRECCION.search(texto).group(0)
                f = apuntar(ca, nota=texto.replace(ca, "").strip())
                if f is None:
                    avisar("Ese ya estaba apuntado. " + ver(ca))
                elif f is False:
                    avisar("No encuentro ese contrato en DexScreener.")
                else:
                    avisar("📒 Apuntado <b>%s</b>\n   capitalización %s · liquidez %s · volumen 24 h %s\n   Le haré una foto cada %d minutos durante %d horas." % (
                        f["simbolo"], dinero(f["mc"]), dinero(f["liq"]) if f["liq"] else "todavía en pump.fun", dinero(f["vol"]), CADA, HORAS))
            else:
                avisar("Pégame un contrato (y una nota si quieres). /libreta · /ver <contrato> · /importa · /exporta")
        if not r:
            time.sleep(3)


def main():
    if not TOKEN:
        print("Falta TELEGRAM_BOT_TOKEN en el fichero .env"); return
    base()
    print("Libreta en marcha. Pégale un contrato a tu bot. (Ctrl+C para parar)")
    threading.Thread(target=escuchar_bot, daemon=True).start()
    seguimiento()


if __name__ == "__main__":
    main()
