# 17 · Bot en papel

Vídeo 17 de la sección "Bots de Solana" del canal **Profesor Diógenes**.
Compra y vende **de mentira** con tus reglas y te dice cuánto habrías ganado o perdido. No tiene billetera y no puede comprar nada de verdad.

Órdenes: pegar un contrato (lo "compra") · `/plan 0.2 2 50` (SOL por entrada · vender en x2 · cortar si cae un 50 %) · `/cartera` · `/balance` · `/cierra <contrato>`

## Lo que necesitas antes

- **Python 3.10 o más nuevo.**
- **Un bot de Telegram y su clave** (BotFather). Lo enseñamos en el Curso de Claude, capítulo 18.

## Instalar y arrancar

1. Copia `.env.ejemplo` como `.env` y pon la clave de tu bot.
2. `pip install -r requirements.txt` y `python3 papel.py`.
3. Escríbele a tu bot: te dirá tu número de usuario. Ponlo en `TELEGRAM_MI_ID` y vuelve a arrancarlo. Así solo te contesta a ti.

Tiene que estar encendido todo el rato: el ordenador encendido o un servidor en la nube.
Si no sabes programar, pídeselo a Claude: "Instálame este bot de GitHub, pon la clave de mi bot de Telegram, arráncalo y que se levante solo si se cae".

## Lo que hay que saber

- Precios de DexScreener cada 30 segundos. Entre mirada y mirada el precio puede saltarse tu corte: se vende al precio que haya.
- Descuenta `COMISION` (3 % por defecto) en cada compra y en cada venta. Todo queda en `operaciones.csv`.
- Lo que medimos (nuestros datos, agosto de 2026, 574 curvas): con 0,2 SOL, objetivo doblar y corte al −50 %, ganar son +0,188 SOL y perder −0,10:
  hay que acertar el **34,6 %** para no perder. A ciegas se acertaba entre el 17 % y el 25 %. Probamos 5 objetivos por 5 cortes: las 100 combinaciones perdían.
- De los que doblan, si aguantas en vez de vender: el 78 % acaba por debajo del doble y el precio típico final es x0,44.

**Esto no es consejo financiero.** Es una herramienta para mirar.
