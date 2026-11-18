#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analizar un contrato de Solana con la API de GMGN.
Canal de YouTube: Profesor Diógenes · sección "Bots de Solana", vídeo 1.

    python3 analizar.py <DIRECCION_DEL_CONTRATO>

Saca de un contrato:
  1. La ficha: precio, capitalización, liquidez, holders, edad.
  2. La seguridad: si pueden fabricar más tokens o congelarte, top 10, snipers, bundlers, insiders.
  3. Contraste con DexScreener (gratis, sin clave): si la liquidez no cuadra, cuidado.
  4. Quién hay dentro: top holders con sus etiquetas y QUIÉN LES MANDÓ EL DINERO.
     Varias billeteras financiadas desde el mismo sitio = probablemente el mismo dueño.
  5. Quién ha ganado dinero, quién tiene tokens que nunca compró y quién se compra y se vende a sí mismo.
  6. El dev: cuántos tokens ha lanzado y quién le pagó la billetera.

Tu clave va en el fichero .env (copia .env.ejemplo). Sin clave usa la clave pública de
pruebas de GMGN, que vale para probar pero no para uso real.

Esto NO es consejo financiero. Es una herramienta para mirar, no para decidir por ti.
"""
import os, sys, time, uuid, json
import requests

HOST = "https://openapi.gmgn.ai"
CLAVE_DE_PRUEBAS = "gmgn_solbscbaseethmonadtron"   # la publica de GMGN, solo para probar


def cargar_env(ruta=".env"):
    if not os.path.exists(ruta):
        return
    for linea in open(ruta, encoding="utf-8"):
        linea = linea.strip()
        if linea and not linea.startswith("#") and "=" in linea:
            k, v = linea.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


cargar_env(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
CLAVE = os.environ.get("GMGN_API_KEY") or CLAVE_DE_PRUEBAS

# Plan gratis de GMGN: cubo de 5 unidades que se rellena a 5 por segundo.
# token info / security pesan 1; holders / traders pesan 5. Vamos despacio a proposito.
PESO = {"/v1/token/info": 1, "/v1/token/security": 1,
        "/v1/market/token_top_holders": 5, "/v1/market/token_top_traders": 5,
        "/v1/user/created_tokens": 2}
_ultima = [0.0]


def gmgn(ruta, **parametros):
    """Una peticion a GMGN. Devuelve el campo 'data' o None."""
    espera = PESO.get(ruta, 3) / 5.0 - (time.time() - _ultima[0])
    if espera > 0:
        time.sleep(espera)
    q = dict(parametros, timestamp=int(time.time()), client_id=str(uuid.uuid4()))
    for intento in range(3):
        try:
            r = requests.get(HOST + ruta, params=q, timeout=25,
                             headers={"X-APIKEY": CLAVE, "User-Agent": "profesor-diogenes"})
            _ultima[0] = time.time()
            if r.status_code == 429:
                # te has pasado: GMGN te dice cuando puedes volver. Insistir alarga el castigo.
                print("   (GMGN pide calma: esperando 10 s)")
                time.sleep(10)
                q.update(timestamp=int(time.time()), client_id=str(uuid.uuid4()))
                continue
            d = r.json()
            if str(d.get("code")) not in ("0", "None"):
                print("   (GMGN contesta %s: %s)" % (d.get("code"), d.get("message") or d.get("error")))
                return None
            return d.get("data")
        except Exception as e:
            print("   (fallo de red: %s)" % str(e)[:60])
            time.sleep(2)
    return None


def num(x, d=0.0):
    try:
        return float(x)
    except Exception:
        return d


def dinero(x):
    s = "-" if x < 0 else ""
    x = abs(x)
    if x >= 1e6: return "%s%.2f M$" % (s, x / 1e6)
    if x >= 1e3: return "%s%.1f K$" % (s, x / 1e3)
    return "%s%.0f $" % (s, x)


def lista(d):
    if isinstance(d, dict):
        return d.get("list") or []
    return d or []


def quien_le_pago(w):
    """Quien le mando el primer SOL a esta billetera."""
    nt = w.get("native_transfer") or {}
    if isinstance(nt, dict):
        return nt.get("from_address") or nt.get("address")
    return None


def main(ca):
    print("═" * 72)
    print(" ANALIZANDO %s" % ca)
    print("═" * 72)

    info = gmgn("/v1/token/info", chain="sol", address=ca) or {}
    seg = gmgn("/v1/token/security", chain="sol", address=ca) or {}
    if not (info.get("symbol") or num(info.get("total_supply"))):
        print(" GMGN no conoce ese contrato (o es una billetera, no un token).")
        return

    # ── 1. LA FICHA ─────────────────────────────────────────────────────
    precio = num((info.get("price") or {}).get("price"))
    mc = precio * num(info.get("total_supply"))          # GMGN no la da: hay que calcularla
    liq = num(info.get("liquidity"))
    nacio = num(info.get("open_timestamp") or info.get("creation_timestamp"))
    horas = (time.time() - nacio) / 3600 if nacio else 0
    print("\n[1] LA FICHA")
    print("    %s (%s) · %.1f horas de vida" % (info.get("symbol"), info.get("name"), horas))
    print("    capitalización %s · liquidez %s · holders %s" % (
        dinero(mc), dinero(liq), (info.get("stat") or {}).get("holder_count") or info.get("holder_count")))

    # ── 2. LA SEGURIDAD ─────────────────────────────────────────────────
    print("\n[2] LA SEGURIDAD")
    si = lambda v: str(v).lower() in ("true", "1")
    print("    ¿pueden fabricar más tokens? %s" % ("NO" if si(seg.get("renounced_mint")) else "SÍ  <- pueden diluirte"))
    print("    ¿pueden congelar tu billetera? %s" % ("NO" if si(seg.get("renounced_freeze_account")) else "SÍ  <- no podrías vender"))
    print("    top 10 tiene el %.1f%% · snipers: %s · bundlers mueven el %.1f%% · insiders el %.1f%%" % (
        100 * num(seg.get("top_10_holder_rate")),
        seg.get("sniper_count") if seg.get("sniper_count") is not None else "sin dato",
        100 * num(seg.get("bundler_trader_amount_rate")), 100 * num(seg.get("rat_trader_amount_rate"))))

    # ── 3. CONTRASTE CON DEXSCREENER ────────────────────────────────────
    print("\n[3] ¿CUADRA CON DEXSCREENER?")
    try:
        pares = requests.get("https://api.dexscreener.com/latest/dex/tokens/" + ca, timeout=20).json().get("pairs") or []
    except Exception:
        pares = []
    liq_ds = sum(num((p.get("liquidity") or {}).get("usd")) for p in pares)
    vol_ds = sum(num((p.get("volume") or {}).get("h24")) for p in pares)
    print("    GMGN dice liquidez %s · DexScreener dice %s (%d pools) · volumen 24 h %s" % (
        dinero(liq), dinero(liq_ds), len(pares), dinero(vol_ds)))
    if liq_ds < 1000 and vol_ds > 10000:
        print("    🔴 MUCHO VOLUMEN Y CASI NADA DE LIQUIDEZ: entras y no sales.")
    elif max(liq, liq_ds) > 0 and abs(liq - liq_ds) > 0.5 * max(liq, liq_ds):
        print("    🟡 NO CUADRAN. Fíate del que menos dice y mira por qué.")
    else:
        print("    🟢 cuadran")

    # ── 4. QUIÉN HAY DENTRO ─────────────────────────────────────────────
    print("\n[4] QUIÉN HAY DENTRO (top holders)")
    holders = lista(gmgn("/v1/market/token_top_holders", chain="sol", address=ca, limit=50))
    # fuera las "maquinas": la pool del DEX y la curva del launchpad no son personas
    pools = {p.get("pairAddress") for p in pares if p.get("pairAddress")}
    def es_maquina(w):
        if w.get("address") in pools or w.get("account_address") in pools:
            return True
        n = (w.get("name") or "").lower()
        return any(x in n for x in ("pool", "vault", "curve", "amm", "bonding", "liquidity"))
    maquinas = [w for w in holders if es_maquina(w)]
    personas = [w for w in holders if not es_maquina(w)]
    if maquinas:
        print("    (apartadas %d direcciones que son la pool o la curva: %.1f%% del supply)" % (
            len(maquinas), 100 * sum(num(w.get("amount_percentage")) for w in maquinas)))
    for w in personas[:10]:
        etiquetas = ",".join((w.get("tags") or []) + (w.get("maker_token_tags") or [])) or "-"
        print("    %s… %6.2f%%  %-28s le pagó: %s" % (
            (w.get("address") or "")[:10], 100 * num(w.get("amount_percentage")),
            etiquetas[:28], (quien_le_pago(w) or "?")[:10]))
    grupos = {}
    for w in personas:
        o = quien_le_pago(w)
        if o:
            grupos.setdefault(o, []).append(num(w.get("amount_percentage")))
    hermanas = {o: v for o, v in grupos.items() if len(v) > 1}
    if hermanas:
        print("    ⚠️  BILLETERAS HERMANAS (mismo pagador):")
        for o, v in sorted(hermanas.items(), key=lambda x: -sum(x[1]))[:5]:
            print("       %s… pagó a %d billeteras que juntas tienen el %.2f%%" % (o[:12], len(v), 100 * sum(v)))
    else:
        print("    no se ven billeteras con el mismo pagador en el top")
    regaladas = [w for w in personas if w.get("transfer_in") and num(w.get("buy_volume_cur")) <= 1]
    if regaladas:
        print("    ⚠️  %d billeteras tienen el %.2f%% SIN HABERLO COMPRADO (se lo pasaron)" % (
            len(regaladas), 100 * sum(num(w.get("amount_percentage")) for w in regaladas)))

    # ── 5. QUIÉN HA GANADO Y QUIÉN HACE TRAMPA ──────────────────────────
    print("\n[5] QUIÉN HA GANADO DINERO AQUÍ")
    traders = lista(gmgn("/v1/market/token_top_traders", chain="sol", address=ca, limit=100, order_by="profit"))
    for w in sorted(traders, key=lambda w: -num(w.get("profit")))[:5]:
        if num(w.get("profit")) <= 0:
            break
        print("    %s…  ganó %9s  (metió %s, sacó %s)" % (
            (w.get("address") or "")[:10], dinero(num(w.get("profit"))),
            dinero(num(w.get("buy_volume_cur"))), dinero(num(w.get("sell_volume_cur")))))
    gana = sum(num(w.get("profit")) for w in traders if num(w.get("profit")) > 0)
    pierde = sum(num(w.get("profit")) for w in traders if num(w.get("profit")) < 0)
    print("    en el top 100: se ganó %s y se perdió %s" % (dinero(gana), dinero(abs(pierde))))
    vende_sin_comprar = [w for w in traders if num(w.get("buy_volume_cur")) <= 1 and num(w.get("sell_volume_cur")) > 50]
    if vende_sin_comprar:
        print("    ⚠️  %d billeteras VENDEN sin haber comprado: sacaron %s" % (
            len(vende_sin_comprar), dinero(sum(num(w.get("sell_volume_cur")) for w in vende_sin_comprar))))
    lavado = [w for w in traders
              if num(w.get("buy_volume_cur")) > 200 and num(w.get("buy_tx_count_cur")) >= 3
              and num(w.get("sell_tx_count_cur")) >= 3
              and 0.85 < num(w.get("sell_volume_cur")) / num(w.get("buy_volume_cur"), 1) < 1.18
              and abs(num(w.get("profit"))) < 0.08 * num(w.get("buy_volume_cur"))]
    if lavado:
        print("    ⚠️  %d billeteras compran y venden lo mismo sin ganar ni perder: %s de volumen de mentira" % (
            len(lavado), dinero(sum(num(w.get("buy_volume_cur")) + num(w.get("sell_volume_cur")) for w in lavado))))

    # ── 6. EL DEV ───────────────────────────────────────────────────────
    print("\n[6] EL DEV")
    dev = info.get("dev") or {}
    creador = dev.get("creator_address") or seg.get("creator")
    print("    creador: %s" % (creador or "?"))
    print("    tokens lanzados antes: %s · le pagó la billetera: %s" % (
        dev.get("creator_open_count") or "?", dev.get("fund_from") or "?"))
    if dev.get("twitter_name_change_history"):
        print("    ⚠️  el Twitter del proyecto ha cambiado de nombre %d veces" % len(dev["twitter_name_change_history"]))

    print("\n" + "─" * 72)
    print(" Esto es lo que se puede MIRAR. Que algo esté limpio no significa que vaya a subir.")
    print(" No es consejo financiero.")
    print("─" * 72)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 analizar.py <DIRECCION_DEL_CONTRATO>")
        sys.exit(1)
    main(sys.argv[1].strip())
