# 26 · Entrenar un modelo y compararlo con una moneda al aire

Vídeo 26 de la sección **Bots de Solana** del canal Profesor Diógenes.

Le das a una máquina la tabla del vídeo 25 (`tabla.csv`: una fila por token, lo que se sabía al verlo y si dobló en 6 horas), la entrenas y la examinas con tokens que no ha visto. Y la comparas con lo único honrado: elegir los mismos tokens a cara o cruz.

## Qué hace

- **`/entrena`** — parte la tabla en dos **por fecha**: aprende con la mitad antigua y se examina con la nueva. El modelo «compra» el 20 % con mejor nota.
- **`/entrena 60`** — lo mismo aprendiendo con el 60 % más antiguo.

Te dice cuántos doblan de los que eligió el modelo, cuántos doblan de todos, qué saca una moneda al aire eligiendo los mismos, y cuánto ganas o pierdes según lo que te cueste entrar y salir.

## Ponerlo en marcha

```
pip install -r requirements.txt
cp .env.ejemplo .env      # y pon dentro la clave de tu bot de Telegram
python3 bot.py
```

Sin Telegram: `python3 entrenar.py` o `python3 entrenar.py 60`

## Lo que medimos

965 tokens de pump.fun de agosto de 2026. Aprendiendo con la mitad antigua y examinando con la nueva (483 tokens):

- De todos doblan el **22,8 %**.
- De los 96 que elige el modelo doblan el **35,4 %**.
- Una moneda al aire, eligiendo 96, saca entre el 16,7 % y el 29,2 % en 9 de cada 10 tiradas. El modelo queda por encima.

Hasta aquí parece que gana. Ahora los costes. La ganancia media de los que elige el modelo, según lo que pierdas al entrar y otra vez al salir:

| Coste a cada lado | Ganancia media |
|---|---|
| 3 % | +5,7 % |
| 5 % | +2,8 % |
| 8 % | −1,5 % |
| 10 % | −3,0 % |

En estos tokens un 8 o un 10 % por lado es lo corriente. El margen es tan fino que el deslizamiento se lo come. Y la cuenta vende justo en el máximo, que en la vida real no te lo dan.

En el vídeo 28 este mismo modelo se pone a funcionar en directo. Mira lo que pasa.

## Si no sabes programar

Dile a Claude: *"Tengo estos programas de Python. Ayúdame paso a paso a instalarlos en mi ordenador y a crear mi bot de Telegram para usarlos."* y pégale los ficheros.

Esto no es consejo financiero. Es una herramienta para mirar.
