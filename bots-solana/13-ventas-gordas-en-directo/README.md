# 13 · Ventas gordas en directo

Vídeo 13 de la sección "Bots de Solana" del canal **Profesor Diógenes**.
Le pegas el contrato de un token de pump.fun y te avisa cuando alguien vende mucho de golpe: quién, qué parte del supply suelta,
cuánto SOL saca y cuánto le queda.

Órdenes: pegar un contrato (y un nombre) · `/lista` · `/quitar <contrato>` · `/umbral 2` (SOL) · `/supply 0.5` (% del supply)

## Lo que necesitas antes

- **Python 3.10 o más nuevo.**
- **Un bot de Telegram y su clave** (BotFather). Lo enseñamos en el Curso de Claude, capítulo 18.

## Instalar y arrancar

1. Copia `.env.ejemplo` como `.env` y pon la clave de tu bot.
2. `pip install -r requirements.txt` y `python3 ventas_gordas.py`.
3. Escríbele a tu bot: te dirá tu número de usuario. Ponlo en `TELEGRAM_MI_ID` y vuelve a arrancarlo. Así solo te contesta a ti.

Tiene que estar encendido todo el rato: el ordenador encendido o un servidor en la nube.
Si no sabes programar, pídeselo a Claude: "Instálame este bot de GitHub, pon la clave de mi bot de Telegram, arráncalo y que se levante solo si se cae".

## Lo que hay que saber

- Solo tokens de pump.fun (en la curva o ya en PumpSwap): se reconocen las ventas por el registro "Instruction: Sell".
- El nodo gratis contesta más o menos una pregunta por segundo: en un token con muchísimas ventas la cola se llena y las más
  viejas se tiran. Para eso, un nodo propio (`SOLANA_RPC` y `SOLANA_WS`).
- Lo que medimos (nuestros datos, agosto de 2026, 700 curvas): si sales "a ojo", el corte de pérdidas que tenías en la cabeza al −20 %
  se ejecuta de media al −40 % mirando cada 5 minutos, y al −62 % mirando cada hora. El precio no espera a que mires.
- Y la señal "vende el bundler" de GMGN (vídeo 9): después de ella solo el 14,3 % llegó a doblar.

**Esto no es consejo financiero.** Es una herramienta para mirar.
