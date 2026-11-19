# 27 · Por qué el modelo se engaña

Vídeo 27 de la sección **Bots de Solana** del canal Profesor Diógenes.

El mismo modelo del vídeo 26, con la misma tabla, examinado de cuatro maneras. En las cuatro se mira lo mismo: de los tokens que el modelo pone arriba, cuántos doblaron. Tres de las cuatro te mienten.

## Qué hace

**`/engano`** hace las cuatro. También una a una: `/engano memoria`, `/engano azar`, `/engano trampa`, `/engano fecha`.

| Manera | Qué hace | Doblan los elegidos |
|---|---|---|
| De memoria | Lo examinas con las mismas fichas con las que aprendió | 100 % |
| Al azar | Partes la tabla al azar en vez de por fecha: mezcla días | 38,3 % |
| Con trampa | Le dejas dentro la columna del vídeo 25 que mira el futuro | 53,1 % |
| Por fecha | Aprende con lo antiguo, se examina con lo nuevo, sin trampas | 35,4 % |

La honrada es la peor nota de las cuatro, y es la única que se parece a lo que te pasaría a ti.

## Ponerlo en marcha

```
pip install -r requirements.txt
cp .env.ejemplo .env      # y pon dentro la clave de tu bot de Telegram
python3 bot.py
```

Sin Telegram: `python3 engano.py` o `python3 engano.py memoria`

Lleva dentro `tabla.csv` (la limpia) y `tabla_trampa.csv` (con la columna tramposa `subida_market_cap`).

## Con qué quedarte

Cuanto mejor sale un examen, más hay que desconfiar. Cuando alguien te enseñe un modelo que acierta muchísimo, pregúntale con qué fichas lo examinó.

## Si no sabes programar

Dile a Claude: *"Tengo estos programas de Python. Ayúdame paso a paso a instalarlos en mi ordenador y a crear mi bot de Telegram para usarlos."* y pégale los ficheros.

Esto no es consejo financiero. Es una herramienta para mirar.
