# Claude en tu día a día 4: sobres y metas que tu banco no tiene

▶️ Vídeo: (enlace en la descripción del canal)

## Qué hace

Tienes una cuenta de ahorro y dentro hay dinero de muchas cosas: la hucha de Navidad, lo que va camino de la inversión, lo de las oportunidades. Mirando el saldo es imposible saber de quién es cada euro.

No hace falta abrir más cuentas. Este programa coge los movimientos que ya bajas del banco cada mañana (los del [capítulo 2](../02-banco-en-solo-lectura/)), los reparte en **sobres** desde una fecha de corte con **tus** reglas, y te dice cuánto hay en cada sobre, el total y lo que puedes gastar. Comprueba que cuadra al céntimo con el saldo del banco, te avisa si una regla deja de entrar y, si quieres, te lo manda por Telegram.

Viene con **movimientos de ejemplo inventados** para que lo pruebes sin tocar tu banco.

## La frase para Claude

> Lee los movimientos de mi cuenta de ahorro desde la fecha de corte y repártelos en sobres con mis reglas, sin inventarte ninguna. Dime cuánto hay en cada sobre y cuánto puedo gastar. Y avísame si una regla deja de entrar.

## Lo que necesitas antes

- **Python 3.10 o más nuevo** (gratis). Entra en [python.org/downloads](https://www.python.org/downloads/), baja la última versión e instálala. En Windows, **marca la casilla *Add python.exe to PATH*** antes de pulsar *Install*. Para comprobarlo, abre una terminal y escribe `python --version` (en Mac y Linux, `python3 --version`): tiene que salir 3.10 o un número mayor.
- **Una cuenta de Claude** (vale la gratis). Cómo se crea y qué plan te sirve: **Curso de Claude 1: qué es Claude y cuál te sirve (desde cero)** → [`curso-de-claude/01-que-es-claude`](../../curso-de-claude/01-que-es-claude/).
- **Los movimientos de tu cuenta de ahorro** (para usarlo de verdad): los baja cada mañana **Claude en tu día a día 2: conectar Claude a tu banco en solo lectura** → [`claude-en-tu-dia-a-dia/02-banco-en-solo-lectura`](../02-banco-en-solo-lectura/). Para probar no hace falta: viene un archivo de ejemplo inventado.
- **El saldo de tu cuenta de ahorro el día de corte y el de hoy**: lo miras tú en la app de tu banco.
- **Solo si quieres el informe por Telegram:**
  - **Un bot de Telegram y su clave** (gratis). Se crea hablando con `@BotFather` en Telegram: lo enseña **Curso de Claude 18: tu primer bot de Telegram que te avisa** → [`curso-de-claude/18-tu-primer-bot-de-telegram`](../../curso-de-claude/18-tu-primer-bot-de-telegram/), y el short *Esa clave es la llave del bot*. Guía oficial: [core.telegram.org/bots/tutorial](https://core.telegram.org/bots/tutorial).
  - **Tu número de chat de Telegram** (`TELEGRAM_CHAT_ID`), para que el bot te escriba solo a ti. Lo explica **Curso de Claude 19: comandos y que tu bot te conteste solo a ti** → [`curso-de-claude/19-comandos-y-solo-a-ti`](../../curso-de-claude/19-comandos-y-solo-a-ti/) y el short *Cada mensaje lleva quién lo manda*. El bot del [capítulo 3](../03-movimientos-cada-manana/) también te lo dice si le escribes.

## Qué hay en la carpeta

| Archivo | Para qué |
|---|---|
| `sobres.py` | Reparte los movimientos en sobres, suma los ajustes, comprueba con el saldo y avisa. |
| `reglas.txt` | **Tus** reglas de reparto. Las decides tú, no Claude. |
| `partida_ejemplo.json` | El punto de partida: la fecha de corte y cuánto había en cada sobre ese día. |
| `ajustes_ejemplo.csv` | Lo que no encaja en ninguna regla, a mano, con fecha y motivo. |
| `movimientos_ejemplo.csv` | Movimientos inventados para probar (con un repetido y uno de antes del corte, a propósito). |

## Cómo se usa

**1. Instala lo necesario** (una vez), abriendo una terminal en esta carpeta:

```
pip install -r requirements.txt
```

**2. Pruébalo con el ejemplo** (no necesita claves):

```
python sobres.py --saldo 750,00
```

Si va bien verás los tres sobres (`hucha_navidad 535,00 €`, `hacia_inversion 150,00 €`, `oportunidades 65,00 €`), el `TOTAL 750,00 €`, la línea `CUADRA al céntimo. Todo tiene dueño: gastable 0,00 €` y un aviso a propósito: `AVISO: la regla 'REDONDEO' no ha entrado nada en 2026-10` (en el ejemplo, el redondeo se paró en octubre).

**3. El punto de partida.** Elige una fecha de corte, mira en la app del banco el saldo de ese día y decide **tú, a mano y una sola vez**, cuánto de ese saldo es de cada sobre. Copia `partida_ejemplo.json`, pon tu fecha y tus cifras, y deja `"comprobado_a_mano": true` solo cuando lo hayas comprobado. La suma de los sobres tiene que ser el saldo de ese día. A partir de ahí, el programa solo suma y resta lo que pasa **después** de esa fecha.

**4. Tus reglas.** Abre `reglas.txt` y escribe las tuyas. Cada línea dice qué palabras del concepto del banco van a qué sobre:

```
REDONDEO = oportunidades | cada mes
AHORRO AUTOMATICO = hucha_navidad 50, hacia_inversion resto | cada mes
TRASPASO A INVERSION = hacia_inversion
* = hucha_navidad
```

- `sobre1 50, sobre2 resto`: 50 € fijos a uno y lo que quede al otro.
- `| cada mes`: si un mes entero no entra nada de esa regla, te avisa.
- `* = …`: adónde va cualquier otro movimiento.

Si algo no encaja en ninguna regla, **no inventes una regla nueva para un caso suelto**: apúntalo en el archivo de ajustes (`fecha;sobre;importe;motivo`). Sin motivo, el programa no lo acepta.

**5. Copia `.env.ejemplo` a `.env`** y pon tus archivos:
- `MOVIMIENTOS`: el de tu banco (por ejemplo `../02-banco-en-solo-lectura/datos/movimientos.csv`).
- `CUENTA_AHORRO`: si ese archivo trae varias cuentas, la de ahorro (lo que sale en la columna `cuenta`). Si solo trae esa, déjalo vacío.
- `PARTIDA`, `REGLAS`, `AJUSTES`: tus archivos (puedes dejar los nombres y cambiar el contenido).
- `TELEGRAM_TOKEN` y `TELEGRAM_CHAT_ID`: solo si lo quieres por Telegram.

**6. El informe:**

```
python sobres.py --saldo 1234,56
python sobres.py --saldo 1234,56 --telegram
```

Pon en `--saldo` el saldo de hoy según tu banco. Con `--telegram` te llega el mismo informe al móvil. Si quieres que llegue solo cada mañana, prográmalo como el aviso del [capítulo 3](../03-movimientos-cada-manana/) (Programador de tareas en Windows, `crontab -e` en Mac y Linux), un rato después de la descarga.

## La trampa del barrido

Si tu banco te deja poner un tope a la cuenta del día a día y **barrer** lo que sobra al ahorro, ojo con el día. El recibo más gordo del mes, el de la tarjeta, llega a primeros: si el barrido salta antes, te deja sin dinero para cubrirlo. Que actúe **después**. Y en los meses en que cae un recibo anual, el tope sube.

## Cómo lo compruebas

Suma los sobres y compáralo con el saldo real de la cuenta (`--saldo`). Tiene que **cuadrar al céntimo**. Si sale `NO CUADRA`, falta un ajuste o sobra una regla. Si sale dinero sin sobre que no esperabas, falta una regla.

## Los tres fallos

1. **Claude se inventa el reparto** y te propone sus porcentajes. Corrección: las reglas las escribes tú (`reglas.txt`) y él solo las aplica.
2. **Da por hecho que la regla sigue funcionando.** A nosotros el redondeo se paró semanas y nadie se enteró. Corrección: que avise si en un mes no entra nada de una regla (`| cada mes`).
3. **Te monta un sistema que depende de que tú hagas algo a mano cada mes.** Corrección: que todo vaya solo, y tú solo mires. Lo único a mano es el punto de partida, una vez, y algún ajuste suelto.

---

Esto no es consejo financiero y aquí no se señala a nadie.
