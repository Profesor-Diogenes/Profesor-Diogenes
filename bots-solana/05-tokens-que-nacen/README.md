# 05 · Los tokens que nacen, en directo (avisos a tu Telegram con TUS reglas)

Vídeo 5 de la sección "Bots de Solana" del canal **Profesor Diógenes**.
En pump.fun nacen tokens sin parar. Este bot los escucha en directo y solo te avisa de los que cumplen tus reglas:
palabras en el nombre, cuánto compra el creador al nacer y cuántos tokens ha lanzado antes ese creador.

## Las reglas (desde Telegram)

- `/reglas` → te enseña las que tienes.
- `/palabras gato,perro` → solo si el nombre o el ticker lleva alguna (vacío = cualquiera).
- `/compra 1` → solo si el creador se compra él mismo al nacer al menos 1 SOL (0 = da igual). Por defecto, 0,5.
- `/historial 0 10` → solo si el creador ha lanzado antes entre 0 y 10 tokens.
- `/pausa` y `/sigue` → para y reanuda los avisos.
- `/cuentas` → cuántos han nacido desde que lo arrancaste y de cuántos te ha avisado.

Cada aviso trae: el ticker y el nombre, lo que compra el creador al nacer, cuántos tokens ha lanzado antes,
cuántos de esos salieron de la curva de pump.fun, su mejor token, la dirección y los enlaces.

## Instalar y arrancar

1. Crea tu bot en BotFather (lo explicamos en el Curso de Claude del canal, capítulo 18) y copia su clave.
2. Copia `.env.ejemplo` como `.env` y pega la clave en `TELEGRAM_BOT_TOKEN`.
3. `pip install -r requirements.txt` y `python3 nacimientos.py`. Escríbele y te dirá tu número de usuario: ponlo en `TELEGRAM_MI_ID`
   y vuelve a arrancarlo.

Tiene que estar encendido todo el rato: el ordenador encendido o un servidor en la nube.
Si no sabes programar: "Instálame este bot de GitHub, pon la clave de mi bot de Telegram, arráncalo y que se levante solo si se cae".

## Cómo funciona por dentro

- Una sola conexión abierta (WebSocket) con el nodo público de Solana, escuchando el programa de pump.fun. Gratis y sin clave.
- Cada operación de pump.fun deja escrito en sus registros un "evento". El de **nacimiento** trae el nombre, el ticker,
  la dirección y el creador. El de **compra** trae quién compra y cuánto. Se leen directamente del aviso:
  no hace falta preguntar nada más al nodo, así que no hay límite de velocidad que te frene.
- El historial del creador se pregunta a GMGN (`/v1/user/created_tokens`), que con la clave de pruebas contesta.

## Lo que hay que saber

- Nacen del orden de diez tokens por minuto. Sin reglas, tu móvil no para.
- Que el creador compre mucho al nacer no dice si el token va a ir bien: puede ser para vender encima de ti.
- Muchos creadores lanzan cientos de tokens. Mira cuántos salieron de la curva antes de emocionarte.

**Esto no es consejo financiero.** Es una herramienta para mirar.
