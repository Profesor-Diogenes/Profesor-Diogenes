# 25 · Preparar la tabla para que la lea una máquina

Vídeo 25 de la sección **Bots de Solana** del canal Profesor Diógenes.

Antes de enseñarle nada a un modelo hay que darle una tabla: una fila por token, con lo que se sabía al verlo y lo que pasó después. Parece lo más fácil del mundo. Es donde se cuela casi todo el engaño.

## Qué hace

1. **`/tabla`** — junta nuestros datos (la ficha de cada token y sus velas) y hace `tabla.csv`. Te la manda como fichero.
2. **`/revisa`** — mira cada columna y te dice cuáles separan demasiado. En memes, una columna que acierta mucho casi nunca es un descubrimiento: es que mira el futuro.
3. **`/trampa`** — hace la misma tabla con una columna tramposa metida a propósito, y te enseña cómo la caza `/revisa`.

## Ponerlo en marcha

```
pip install -r requirements.txt
cp .env.ejemplo .env      # y pon dentro la clave de tu bot de Telegram
python3 bot.py
```

Sin Telegram: `python3 tabla.py hacer`, `python3 tabla.py revisa tabla.csv`, `python3 tabla.py trampa`

La primera vez baja de nuestro GitHub (rama `datos`) los dos ficheros que necesita: `libreta.jsonl.gz` (88 MB) y `curvas.jsonl.gz` (3,5 MB).

## Las reglas de la tabla

- La ficha es la **primera** vez que vimos el token. Nada de fotos posteriores.
- Se entra en la vela siguiente a verlo.
- Solo tokens de pump.fun con más de 1.000 $ de volumen.
- «Dobla» es llegar a x2 después de un 3 % de coste al entrar y otro al salir (x2,13 de precio), en 6 horas.

Esta tabla es la misma que usa el vídeo 24 (`fichas.csv`).

## La columna tramposa

`subida_market_cap`: cuánto subió la capitalización entre la primera foto del token y la última que le sacamos en las 6 horas siguientes. Suena a un dato más de la ficha. Pero esa última foto es **del futuro**: cuando decides comprar, todavía no existe.

## Lo que medimos

965 tokens de agosto de 2026. Doblan 236: el 24,5 %. Ese es el número a batir.

- Con la tabla limpia, la columna que más separa (`smart_degen_count`, cuántas billeteras «listas» tenía dentro) da un 32 % en el tercio de arriba: 7,5 puntos más. Las demás, menos de 5.
- Con la columna tramposa: los 111 tokens donde más subió doblan el **61,3 %**. Casi tres veces la media. Si no sabes de dónde sale esa columna, crees que has encontrado la piedra filosofal.

Un modelo entrenado con esa columna saca notas espectaculares en el examen y no sirve para nada en directo, porque en directo esa columna no existe todavía.

Esto no es consejo financiero. Es lo que miden nuestros datos.
