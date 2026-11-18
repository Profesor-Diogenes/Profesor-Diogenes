# 09 · Las señales de GMGN en tu Telegram (y cómo medir si sirven)

Vídeo 9 de la sección "Bots de Solana" del canal **Profesor Diógenes**.
GMGN avisa en directo de cosas que pasan en un token. Este bot te pasa las que elijas a Telegram y las apunta para que las midas.

| orden | señal | qué es |
|---|---|---|
| `smart` | compra el dinero listo | compra una billetera que GMGN considera "smart money" |
| `kol` | compra un KOL | compra un influencer conocido |
| `bundler` | vende el bundler | venden los bots que compraron en el lanzamiento |
| `cto` | CTO | la comunidad se queda el token que abandonó el creador |

## Cómo se usa (desde tu bot)

`/senales` · `/pon kol` · `/quita bundler` · `/minimo 50000` (capitalización mínima en el disparo, en $) · `/mide`

Cada señal trae la capitalización **en el instante del disparo**, que es lo que hace falta para medir sin trampa.
Se apunta en `senales.csv`. `/mide` compara la capitalización de ahora (DexScreener) con la del disparo, solo en las de hace más de 3 horas.

## Lo que necesitas antes

- **Python 3.10 o más nuevo** y **un bot de Telegram** (BotFather; Curso de Claude, capítulo 18).
- **Clave de GMGN** (opcional): sin clave usa la pública de pruebas. La tuya, gratis en https://gmgn.ai/ai

## Instalar y arrancar

1. Copia `.env.ejemplo` como `.env` y pon la clave de tu bot.
2. `pip install -r requirements.txt` y `python3 senales.py`. Tiene que estar encendido todo el rato.

## Lo que medimos (nuestros datos, 19 al 25 de agosto de 2026, 3 horas desde el disparo)

| señal | n | llega a doblar | pierde la mitad | precio típico a las 3 h |
|---|---|---|---|---|
| compra un KOL | 44 | 31,8 % | 65,9 % | x0,41 |
| compra el dinero listo | 44 | 29,5 % | 45,5 % | x0,53 |
| vende el bundler | 691 | 14,3 % | 31,0 % | x0,81 |
| CTO | 173 | 11,6 % | 56,1 % | x0,49 |

De KOL y dinero listo solo hay 44 de cada una: es una sospecha, no una ley. Se apuntaron más de 27.000 señales; las de la tabla
son las que se pudieron medir con velas.

**Esto no es consejo financiero.** Es una herramienta para mirar.
