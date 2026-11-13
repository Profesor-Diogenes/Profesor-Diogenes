# Claude en tu día a día 2: conectar Claude a tu banco en solo lectura

▶️ Vídeo: (enlace en la descripción del canal)

## Qué hace

En Europa, la norma de pagos PSD2 obliga a los bancos a dejar que programas autorizados **lean** tus cuentas si tú das permiso, sin darle tu contraseña a nadie (es la "banca abierta"). Aquí tienes los programas que le pedimos a Claude en el vídeo:

- `conectar.py`: te da el enlace del banco, das el permiso desde el móvil y guarda la sesión.
- `descargar.py`: baja los movimientos de cada cuenta a `datos/movimientos.csv`, **solo leyendo** y sin repetidos. Es el archivo que usa el [capítulo 3](../03-movimientos-cada-manana/).
- `vigilante.py`: mira cuánto le queda al permiso y te avisa por Telegram cuando quedan menos de 20 días.

Ninguno puede mover dinero: solo piden cuentas y movimientos.

## La frase para Claude

> Escríbeme dos programas para leer mis cuentas por banca abierta europea, a través de un proveedor oficial y solo en lectura. Uno para dar el permiso y otro para descargar los movimientos cada mañana, sin repetidos. La llave privada, en un archivo aparte, nunca en el código. Avísame por Telegram cuando al permiso le queden menos de veinte días. Y no des por hecho que los identificadores de las cuentas no cambian.

## Lo que necesitas antes

