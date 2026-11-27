# Claude en tu día a día 8: comentarios con Claude que solo salen si tú das el OK

▶️ Vídeo: (enlace en la descripción del canal)

## Qué hace

Cada día prepara la lista de cuentas que toca comentar (5 de Instagram y 5 de X, que van rotando), descarta los posts viejos o fijados, le pide a Claude **dos opciones de comentario por post**, las pasa por un **filtro que quita lo que suena a máquina** y te las manda a Telegram con tres botones: **A**, **B** o **fuera**. Solo se publica lo que apruebas tú.

La norma: comentar de forma automática puede ir contra las condiciones de algunas redes (las de Instagram lo dicen: [help.instagram.com/581066165581870](https://help.instagram.com/581066165581870)). Por eso aquí la máquina recoge y escribe, y lo que sale lo decides tú. En el vídeo, en nuestro servidor, el navegador publica lo aprobado; en esta versión, `publicar.py` te abre el post y te enseña el comentario **para que lo pegues tú**.

Viene con **cuentas y posts de ejemplo inventados** para probarlo sin tocar ninguna red.

## La frase para Claude

> Móntame un sistema de comentarios para mis redes. Cada día, escribe dos opciones por post, cortas y naturales, sin venta ni enlaces. Pásalas por un filtro que quite lo que suene a máquina y mándamelas a Telegram con botones. Solo se publica lo que yo apruebe.

## Lo que necesitas antes

- **Python 3.10 o más nuevo** (gratis). Entra en [python.org/downloads](https://www.python.org/downloads/), baja la última versión e instálala. En Windows, **marca la casilla *Add python.exe to PATH*** antes de pulsar *Install*. Para comprobarlo, abre una terminal y escribe `python --version` (en Mac y Linux, `python3 --version`): tiene que salir 3.10 o un número mayor.
- **Claude Code instalado en tu ordenador y con tu cuenta dentro**: es el que escribe las opciones, con su modo sin conversación (`claude -p`). Lo explica **Claude en tu día a día 33: Claude trabajando en tu servidor mientras duermes** → [`claude-en-tu-dia-a-dia/33-claude-trabajando-mientras-duermes`](../33-claude-trabajando-mientras-duermes/). Para instalarlo, la guía oficial: [code.claude.com/docs/en/setup](https://code.claude.com/docs/en/setup) (se instala con una orden en la terminal y entras con tu cuenta de Claude). Para comprobarlo, `claude --version`. Necesita un plan de pago de Claude: qué plan te sirve, **Curso de Claude 1: qué es Claude y cuál te sirve (desde cero)** → [`curso-de-claude/01-que-es-claude`](../../curso-de-claude/01-que-es-claude/); cómo se paga, en [claude.ai](https://claude.ai), *Ajustes* → *Facturación* (es una cuota fija al mes, no saldo que se recarga); y lo que llevas gastado del cupo, **Curso de Claude 10: por qué se te acaba el plan y dónde ver lo que gastas** → [`curso-de-claude/10-por-que-se-acaba-el-plan`](../../curso-de-claude/10-por-que-se-acaba-el-plan/). Precios oficiales: [claude.com/pricing](https://claude.com/pricing).
- **Un bot de Telegram y su clave** (gratis). Se crea hablando con `@BotFather` en Telegram: lo enseña **Curso de Claude 18: tu primer bot de Telegram que te avisa** → [`curso-de-claude/18-tu-primer-bot-de-telegram`](../../curso-de-claude/18-tu-primer-bot-de-telegram/), y el short *Esa clave es la llave del bot*. Guía oficial: [core.telegram.org/bots/tutorial](https://core.telegram.org/bots/tutorial).
- **Tu número de chat de Telegram** (`TELEGRAM_CHAT_ID`), para que el bot solo te haga caso a ti. Lo explica **Curso de Claude 19: comandos y que tu bot te conteste solo a ti** → [`curso-de-claude/19-comandos-y-solo-a-ti`](../../curso-de-claude/19-comandos-y-solo-a-ti/) y el short *Cada mensaje lleva quién lo manda*. Si no lo sabes, este bot te lo dice (paso 5 de *Cómo se usa*).
- **Los botones debajo del mensaje** son los de **Curso de Claude 20: botones, fotos y archivos en tu bot de Telegram** → [`curso-de-claude/20-botones-fotos-y-archivos`](../../curso-de-claude/20-botones-fotos-y-archivos/). Para usar este no hace falta haberlo visto: ya vienen hechos.
- **Tus cuentas de Instagram y de X**, con las que comentas tú a mano. Este programa no entra en ellas ni necesita sus contraseñas.
- **Los posts recogidos** en un archivo (`posts_recogidos.json`, con la misma forma que `posts_ejemplo.json`; luego pon `POSTS=posts_recogidos.json` en el `.env`). En el vídeo los recoge un navegador que va solo, como el de **Curso de Claude 33: un navegador que va solo para las webs que se rellenan (Playwright)** → [`curso-de-claude/33-navegador-que-va-solo-playwright`](../../curso-de-claude/33-navegador-que-va-solo-playwright/). Mira antes las condiciones de cada red: leerlas con un programa también puede ir contra ellas. Si no, los apuntas tú (enlace, texto y fecha) o se los pasas a Claude para que te rellene el archivo.

## Qué hay en la carpeta

| Archivo | Para qué |
|---|---|
| `comentarios.py` | El encargo diario, el filtro de posts viejos, lo que se le pide a Claude y el quitador de pinta de máquina. |
| `bot.py` | Te manda las opciones a Telegram con los botones A, B y fuera. Solo te hace caso a ti. |
| `publicar.py` | Una pasada de publicación: solo lo aprobado, uno a uno, con espera de 1 a 3 minutos. |
| `cuentas.txt` | **Tus** cuentas a comentar, de tu tema y de tu idioma (aquí, inventadas). |
| `posts_ejemplo.json` | Posts inventados para probar: uno viejo, uno fijado y uno de X de tres días, a propósito. |
| `frases_prueba.txt` | Frases con pinta de máquina para comprobar el filtro a mano. |

Al funcionar se crean `estado.json` (qué opciones hay y qué has aprobado) y `memoria.txt` (lo que ya has publicado, para que Claude no se repita).

## Cómo se usa

**1. Instala lo necesario** (una vez), abriendo una terminal en esta carpeta:

```
pip install -r requirements.txt
```

**2. Copia `.env.ejemplo` a `.env`.** Para probar con los ejemplos no cambies nada más todavía (la línea `HOY=2026-11-09` hace como si hoy fuera ese día, para que los posts de ejemplo no estén viejos; **bórrala cuando uses tus posts de verdad**).

**3. Pruébalo sin Claude ni bot** (no necesita claves):

```
python comentarios.py encargo
python comentarios.py posts
python comentarios.py filtro
```

Si va bien verás las 5 + 5 cuentas del día con `"tope_me_gusta": 20`; en los posts, dos con `SE COMENTA` y tres `fuera` (el de hace 6 días, el fijado y el de X de hace 3 días); y en el filtro, cuatro frases `FUERA` (empieza con "gran post", "no es solo esto, es lo otro", lista de tres y emoji de cohete) y tres `VALE`, una con el "sin lugar a dudas" quitado y otra con la raya larga cambiada por una coma. Para probar una frase tuya: `python comentarios.py filtro "tu frase"`.

**4. Que Claude escriba las opciones:**

```
python comentarios.py escribir
```

Por cada post que vale, llama a Claude Code con las normas (de 4 a 25 palabras, como un colega de redes, una sola idea, sin venta, enlaces ni etiquetas) y la memoria, y pasa las dos opciones por el filtro. Verás `ig1: 2 opción(es) listas` o, si alguna cae, `opción A FUERA (motivo)`.

**5. Rellena el bot en el `.env`**: `TELEGRAM_TOKEN` (la clave que te dio BotFather) y `TELEGRAM_CHAT_ID`. Si no sabes tu número de chat, arranca `python bot.py`, escríbele cualquier cosa y en la terminal saldrá `Si eres tú, pon TELEGRAM_CHAT_ID=... en el .env`.

**6. Mándate las opciones y pulsa los botones:**

```
python bot.py enviar
python bot.py
```

El primero te manda un mensaje por post con el texto del post, la opción A, la B y los botones ✅ A, ✅ B y ❌ Fuera. Si ese día no hay ninguna opción, te manda un aviso: `Esta mañana no ha llegado ninguna opción`. El segundo se queda escuchando: al pulsar, el mensaje cambia a `✅ Aprobada la A. Se publica en la próxima pasada.` o `❌ Descartado`. Para pararlo, `Ctrl+C`.

**7. Publica lo aprobado:**

```
python publicar.py
```

Te abre cada post aprobado en tu navegador y te enseña el comentario. Lo pegas tú, contestas `s` y queda apuntado en la memoria para no ofrecértelo otra vez. Entre uno y otro espera de 1 a 3 minutos.

**8. Cada mañana, solo.** `python comentarios.py escribir` y luego `python bot.py enviar`, a primera hora; `python bot.py` tiene que estar en marcha para recoger tus botones.
- **Windows**: Programador de tareas → Crear tarea básica → Diariamente a las 8:00 → programa `python`, argumentos `comentarios.py escribir`, "Iniciar en": esta carpeta. Otra igual a las 8:15 con `bot.py enviar`.
- **Mac / Linux**: `crontab -e` y añade `0 8 * * * cd /ruta/a/esta/carpeta && python3 comentarios.py escribir && python3 bot.py enviar` (cambia la ruta por la tuya).

## Cómo lo compruebas

Pasa a mano por el filtro unas cuantas frases que suenen a máquina (`python comentarios.py filtro "Gran post, qué gran aporte"`) y mira que las pilla. Y después de cada pasada, entra en el post y mira que hay **una sola** respuesta tuya, no dos.

## Los tres fallos

1. **Claude escribe como un sabio**, con metáforas y frases redondas que nadie dice. Corrección: que hable como un colega de redes, con un ejemplo bueno y uno malo (van en las normas de `comentarios.py`).
2. **Pierde el hilo** y comenta algo que no viene al cuento. Corrección: una sola idea, sobre lo que dice el post, sin inventar nada.
3. **Se repite de un día para otro.** Corrección: que lea la memoria antes de escribir (`memoria.txt`; además, el filtro tira lo que ya dijiste).

---

Esto no es consejo financiero y aquí no se señala a nadie.
