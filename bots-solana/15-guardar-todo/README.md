# 15 · La libreta: guardar todo lo que ves

Vídeo 15 de la sección "Bots de Solana" del canal **Profesor Diógenes**.
Una base de datos (SQLite, un solo fichero) donde tu bot apunta cada contrato con su foto de ese momento y le hace una foto nueva
cada 15 minutos durante 48 horas. Sin esto no se puede medir nada después.

Órdenes: pegar un contrato (y una nota) · `/libreta` · `/ver <contrato>` · `/importa` (mete los .csv de los otros bots que copies a esta carpeta) · `/exporta`

## Lo que necesitas antes

- **Python 3.10 o más nuevo.**
- **Un bot de Telegram y su clave** (BotFather). Lo enseñamos en el Curso de Claude, capítulo 18.

## Instalar y arrancar

1. Copia `.env.ejemplo` como `.env` y pon la clave de tu bot.
2. `pip install -r requirements.txt` y `python3 libreta.py`.
3. Escríbele a tu bot: te dirá tu número de usuario. Ponlo en `TELEGRAM_MI_ID` y vuelve a arrancarlo. Así solo te contesta a ti.

Tiene que estar encendido todo el rato: el ordenador encendido o un servidor en la nube.
Si no sabes programar, pídeselo a Claude: "Instálame este bot de GitHub, pon la clave de mi bot de Telegram, arráncalo y que se levante solo si se cae".

## Lo que hay que saber

- Precios de DexScreener (gratis, sin clave), de 30 en 30 contratos.
- La primera foto es la que manda: si un contrato ya estaba apuntado, no se pisa.
- Por qué hay que seguirlos a todos el mismo tiempo: nosotros bajábamos cada curva una sola vez y unas cubrían 11 minutos y otras dos días.
  Compararlas era mentira. Todos, 48 horas o hasta que mueren.

**Esto no es consejo financiero.** Es una herramienta para mirar.