- **Python 3.10 o más nuevo** (gratis). Entra en [python.org/downloads](https://www.python.org/downloads/), baja la última versión e instálala. En Windows, **marca la casilla *Add python.exe to PATH*** antes de pulsar *Install*. Para comprobarlo, abre una terminal y escribe `python --version` (en Mac y Linux, `python3 --version`): tiene que salir 3.10 o un número mayor.
- **Una cuenta de Claude** (vale la gratis). Cómo se crea y qué plan te sirve: **Curso de Claude 1: qué es Claude y cuál te sirve (desde cero)** → [`curso-de-claude/01-que-es-claude`](../../curso-de-claude/01-que-es-claude/).
- **Un proveedor oficial de banca abierta** que haga de puente (un "proveedor de servicios de información sobre cuentas" autorizado). Ningún capítulo enseña todavía a darse de alta, así que estos son los pasos:
  1. Elige uno autorizado. Qué es la banca abierta lo explica el Banco de España en su [Portal del Cliente Bancario](https://clientebancario.bde.es); los proveedores autorizados en Europa salen en el [registro oficial de la Autoridad Bancaria Europea](https://euclid.eba.europa.eu/register/). Aquí no se recomienda ninguno.
  2. Date de alta en su portal para desarrolladores y **registra tu aplicación**, con la dirección de vuelta que pondrás en `REDIRECT_URL`.
  3. Te dará un **identificador de aplicación**, una **llave privada** (un archivo `.pem` que demuestra que eres tú), la dirección de su API y los datos de firma (emisor y audiencia). Guárdalo todo en el `.env` y el `.pem` en esta carpeta, nunca en el código.
  4. **Si es de pago**: el método de pago se pone y el gasto se ve en la parte de facturación de su portal (cada proveedor la llama a su manera; búscala en su documentación). Mira antes si cobra por cuenta conectada, por consulta o con cuota fija, y si tiene un nivel gratis para uso personal.

  Este código usa la forma más habitual de estas APIs (petición firmada con tu llave, `/auth`, `/sessions` y `/accounts/.../transactions`). Si tu proveedor usa otras rutas o nombres de campos, pásale a Claude su documentación y pídele que adapte `comun.py`, `conectar.py` y `descargar.py`.
- **Un bot de Telegram y su clave** (opcional, para los avisos; gratis). Se crea hablando con `@BotFather` en Telegram: lo enseña **Curso de Claude 18: tu primer bot de Telegram que te avisa** → [`curso-de-claude/18-tu-primer-bot-de-telegram`](../../curso-de-claude/18-tu-primer-bot-de-telegram/), y el short *Esa clave es la llave del bot*. Guía oficial: [core.telegram.org/bots/tutorial](https://core.telegram.org/bots/tutorial).
- **Tu número de chat de Telegram** (`TELEGRAM_CHAT_ID`), para que el bot te escriba solo a ti. Lo explica **Curso de Claude 19: comandos y que tu bot te conteste solo a ti** → [`curso-de-claude/19-comandos-y-solo-a-ti`](../../curso-de-claude/19-comandos-y-solo-a-ti/) y el short *Cada mensaje lleva quién lo manda*. Si no lo sabes, el bot del [capítulo 3](../03-movimientos-cada-manana/) te lo dice al escribirle (su paso 4).

## Cómo se usa

**1. Instala lo necesario** (una vez), con una terminal abierta en esta carpeta:

```
pip install -r requirements.txt
```

**2. Copia `.env.ejemplo` a `.env`** y rellena tus datos. Pon tu llave privada `.pem` en esta carpeta y su nombre en `LLAVE_PRIVADA`. **El `.env` y el `.pem` no se comparten nunca** (ya están en el `.gitignore`).

**3. Da el permiso:**

```
python conectar.py permiso
```

Te sale un enlace. Ábrelo, entra en tu banco como siempre y acepta. Al terminar, el navegador vuelve a tu `REDIRECT_URL` con `?code=...` en la dirección. Copia ese código y:

```
python conectar.py sesion EL_CODIGO
```

Si va bien: `Sesión guardada. Cuentas: N. El permiso caduca: ...`

**4. Descarga los movimientos:**

```
python descargar.py
```

Si va bien, por cada cuenta verás cuántos ha bajado y cuántos son nuevos, y al final `Guardado: datos/movimientos.csv (... movimientos, ... nuevos)`. Si lo lanzas otra vez, saldrá `0 nuevos`: no repite nada.

Cómo evita los repetidos: empieza unos días antes del último movimiento que ya tiene (por si el banco apuntó alguno tarde) y descarta los que ya estaban por la **referencia del banco**; si no hay referencia, por fecha, importe y concepto.

**5. Mira el permiso:**

```
python vigilante.py
```

Verás `Caduca DD-MM-AAAA -> quedan N días`. Si quedan menos de 20, te llega el aviso por Telegram (si no has puesto Telegram, sale solo en pantalla).

**6. Que se haga solo cada mañana.** Con una vez al día basta: la norma solo deja consultar unas cuatro veces al día sin que tú estés delante.
- **Windows**: Programador de tareas → Crear tarea básica → Diariamente a las 8:00 → programa `python`, argumentos `descargar.py`, "Iniciar en": esta carpeta. Otra igual para `vigilante.py`.
- **Mac / Linux**: `crontab -e` y añade (cambiando la ruta por la tuya):
  ```
  0 8 * * * cd /ruta/a/esta/carpeta && python3 descargar.py && python3 vigilante.py
  ```

**7. Cuando caduque**, repite el paso 3. Al renovar puedes pedirlo por más días (en el vídeo: 90 la primera vez y 179 al renovar; lo máximo lo pone tu banco). Si al renovar el banco cambia los identificadores de las cuentas, `descargar.py` lo detecta, te avisa y usa los nuevos sin duplicar movimientos.

## Los tres fallos

1. **Claude guarda la llave privada dentro del código.** Si compartes el programa, regalas la llave. Corrección: que la lea de un archivo aparte que nunca se comparte (aquí, `LLAVE_PRIVADA` en el `.env`).
2. **No prevé la caducidad**, y un día deja de bajar sin que te enteres. Corrección: el aviso antes de que caduque (`vigilante.py`).
3. **Da por hecho que los identificadores de las cuentas no cambian.** Corrección: que se los pida al banco en cada conexión y avise si no coinciden (lo hace `descargar.py`).

Si sale `401 Unauthorized`, el proveedor no acepta tu firma: revisa `APP_ID`, la llave, `JWT_EMISOR` y `JWT_AUDIENCIA`.

---

Esto no es consejo financiero y aquí no se señala a nadie. Solo lectura: estos programas no pueden mover dinero.
