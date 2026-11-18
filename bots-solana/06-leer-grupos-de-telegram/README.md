# 06 · Leer los grupos de calls de Telegram (cada contrato, a tu móvil)

Vídeo 6 de la sección "Bots de Solana" del canal **Profesor Diógenes**.
Estás en diez grupos de calls y no puedes leerlos todos. Este programa los escucha por ti: cada vez que un grupo suelta
un contrato de Solana, tu bot te avisa con el nombre del token, la capitalización, la liquidez y qué grupo lo ha llamado.
Si otro de tus grupos ya lo había llamado, te dice cuál y hace cuánto.

## Lo que necesitas antes

- **Python 3.10 o más nuevo.**
- **Un bot de Telegram y su clave** (BotFather). Lo enseñamos en el Curso de Claude, capítulo 18.
- **La clave de aplicación de tu cuenta de Telegram** (`api_id` y `api_hash`), en my.telegram.org → *API development tools*.
  Lo enseñamos en el Curso de Claude, capítulo 27. Hace falta porque un bot **no puede leer** los grupos en los que estás tú:
  los lee tu propia cuenta.
- Tu cuenta tiene que estar ya metida en los grupos que quieras escuchar.

## Instalar y arrancar

1. Copia `.env.ejemplo` como `.env` y rellena las claves.
2. `pip install -r requirements.txt` y `python3 grupos.py`.
3. La primera vez te pide tu teléfono y el código que te manda Telegram. Queda guardado en `sesion_grupos.session`:
   **ese fichero es tu cuenta, no se lo pases a nadie ni lo subas a ningún sitio.**
4. Escríbele a tu bot. Si no has puesto `TELEGRAM_MI_ID`, te dice tu número: ponlo en el `.env` y vuelve a arrancar.

**Tiene que estar encendido todo el rato** para avisarte: el ordenador encendido o un servidor en la nube.
Si no sabes programar, pídeselo a Claude: "Instálame este bot de GitHub, pon la clave de mi bot de Telegram, arráncalo y que se levante solo si se cae".

## Cómo se usa (desde tu bot)

- `/grupos` → los grupos y canales en los que estás, con su número. `/grupos calls` → solo los que llevan "calls" en el nombre.
- `/escucha <número> <número>…` → empieza a escucharlos.
- `/quita <número>` → deja de escuchar uno.
- `/lista` → los que estás escuchando. `/ultimos` → las últimas llamadas.

Cada llamada queda apuntada en `llamadas.csv` (hora, grupo, contrato, símbolo, capitalización y liquidez en ese momento),
para que puedas medir tú después a qué llegó cada una.

## Cómo funciona por dentro

- Tu cuenta, con **Telethon**, recibe los mensajes **nuevos** de los grupos que elijas. No baja historial.
- De cada mensaje saca las direcciones de Solana (también las que van dentro de un enlace de pump.fun o DexScreener).
- Pregunta a **DexScreener** qué token es. Si no lo conoce, a **pump.fun** (el token sigue en la curva). Si no lo conoce
  nadie, no es un token (será una billetera) y no te molesta.
- Cada grupo y contrato, un solo aviso.

## Lo que hay que saber

- **No bajes el historial de cientos de grupos.** Es la forma más rápida de que Telegram te frene (FLOOD_WAIT) y te bloquee
  la cuenta. Este programa solo escucha lo nuevo, como si tuvieras el chat abierto.
- Mejor con una cuenta de Telegram aparte, que no sea la de tu vida diaria.
- Lo que medimos con nuestros datos (casi 2 millones de menciones en 1.881 grupos, de agosto de 2025 a julio de 2026):
  - Los rankings de grupos suelen medir desde que alguien vio el token por primera vez, no desde la llamada del grupo.
    Así, llegar tarde parece acertar más: llegando el primero, un grupo acertaba el 13 %; contando 6 horas tarde, "el 47 %".
  - Que lo llamen dos grupos no cambia nada: 23,4 % de tokens que doblan con un grupo, 22,7 % con dos. El segundo llega
    a los 2 minutos y medio de mediana: es eco.
  - Dos de los mejores grupos de nuestro ranking honesto (42 % y 48 % sobre el papel) dieron en directo, del 16 al 25 de
    agosto de 2026, un 18 % y un 24 %. Y en 9 de cada 10 llamadas el precio llegó a caer a la mitad en algún momento.

## Verificación doble (truco)

Lo que apunta este bot en `llamadas.csv` lo has guardado tú. Para tener una segunda prueba que no dependa de ti, mete en el mismo grupo
un bot de análisis de los que registran cada contrato cuando entra (por ejemplo, Phanes): él apunta por su cuenta quién lo llamó primero,
a qué capitalización y cuánto ha hecho desde entonces. Si tu fichero y el suyo coinciden, tu ranking de grupos se puede comprobar en dos pasos.

**Esto no es consejo financiero.** Es una herramienta para mirar.
