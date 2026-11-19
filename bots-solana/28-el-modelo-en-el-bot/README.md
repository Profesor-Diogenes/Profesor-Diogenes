# 28 · El modelo dentro del bot, en directo

Vídeo 28, el último de la sección **Bots de Solana** del canal Profesor Diógenes.

Todo lo anterior eran pruebas contra el pasado. Esta es la única que vale: el bot apunta hoy lo que compraría, sin poner un euro, y seis horas después mide qué pasó.

## Qué hace

1. **Entrena** el modelo con `tabla.csv` (agosto de 2026), usando solo los 15 datos que GMGN da hoy gratis en su ranking. Si el modelo usa un dato que en directo no tienes, no sirve.
2. **Vigila**: cada 10 minutos lee el ranking de GMGN, le pone nota a cada token nuevo de pump.fun y lo apunta todo, lo elegido y lo no elegido. Si la nota pasa del corte, te avisa: «el modelo lo compraría (en papel)».
3. **`/balance`** — mide lo que ya lleva 6 horas apuntado, con las reglas del vídeo 16, y compara los del modelo con todos y con una moneda al aire. También según lo que te cueste entrar y salir.
4. **`/ultimos`** — los últimos que eligió.

## Ponerlo en marcha

```
pip install -r requirements.txt
cp .env.ejemplo .env      # y pon dentro la clave de tu bot de Telegram
python3 bot.py
```

Sin Telegram: `python3 modelo.py entrena`, `python3 modelo.py vigila`, `python3 modelo.py balance`

Las velas salen de GeckoTerminal gratis, unas 10 por minuto: el balance tarda.

## Lo que nos salió

Una tarde de noviembre de 2026, de mediodía a la noche. El bot apuntó 320 tokens; se pudieron medir 204.

- **Todos:** doblan 27 de 204 (13,2 %). Comprándolos todos, −27,8 % de media.
- **Los que eligió el modelo:** doblan 4 de 52 (7,7 %). Comprándolos, −33,7 % de media.
- **Una moneda al aire** eligiendo 52: entre el 7,7 % y el 19,2 %.
- Con un 10 % de coste a cada lado: −40,8 % los del modelo, −37,9 % todos.

El mismo modelo que en el examen del vídeo 26 sacaba 35 contra 23, en directo saca 8 contra 13. Aprendió una semana de agosto y noviembre no se le parece; en directo solo tiene 15 de los 29 datos; y es una sola tarde, mañana puede salir al revés. Si un día sale cara y otro cruz, no tienes una ventaja.

## Si no sabes programar

Dile a Claude: *"Tengo estos programas de Python. Ayúdame paso a paso a instalarlos en mi ordenador y a crear mi bot de Telegram para usarlos."* y pégale los ficheros.

Esto no es consejo financiero. Es una herramienta para mirar.
