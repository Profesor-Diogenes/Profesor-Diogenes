# Los datos de «Bots de Solana»

Estos son los datos con los que se han medido los números que se dicen en los vídeos de la serie [Bots de Solana](https://www.youtube.com/playlist?list=PLbRgpdRexHjI) del canal Profesor Diógenes. Están aquí para que los compruebes tú: bájalos, dáselos a tu IA y pregúntale lo que quieras.

El código de cada vídeo está en la rama principal: [bots-solana](https://github.com/Profesor-Diogenes/Profesor-Diogenes/tree/main/bots-solana).

Todo son datos públicos de la cadena de Solana y de fuentes abiertas (GMGN, GeckoTerminal, DexScreener, grupos públicos de Telegram), recogidos por nosotros. No hay ninguna clave ni dato personal. Las horas van en segundos Unix (UTC).

**Para abrirlos:** los `.gz` están comprimidos. En Python: `gzip.open("libreta.jsonl.gz", "rt")` y lees línea a línea; cada línea es un JSON. Con pandas: `pd.read_json("curvas.jsonl.gz", lines=True)` o `pd.read_csv("menciones_grupos.csv.gz", header=None)`.

## Qué es cada fichero

| Fichero | Filas | Qué es | Vídeos |
|---|---|---|---|
| `libreta.jsonl.gz` | 124.603 | Cada vez que vimos un token, su ficha tal como estaba EN ESE MOMENTO (agosto de 2026). Un mismo token puede salir varias veces. | 1, 14, 17, 18 |
| `curvas.jsonl.gz` | 3.214 | Qué hizo el precio de cada token DESPUÉS de verlo: velas de un minuto. | 14, 16, 17, 18 |
| `radiografias.jsonl.gz` | 2.951 | Los mayores holders de cada token en el momento de verlo, y quién les mandó el dinero. | 7, 22 |
| `senales.jsonl.gz` | 27.255 | Señales de GMGN (compra de «smart money», etc.) con la capitalización al saltar. | 9 |
| `velas_senales.jsonl.gz` | 1.850 | Velas de un minuto después de esas señales, por pool. | 9 |
| `menciones_grupos.csv.gz` | 1.921.363 | Cada vez que un grupo de llamadas de Telegram nombró un contrato, de agosto de 2025 a julio de 2026. Sin cabecera. | 6 |
| `llamadas_grupos_agosto.jsonl.gz` | 2.508 | Prueba en directo de dos grupos «buenos» del ranking, del 16 al 25 de agosto de 2026: la llamada y lo que hizo el precio después. | 6 |
| `contratos_en_x_noviembre.csv` | 2.275 | Contratos publicados en X que recogió el bot del vídeo 12 en su prueba de noviembre de 2026. | 12 |
| `libreta_68_contratos.csv`, `libreta_68_fotos.csv` | 68 | La libreta de la prueba de los vídeos 15 y 16: los contratos apuntados y las fotos que se les fue sacando. | 15, 16 |

Las 965 fichas del examen del vídeo 18 están con su código: [`bots-solana/18-bot-con-ia/examen.json`](https://github.com/Profesor-Diogenes/Profesor-Diogenes/tree/main/bots-solana/18-bot-con-ia).

## Las columnas

**`libreta.jsonl.gz`** — una ficha por avistamiento. Lo nuestro: `t0` (cuándo lo vimos), `edad_min` (minutos de vida al verlo), `cat` (`NUEVO`, `CASI` a punto de graduar o `GRADUADO`), `pasa` (si pasaba nuestra criba de entonces) y `fallos` (qué condiciones no cumplía). El resto es la ficha de GMGN tal cual: `address` (contrato), `symbol`, `name`, `market_cap`, `liquidity`, `price`, `volume_24h`, `swaps_24h`, `buys_24h`, `sells_24h`, `holder_count`, `top_10_holder_rate`, `creator` (el dev), `creator_created_count` (cuántos tokens ha creado), `dev_team_hold_rate`, `bundler_trader_amount_rate`, `rat_trader_amount_rate`, `fresh_wallet_rate`, `suspected_insider_hold_rate`, `top70_sniper_hold_rate`, `rug_ratio`, `is_wash_trading`, `burn_status`, `renounced_mint`, `renounced_freeze_account`, `fund_from_address` (quién le dio el dinero al dev), `launchpad`, `progress` (cuánto lleva de la curva), `twitter`, `x_user_follower`, `tg_call_count`… Los `_rate` van de 0 a 1.

**`curvas.jsonl.gz`** — `ca` (contrato), `t0` (cuándo lo vimos), `cat`, `pasa`, `symbol` y `velas`: lista de `[hora, apertura, máximo, mínimo, cierre, volumen en dólares]`, una por minuto, empezando DESPUÉS de `t0`.

**`radiografias.jsonl.gz`** — `ca`, `t0`, `mc_t0` (capitalización al verlo), `top` (los mayores holders con su porcentaje, etiquetas de GMGN y cuándo empezaron a tener), `maquinas` (las direcciones que no son personas: pool, curva, exchange), `wallets_reales`, `wallets_nuevas`, `wallets_regaladas`, `supply_regalado`, `origenes_compartidos` y `supply_en_grupos` (holders que recibieron el dinero de la misma billetera), `dev`.

**`senales.jsonl.gz`** — `ca`, `tipo` y `tipo_nombre` (qué señal), `trigger_at` (cuándo saltó), `trigger_mc` (capitalización al saltar), `primer_trigger_mc`, `veces` y `veces_por_tipo` (cuántas señales llevaba ese token), `pool`, `visto` (cuándo la leímos nosotros).

**`velas_senales.jsonl.gz`** — `pool`, `desde` y `velas` (mismo formato que en las curvas).

**`menciones_grupos.csv.gz`** — cuatro columnas, sin cabecera: contrato, grupo, hora, capitalización al nombrarlo (vacía si no la teníamos). Los grupos van numerados (`grupo_1`, `grupo_2`…): el mismo número es siempre el mismo grupo.

**`llamadas_grupos_agosto.jsonl.gz`** — `ca`, `grupo`, `puesto_ranking` y `wr_2x_minimo` (lo que decía el ranking de ese grupo), `ts_call` y `hora_call`, y lo medido después: `x_maximo_desde_call`, `x_minimo_desde_call`, `mc_ahora`, `liquidez`, `estado`.

## Cómo se mide sin hacer trampa

La trampa más fácil es usar algo que en el momento de decidir no podías saber. Para no caer:

1. La ficha es la del momento `t0`. Para decidir solo vale lo que hay en esa ficha.
2. El resultado se mira en las velas de DESPUÉS de `t0`. Se entra en la vela siguiente a verlo, no en la misma.
3. Se cuenta el coste: un 3 % al entrar y otro 3 % al salir (comisiones y lo que se mueve el precio al comprar). Por eso «doblar» no es que el precio llegue a x2, sino a x2,13 (2 dividido entre 0,97 al cuadrado).
4. Ventana fija de 6 horas. Si en ese tiempo no llega, no cuenta.
5. Solo tokens con volumen de verdad (más de 1.000 $). Con menos, el precio sube pero no puedes vender.
6. Para probar una regla: se busca en una parte de los datos y se comprueba en OTRA parte, posterior en el tiempo. Si solo funciona donde la buscaste, es casualidad.

El programa que hace esta medición está en [`bots-solana/16-medir-sin-trampa`](https://github.com/Profesor-Diogenes/Profesor-Diogenes/tree/main/bots-solana/16-medir-sin-trampa).

## Lo que NO son estos datos

No son todos los tokens de Solana ni todos los días: son los que vimos nosotros, en las fechas que se dicen. Las fichas con resultado medido son pocos días de agosto de 2026. Sirven para comprobar lo que decimos en los vídeos y para que hagas tus pruebas, no para sacar una regla y jugarte el dinero.

Esto no es consejo financiero. Es lo que miden nuestros datos.
