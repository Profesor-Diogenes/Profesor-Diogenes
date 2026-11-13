# Claude en tu día a día 3: que Claude te lea los movimientos del banco cada mañana

▶️ Vídeo: (enlace en la descripción del canal)

## Qué hace

Coge el archivo de movimientos que se descarga cada mañana (el del [capítulo 2](../02-banco-en-solo-lectura/)), quita los repetidos, pone cada movimiento en una categoría de **tu** lista, deja los traspasos entre tus cuentas fuera de las sumas y te lo cuenta por un bot de Telegram con cinco órdenes: `/mes`, `/categorias`, `/alertas`, `/resumen` y `/buscar`.

Viene con **movimientos de ejemplo inventados** para que lo pruebes sin tocar tu banco.

## La frase para Claude

> Lee el archivo de movimientos que se descarga cada mañana. Pon cada uno en una categoría de mi lista, y lo que no encaje, en otros, sin inventarte categorías. Quita los repetidos por la referencia del banco. Deja fuera de las sumas los traspasos entre mis cuentas. Móntame un bot de Telegram con las órdenes mes, categorías, alertas, resumen y buscar. Y antes de opinar de mi dinero, dime qué archivos has leído.

## Lo que necesitas antes

- **Python 3.10 o más nuevo** (gratis). Entra en [python.org/downloads](https://www.python.org/downloads/), baja la última versión e instálala. En Windows, **marca la casilla *Add python.exe to PATH*** antes de pulsar *Install*. Para comprobarlo, abre una terminal y escribe `python --version` (en Mac y Linux, `python3 --version`): tiene que salir 3.10 o un número mayor.
- **Una cuenta de Claude** (vale la gratis). Cómo se crea y qué plan te sirve: **Curso de Claude 1: qué es Claude y cuál te sirve (desde cero)** → [`curso-de-claude/01-que-es-claude`](../../curso-de-claude/01-que-es-claude/).
- **Un bot de Telegram y su clave** (gratis). Se crea hablando con `@BotFather` en Telegram: lo enseña **Curso de Claude 18: tu primer bot de Telegram que te avisa** → [`curso-de-claude/18-tu-primer-bot-de-telegram`](../../curso-de-claude/18-tu-primer-bot-de-telegram/), y el short *Esa clave es la llave del bot*. Guía oficial: [core.telegram.org/bots/tutorial](https://core.telegram.org/bots/tutorial).
- **Tu número de chat de Telegram** (`TELEGRAM_CHAT_ID`), para que el bot te escriba solo a ti. Lo explica **Curso de Claude 19: comandos y que tu bot te conteste solo a ti** → [`curso-de-claude/19-comandos-y-solo-a-ti`](../../curso-de-claude/19-comandos-y-solo-a-ti/) y el short *Cada mensaje lleva quién lo manda*. Si no lo sabes, este mismo bot te lo dice (paso 4 de *Cómo se usa*).
- **Tus movimientos del banco** (opcional): los baja el capítulo anterior, **Claude en tu día a día 2: conectar Claude a tu banco en solo lectura** → [`claude-en-tu-dia-a-dia/02-banco-en-solo-lectura`](../02-banco-en-solo-lectura/). Para probar no hace falta: viene un archivo de ejemplo inventado.

## Qué hay en la carpeta

| Archivo | Para qué |
|---|---|
| `finanzas.py` | Lee los movimientos, quita repetidos, pone categorías y suma sin traspasos. |
| `bot.py` | El bot de Telegram. Solo te contesta a ti. |
| `categorias.txt` | **Tu** lista de categorías y sus palabras. La decides tú, no Claude. |
| `movimientos_ejemplo.csv` | Movimientos inventados para probar (con un repetido y un traspaso a propósito). |
| `NORMAS.md` | Las normas que Claude lee siempre al empezar: primero lee, luego opina. |
| `diario.log` | El diario que solo crece (aquí, con entradas de ejemplo). |

## Cómo se usa

**1. Instala lo necesario** (una vez), abriendo una terminal en esta carpeta:

```
pip install -r requirements.txt
```

**2. Pruébalo sin bot** (no necesita claves):

```
python finanzas.py
```

Si va bien verás `Leídas 19 filas, 18 tras quitar repetidos`, cada movimiento con su categoría y, al final, la diferencia entre contar los traspasos (mal) y no contarlos (bien): `gastos 520,79 €` sin traspasos.

**3. Crea tu bot de Telegram.** En Telegram, habla con `@BotFather`, escribe `/newbot` y sigue los pasos. Te dará una clave (token).

**4. Copia `.env.ejemplo` a `.env`** y rellena tus datos:
- `TELEGRAM_TOKEN`: la clave que te dio BotFather.
- `TELEGRAM_CHAT_ID`: tu número de chat. Si no lo sabes, déjalo como está, arranca el bot (paso 5), escríbele cualquier cosa y en la terminal saldrá `Si eres tú, pon TELEGRAM_CHAT_ID=... en el .env`. Ponlo y vuelve a arrancarlo.
- `MOVIMIENTOS`: deja `movimientos_ejemplo.csv` para probar. Cuando tengas el capítulo 2 funcionando, pon la ruta de tu archivo (por ejemplo `../02-banco-en-solo-lectura/datos/movimientos.csv`).

**5. Arranca el bot:**

```
python bot.py
```

Saldrá `Bot en marcha`. Escríbele `/mes` en Telegram y te contestará con los gastos del último mes por categoría, el total y `(traspasos fuera de las sumas)`. Para pararlo, `Ctrl+C`.

**6. El aviso de cada mañana.** `python bot.py aviso` te manda los movimientos del último día y termina. Para que salga solo cada mañana:
- **Windows**: Programador de tareas → Crear tarea básica → Diariamente a las 8:30 → programa `python`, argumentos `bot.py aviso`, "Iniciar en": esta carpeta.
- **Mac / Linux**: `crontab -e` y añade `30 8 * * * cd /ruta/a/esta/carpeta && python3 bot.py aviso` (cambia la ruta por la tuya).

Ponlo un rato después de la descarga del capítulo 2, que es a las 8.

## Cómo lo compruebas

Escoge un movimiento que recuerdes, búscalo con `/buscar` y mira que sale **una sola vez** y en su categoría. Luego compara el total del mes con lo que te enseña la app de tu banco. Si no cuadra, algo está repetido o falta.

## Los tres fallos

1. **Claude se inventa categorías** o le pone nombre a un cargo que no conoce. Corrección: lista cerrada (`categorias.txt`), lo que no sepa va a `otros`, y que te pregunte.
2. **Cuenta dos veces un movimiento**, porque el banco lo apuntó tarde y la descarga se solapa. Corrección: quitar repetidos por la referencia del banco y, si no la hay, por fecha, importe y concepto (es lo que hace `finanzas.py`).
3. **Opina sin leer.** Corrección: las normas al principio (`NORMAS.md`) y que te diga qué archivos ha leído antes de opinar.

Y uno más: **los traspasos no son ingresos**. Si pasas dinero de una cuenta tuya a otra, contarlo te infla los gastos y los ingresos. Por eso `traspasos` queda fuera de las sumas.

---

Esto no es consejo financiero y aquí no se señala a nadie.
