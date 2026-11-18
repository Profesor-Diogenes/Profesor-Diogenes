# 04 · Seguir billeteras de Solana en directo (avisos a tu Telegram)

Vídeo 4 de la sección "Bots de Solana" del canal **Profesor Diógenes**.
En el vídeo 3 analizábamos una billetera. Aquí la **vigilamos en directo**: en cuanto compra o vende, tu bot de Telegram te avisa
con qué token, cuánto ha pagado, la capitalización y la liquidez.

## Cómo se usa (desde Telegram)

- Le pegas una billetera → la empieza a vigilar.
- Le pegas una billetera y un nombre detrás (`9ncm3Mfx… el creador`) → la vigila con ese nombre.
- `/lista` → las que estás vigilando.
- `/quitar <billetera>` → deja de vigilarla.

Para qué sirve: has analizado una billetera con el bot del vídeo 3 y quieres saber qué hace sin estar mirando la pantalla.
Te llega al móvil en el momento.

## Instalar y arrancar

1. Crea tu bot en BotFather (lo explicamos en el Curso de Claude del canal, capítulo 18) y copia su clave.
2. Copia `.env.ejemplo` como `.env` y pega la clave en `TELEGRAM_BOT_TOKEN`.
3. `pip install -r requirements.txt` y `python3 vigia.py`. Escríbele y te dirá tu número de usuario: ponlo en `TELEGRAM_MI_ID`
   y vuelve a arrancarlo. Así solo te contesta a ti.

**Tiene que estar encendido todo el rato** para avisarte: el ordenador encendido o un servidor en la nube.
Si no sabes programar, pídeselo a Claude: "Instálame este bot de GitHub, pon la clave de mi bot de Telegram, arráncalo y que se levante solo si se cae".

## Cómo funciona por dentro

- Abre una conexión con el nodo público de Solana que se queda abierta (WebSocket) y le dice: "avísame de todo lo que toque esta billetera".
  Es gratis y no pide clave.
- Cuando llega algo, pide la operación entera, mira cuánto SOL (o USDC, o qué otro token) entró o salió, le pregunta a DexScreener
  el nombre y el precio del token y te lo manda.
- Si la conexión se cae, se vuelve a conectar sola. La lista de billeteras se guarda en `vigiladas.json`.

## Lo que hay que saber

- El nodo público deja unas **100 preguntas cada 10 segundos por IP**. El programa usa UNA sola conexión con una suscripción por billetera: con una conexión por billetera, el nodo gratis nos echaba a partir de 5 o 6.
  Con más de 30 billeteras, o con billeteras que operan cada segundo (bots), te quedas corto: usa tu propio nodo (`SOLANA_RPC` y `SOLANA_WS`).
- Muchas billeteras "que ganan" son máquinas que hacen cientos de operaciones por minuto, casi siempre de céntimos. Por eso
  no se avisa de movimientos de menos de `MINIMO_SOL` (0,05 SOL por defecto).
- Que te avise rápido no significa que llegues a tiempo: cuando te llega el aviso, el precio ya se ha movido.

**Esto no es consejo financiero.** Es una herramienta para mirar.
