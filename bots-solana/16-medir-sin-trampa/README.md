# 16 · Medir sin hacerse trampas

Vídeo 16 de la sección "Bots de Solana" del canal **Profesor Diógenes**.
Lee la libreta del vídeo 15 (`libreta.db`) y mide a qué llegó cada contrato **desde que lo viste tú**, con velas de un minuto de GeckoTerminal.

Órdenes: `/mide` (ventana de 6 horas) · `/mide 3` · `/detalle`

Las tres reglas: se entra en la vela **siguiente** a verlo · sin 1.000 $ de volumen no se mide · el máximo que cuenta es el de **después** de verlo.
El bot te enseña también la cuenta tramposa (contando desde 6 horas antes) para que veas la diferencia.

## Lo que necesitas antes

- **Python 3.10 o más nuevo.**
- **Un bot de Telegram y su clave** (BotFather). Lo enseñamos en el Curso de Claude, capítulo 18.

## Instalar y arrancar

1. Copia `.env.ejemplo` como `.env` y pon la clave de tu bot.
2. `pip install -r requirements.txt` y `python3 medir.py`.
3. Escríbele a tu bot: te dirá tu número de usuario. Ponlo en `TELEGRAM_MI_ID` y vuelve a arrancarlo. Así solo te contesta a ti.

Tiene que estar encendido todo el rato: el ordenador encendido o un servidor en la nube.
Si no sabes programar, pídeselo a Claude: "Instálame este bot de GitHub, pon la clave de mi bot de Telegram, arráncalo y que se levante solo si se cae".

## Lo que hay que saber

- GeckoTerminal gratis: unas 10 preguntas por minuto. Medir 70 contratos tarda unos 8 minutos.
- Copia aquí `libreta.db` o pon su ruta en `LIBRETA`, en el `.env`.
- Los disgustos que nos llevamos nosotros: un ranking de grupos que acertaba el 13 % llegando el primero "acertaba" el 47 % contando desde 6 horas antes;
  y una criba que daba el 60,9 % se quedó en el 34,0 % al quitar los pools sin volumen (volumen típico de esas curvas fantasma: 1 $).

**Esto no es consejo financiero.** Es una herramienta para mirar.
