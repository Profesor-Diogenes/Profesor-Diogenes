# 24 · Probar una regla contra el pasado

Vídeo 24 de la sección **Bots de Solana** del canal Profesor Diógenes.

Tienes una idea: «los tokens con entre 150 y 400 holders doblan más». Este bot te dice si es verdad en los datos, y sobre todo si sigue siendo verdad **fuera de donde la encontraste**.

## La trampa que evita

Si buscas una regla y la compruebas en las mismas fichas, siempre encuentras alguna que «funciona». Entre cientos de reglas posibles, unas cuantas salen bien de casualidad.

Por eso aquí la tabla se parte en dos **por fecha**: la primera mitad es para buscar y la segunda, posterior, para comprobar. Lo que vale es el número de la segunda.

## Ponerlo en marcha

```
pip install -r requirements.txt
cp .env.ejemplo .env      # y pon dentro la clave de tu bot de Telegram
python3 bot.py
```

Sin Telegram: `python3 reglas.py regla holder_count 150 400`

## Órdenes

- `/campos` — los datos que tiene cada ficha (solo lo que se sabía al ver el token).
- `/regla holder_count 150 400` — prueba tu regla: un dato, desde y hasta.
- `/mejor` — busca la mejor regla en la primera mitad y te enseña lo que hace en la segunda.
- `/azar 500` — prueba 500 reglas que nadie ha pensado y cuenta cuántas «funcionan».

## La tabla (`fichas.csv`)

965 tokens de pump.fun vistos entre el 16 y el 22 de agosto de 2026. Una fila por token: `t0` (cuándo lo vimos), 29 datos de su ficha en ese momento, y lo que pasó después (`maximo_x`, `final_x` y `dobla`). Las tres últimas columnas son el resultado: **no se pueden usar para decidir**, y el programa no te deja.

Cómo se mide: se entra en la vela siguiente a verlo, ventana de 6 horas, solo tokens con más de 1.000 $ de volumen, y «doblar» es llegar a x2 después de un 3 % de coste al entrar y otro al salir (x2,13 de precio).

Puedes usar tu propia tabla (la libreta del vídeo 15 exportada y medida con el vídeo 16) poniendo su ruta en `FICHAS`.

## Lo que medimos

Media: dobla el 26,1 % en la primera mitad y el 22,8 % en la segunda.

- **Holders entre 150 y 400:** 36,2 % donde se buscó (152 fichas) y 29,5 % donde se comprueba (44 fichas). Se queda a medias, y con 44 fichas no se distingue de la suerte.
- **La mejor regla de 1.052 probadas** (mucho token en manos de los primeros compradores): 49,0 % donde se buscó, **10,0 % donde se comprueba**. La que parecía la mejor es la peor.
- **500 reglas al azar:** entre 32 y 46 «funcionan» donde se buscan, según la tirada. De esas, siguen funcionando 1 o 2.

Son pocas fichas y pocos días, y lo decimos tal cual. Lo que enseña no es qué regla usar: es cómo no engañarte al buscarla.

Esto no es consejo financiero. Es lo que miden nuestros datos.
