# 20 · La mini app

Vídeo 20 de la sección **Bots de Solana** del canal Profesor Diógenes.

El bot del vídeo 19 lo hace todo, pero en un chat: mucho texto y muchos botones. Esto es lo mismo en una pantalla con pestañas, dentro de Telegram.

## Qué es una mini app

Una página web normal que Telegram abre **dentro** del chat de tu bot. Tiene dos partes:

- **La página** (`web/index.html`): lo que ves. Pestañas, tablas, colores.
- **El programa** (`miniapp.py`): sirve la página y le contesta cuando pregunta. Para contestar usa los programas de los vídeos anteriores, que tienen que estar en sus carpetas, al lado de esta.

Y hace falta una tercera cosa: **una dirección de internet con https** que lleve hasta tu programa. Telegram no abre mini apps sin https.

## Las tres pestañas

| Pestaña | Qué enseña | De qué vídeo sale |
|---|---|---|
| Analizar | Pegas un contrato o una billetera y eliges: ficha, seguridad, holders, el dev, por dentro, billetera | 1, 10, 7, 8, 2 y 3 |
| Libreta | Lo que tienes apuntado: cuánto valía al apuntarlo y cuánto vale ahora | 15 |
| Papel | Tu balance en papel, las abiertas y las cerradas | 17 |

La libreta y el papel solo se **leen**: quien apunta y quien compra en papel siguen siendo sus bots (o el bot definitivo del vídeo 19, que los lleva dentro).

## Ponerlo en marcha

```
pip install -r requirements.txt
cp .env.ejemplo .env      # la clave de tu bot, tu número de usuario y la dirección
python3 miniapp.py
```

Al arrancar, el programa le dice a Telegram que el botón de menú de tu chat con el bot abra la mini app. Abres el chat, tocas **Abrir**, y ya.

## La dirección: dos caminos

**Para probar, gratis y sin comprar nada.** Cloudflare tiene un túnel de pruebas que te da una dirección https al momento:

```
cloudflared tunnel --url http://localhost:8080
```

Te escribe una dirección del tipo `https://palabras-al-azar.trycloudflare.com`. La pones en `MINIAPP_URL` del `.env` y arrancas. Ojo: esa dirección cambia cada vez que arrancas el túnel. Vale para probar, no para dejarlo puesto.

**Para dejarlo puesto: un dominio tuyo.** Un dominio se compra en cualquier registrador y cuesta del orden de una decena de euros al año, según la terminación. Con el dominio en Cloudflare (la cuenta gratis vale), creas un túnel con nombre que une `app.tudominio.com` con tu programa, y esa dirección ya no cambia. Tu ordenador no queda abierto a internet: el túnel sale de dentro hacia fuera.

Si no sabes hacerlo, dile a Claude: *"Tengo un dominio en Cloudflare y un programa en mi ordenador en el puerto 8080. Guíame paso a paso para crear un túnel de Cloudflare con nombre que lo publique en app.midominio.com."*

## Quién puede entrar

Solo tú. Cuando Telegram abre la página le pasa un texto firmado con la clave de tu bot. El programa comprueba esa firma y mira que el usuario sea el de `TELEGRAM_MI_ID`. Quien encuentre la dirección y la abra en un navegador verá la página vacía y no le contestará nada.

Por eso la clave del bot no se enseña a nadie: con ella se puede falsificar la firma.

## Cambiarle el aspecto

Todo lo que se cambia sin tocar código está en **`aspecto.json`**:

- `titulo` y `lema`: lo de arriba.
- `foto`: el nombre de una imagen que metas en la carpeta `web` (por ejemplo `foto.jpg`). Sale redonda, arriba a la izquierda.
- `foto_grande`: otra imagen de la carpeta `web`, pero a todo lo ancho, arriba del todo.
- `colores`: fondo, tarjetas, texto, color principal, y los colores de subir y bajar.
- `pestanas`: cuáles salen y en qué orden. Quita una de la lista y desaparece.
- `pestanas_abajo`: ponlo en `true` y las pestañas bajan al pie, como en una aplicación del móvil.
- `nombres`: cómo se llama cada pestaña.
- `pie`: la frase de abajo.

Guardas, cierras la mini app y la vuelves a abrir.

En la carpeta `ejemplos` hay dos aspectos ya hechos, los del vídeo: uno azul con el papel en la primera pestaña y otro claro con las pestañas abajo. Copia el que quieras encima de `aspecto.json` y pon tu foto.

Y para lo demás, la imaginación es el límite. No hace falta saber programar: le pasas a Claude `miniapp.py`, `web/index.html` y `aspecto.json` y le pides lo que quieras. Ejemplos:

- *"Cámbiame los colores a tonos azul noche con el principal en verde."*
- *"Añade una pestaña 'Señales' que enseñe en una tabla las últimas líneas del senales.csv del vídeo 9."*
- *"En la libreta, que al tocar un token se abra su ficha."*
- *"Añade arriba un buscador que filtre la libreta por nombre."*

## Lo que no hay

Ninguna inteligencia artificial y ninguna compra de verdad. Es una forma más cómoda de mirar lo mismo.

Esto no es consejo financiero. Es una herramienta para mirar.
