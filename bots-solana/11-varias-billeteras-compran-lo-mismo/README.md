# 11 · Varias de tus billeteras compran el mismo token

Vídeo 11 de la sección "Bots de Solana" del canal **Profesor Diógenes**.
Es el vigía del vídeo 4 con una pieza más: cuando 2 o más billeteras **distintas** de las que sigues compran el mismo token
dentro de una ventana de horas, te avisa con quién ha comprado y hace cuánto.

Órdenes: pegar una billetera (y un nombre) · `/lista` · `/quitar <billetera>` · `/minimo 3` · `/ventana 6` · `/sueltas no`

## Lo que necesitas antes

- **Python 3.10 o más nuevo.**
- **Un bot de Telegram y su clave** (BotFather). Lo enseñamos en el Curso de Claude, capítulo 18.

## Instalar y arrancar

1. Copia `.env.ejemplo` como `.env` y pon la clave de tu bot.
2. `pip install -r requirements.txt` y `python3 coincidencias.py`.
3. Escríbele a tu bot: te dirá tu número de usuario. Ponlo en `TELEGRAM_MI_ID` y vuelve a arrancarlo. Así solo te contesta a ti.

Tiene que estar encendido todo el rato: el ordenador encendido o un servidor en la nube.
Si no sabes programar, pídeselo a Claude: "Instálame este bot de GitHub, pon la clave de mi bot de Telegram, arráncalo y que se levante solo si se cae".

## Lo que hay que saber

- Usa el nodo público de Solana (gratis, sin clave): una sola conexión con una suscripción por billetera.
- Lo que medimos (nuestros datos, agosto de 2026, 694 curvas): con 0 billeteras de "dinero listo" dentro, llegaban a doblar el 21,5 %;
  con 2 o 3, el 31,6 %; con 4 o más, el 30,4 %. Suma algo, pero más billeteras no es mejor, y el 78 % de los tokens no tenía ninguna.
- Y en los grupos de Telegram (vídeo 6): que lo llamen dos no cambia nada. El segundo llega porque el precio ya se movió.

**Esto no es consejo financiero.** Es una herramienta para mirar.
