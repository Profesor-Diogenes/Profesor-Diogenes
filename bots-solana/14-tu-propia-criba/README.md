# 14 · Tu propia criba

Vídeo 14 de la sección "Bots de Solana" del canal **Profesor Diógenes**.
Cada pocos minutos mira los tokens con más movimiento en GMGN, se queda con los que cumplen tus reglas y te los manda.
Cada uno que pasa se apunta en `cribados.csv` con su capitalización de ese momento, para medirlo después (vídeo 16).

Órdenes: `/criba` · `/pon mc 25000 600000` · `/pon liquidez 5000` · `/pon volumen 50000` · `/pon holders 150 400` · `/ahora` · `/pausa` · `/sigue`

Reglas fijas: solo pump.fun, nadie puede fabricar más tokens ni congelarte, liquidez quemada.

## Lo que necesitas antes

- **Python 3.10 o más nuevo.**
- **Un bot de Telegram y su clave** (BotFather). Lo enseñamos en el Curso de Claude, capítulo 18.

## Instalar y arrancar

1. Copia `.env.ejemplo` como `.env` y pon la clave de tu bot.
2. `pip install -r requirements.txt` y `python3 criba.py`.
3. Escríbele a tu bot: te dirá tu número de usuario. Ponlo en `TELEGRAM_MI_ID` y vuelve a arrancarlo. Así solo te contesta a ti.

Tiene que estar encendido todo el rato: el ordenador encendido o un servidor en la nube.
Si no sabes programar, pídeselo a Claude: "Instálame este bot de GitHub, pon la clave de mi bot de Telegram, arráncalo y que se levante solo si se cae".

## Lo que hay que saber

- Usa la lista de tokens con más movimiento de GMGN (vale la clave pública de pruebas; la tuya, gratis en https://gmgn.ai/ai).
- Lo que medimos (nuestros datos, agosto de 2026): esta criba, medida la primera noche, daba un 56 % de tokens que doblaban contra un 7 % del resto.
  Era mentira a medias: parte de los "ganadores" eran pools sin volumen. Medido solo con volumen real, **34 %** (241 tokens).
- La mejor señal que encontramos: entre 150 y 400 holders doblaba el 35,1 % (base 24,9 %). Menos de 150, aún no le importa a nadie; más de 400, llegas tarde.
- Y aun así: comprando a ciegas lo que pasa la criba, con objetivo de doblar y corte al −50 %, hace falta acertar el 34,6 % solo para no perder.

**Esto no es consejo financiero.** Es una herramienta para mirar.
