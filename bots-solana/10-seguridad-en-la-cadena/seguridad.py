#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
La seguridad de un token de Solana, comprobada TÚ MISMO en la cadena, sin fiarte de nadie:
¿puede el creador fabricar más tokens? ¿puede congelar tu billetera? ¿lleva trampas escondidas
(impuesto, delegado que te los puede quitar)? ¿cuánto tienen los 10 primeros? ¿la liquidez está quemada?
Canal de YouTube: Profesor Diógenes · sección "Bots de Solana", vídeo 10.

    python3 seguridad.py <contrato>          (o con el bot: python3 bot.py)

De dónde sale cada cosa:
  - autoridades del token y extensiones (Token-2022)  -> nodo público de Solana (getAccountInfo)
  - los mayores holders                                 -> nodo (getTokenLargestAccounts) y si corta, GMGN
  - liquidez quemada o bloqueada                        -> GMGN (vale la clave pública de pruebas), para contrastar
Esto NO es consejo financiero. Es una herramienta para mirar.
"""
import os, sys, time, uuid
import requests

HOST = "https://openapi.gmgn.ai"
CLAVE_DE_PRUEBAS = "gmgn_solbscbaseethmonadtron"


def cargar_env(ruta=None):
    ruta = ruta or os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(ruta):
        return
    for linea in open(ruta, encoding="utf-8"):
        linea = linea.strip()
        if linea and not linea.startswith("#") and "=" in linea:
            k, v = linea.split("=", 1)
            if v.strip():
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


cargar_env()
CLAVE = os.environ.get("GMGN_API_KEY") or CLAVE_DE_PRUEBAS
NODO = os.environ.get("SOLANA_RPC", "https://api.mainnet-beta.solana.com")
TOKEN_2022 = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"   # pragma: allowlist secret
_ultima = [0.0]

# Extensiones de Token-2022 que pueden ir contra ti
PELIGROSAS = {
    "permanentDelegate": "DELEGADO PERMANENTE: alguien puede mover o quemar tus tokens sin tu permiso",
    "transferHook": "GANCHO DE TRANSFERENCIA: un programa del creador decide si puedes mover tus tokens",
    "transferFeeConfig": "IMPUESTO en cada compra y venta",
    "nonTransferable": "NO SE PUEDE TRANSFERIR: no lo podrás vender",
    "pausableConfig": "SE PUEDE PAUSAR: el creador puede parar todas las operaciones",
    "defaultAccountState": "las billeteras nacen CONGELADAS por defecto",
}


def nodo(metodo, params):
    for intento in range(4):
        espera = 1.1 - (time.time() - _ultima[0])
        if espera > 0:
            time.sleep(espera)
        _ultima[0] = time.time()
        try:
            d = requests.post(NODO, json={"jsonrpc": "2.0", "id": 1, "method": metodo, "params": params}, timeout=20).json()
        except Exception:
            time.sleep(2); continue
        if d.get("error"):
            if d["error"].get("code") in (429, -32429) or "rate" in str(d["error"]).lower():
                time.sleep(5); continue
            return None
        return d.get("result")
    return None


def gmgn(ruta, **parametros):
    q = dict(parametros, timestamp=int(time.time()), client_id=str(uuid.uuid4()))
    try:
        d = requests.get(HOST + ruta, params=q, timeout=25, headers={"X-APIKEY": CLAVE, "User-Agent": "profesor-diogenes"}).json()
        return d.get("data") if str(d.get("code")) == "0" else None
    except Exception:
        return None


def corto(a):
    return (a or "?")[:6] + "…" + (a or "?")[-4:]


def main(ca):
    t0 = time.time()
    cuenta = nodo("getAccountInfo", [ca, {"encoding": "jsonParsed"}])
    v = (cuenta or {}).get("value") or {}
    datos = ((v.get("data") or {}).get("parsed") or {}).get("info") or {}
    if not datos or "decimals" not in datos:
        print("Eso no es un token de Solana (o el nodo no contesta)."); return
    rojo, ambar = [], []
    print("SEGURIDAD EN LA CADENA · %s\n" % ca)

    print("[1] ¿PUEDE FABRICAR MÁS TOKENS? (autoridad de acuñar)")
    if datos.get("mintAuthority"):
        print("    ❌ SÍ. %s puede crear tokens nuevos cuando quiera y diluirte." % corto(datos["mintAuthority"])); rojo.append("puede acuñar")
    else:
        print("    ✅ No. Nadie puede crear más: la autoridad está renunciada.")

    print("\n[2] ¿PUEDE CONGELAR TU BILLETERA? (autoridad de congelar)")
    if datos.get("freezeAuthority"):
        print("    ❌ SÍ. %s puede congelar tus tokens y no podrías venderlos." % corto(datos["freezeAuthority"])); rojo.append("puede congelar")
    else:
        print("    ✅ No. La autoridad está renunciada.")

    print("\n[3] ¿LLEVA TRAMPAS ESCONDIDAS? (extensiones del token)")
    if v.get("owner") == TOKEN_2022:
        ext = datos.get("extensions") or []
        nombres = [e.get("extension") for e in ext]
        malas = [n for n in nombres if n in PELIGROSAS]
        print("    Es un token del programa nuevo (Token-2022), con extensiones: %s" % (", ".join(nombres) or "ninguna"))
        for n in malas:
            print("    ❌ %s" % PELIGROSAS[n]); rojo.append(n)
        if not malas:
            print("    ✅ Ninguna de las peligrosas.")
    else:
        print("    ✅ Es un token del programa de siempre: no admite extensiones.")

    print("\n[4] ¿CUÁNTO TIENEN LOS 10 PRIMEROS?")
    total = float(datos.get("supply") or 0) / (10 ** int(datos.get("decimals") or 0)) or 1
    grandes = (nodo("getTokenLargestAccounts", [ca]) or {}).get("value")
    if grandes:
        lista = [(g["address"], 100 * float(g.get("uiAmount") or 0) / total) for g in grandes]
        fuente = "nodo (son cuentas de token: la primera suele ser la curva o el pool)"
    else:
        h = gmgn("/v1/market/token_top_holders", chain="sol", address=ca, limit=20)
        h = (h.get("list") if isinstance(h, dict) else h) or []
        lista = [(x.get("address"), 100 * float(x.get("amount_percentage") or 0)) for x in h]
        fuente = "GMGN (el nodo público corta esta pregunta a menudo)"
    diez = lista[:10]
    print("    Los 10 primeros tienen el %.1f %% (%s):" % (sum(p for _, p in diez), fuente))
    for a, p in diez[:5]:
        print("       %5.2f %%  %s" % (p, corto(a)))

    print("\n[5] ¿LA LIQUIDEZ ESTÁ QUEMADA O BLOQUEADA? (según GMGN)")
    seg = gmgn("/v1/token/security", chain="sol", address=ca) or {}
    quema = seg.get("burn_status") or ""
    if quema == "burn":
        print("    ✅ Quemada: el creador no puede sacar la liquidez.")
    elif seg:
        print("    ⚠ No consta quemada (%s). Si sigue en la curva de pump.fun es normal: allí no hay liquidez que sacar." % (quema or "sin dato"))
        ambar.append("liquidez no quemada")
    else:
        print("    (GMGN no contesta)")

    print("\nVEREDICTO")
    if rojo:
        print("    ❌ NO: %s. Con esto no hay nada más que mirar." % ", ".join(rojo))
    else:
        print("    ✅ Pasa lo básico%s." % (" (ojo: %s)" % ", ".join(ambar) if ambar else ""))
        print("    Pero pasar lo básico no significa nada bueno: lo pasan casi todos, también los que acaban a cero.")
    print("\n(%.0f s · nodo público de Solana + GMGN · no es consejo financiero)" % (time.time() - t0))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("uso: python3 seguridad.py <contrato>"); sys.exit(1)
    main(sys.argv[1])
