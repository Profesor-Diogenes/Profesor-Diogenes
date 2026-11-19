# 23 · El grafo de billeteras

Vídeo 23 de la sección **Bots de Solana** del canal Profesor Diógenes.

Le pegas un contrato a tu bot y te manda **una imagen**: el mapa de quién pagó a quién entre los 100 mayores holders de ese token. Y debajo, el detalle en texto.

## Cómo se lee el dibujo

- **Círculo** = un holder. Cuanto más grande, más token tiene.
- **Rombo** = la billetera que le puso el primer SOL.
- **Arriba, en colores**: los grupos. Varios holders pagados por la misma billetera.
- **Abajo, en gris**: los holders sin grupo. Van por su cuenta, o vienen de una casa de cambio.

## De dónde saca los datos

- Los holders y quién pagó a cada uno: GMGN (vale la clave pública de pruebas).
- Dos comprobaciones con el nodo público de Solana, gratis:
  - **¿El pagador es un repartidor?** Si tiene miles de movimientos, paga a medio mundo y no hace grupo. Sin esta comprobación el mapa miente: salen "grupos" que son gente que no se conoce de nada y sacó el dinero del mismo sitio.
  - **Un paso más atrás.** Si a dos pagadores los pagó la misma billetera, sus grupos se juntan en uno.

Si quieres ver el mapa ingenuo, sin la primera comprobación, arranca con `SIN_FILTRO=1`. Sirve para entender cuánto engaña.

## Ponerlo en marcha

```
pip install -r requirements.txt
cp .env.ejemplo .env      # y pon dentro la clave de tu bot de Telegram
python3 bot.py
```

Sin Telegram: `python3 grafo.py <contrato>` y te deja la imagen en esta carpeta.

Tarda entre 15 segundos y un minuto.

## Lo que no ve

Los grupos que se pagan a través de una casa de cambio. **Un mapa limpio no es un token limpio.**

## Si no sabes programar

Dile a Claude: *"Tengo estos programas de Python, grafo.py y bot.py. Ayúdame paso a paso a instalarlos en mi ordenador y a crear mi bot de Telegram para usarlos."* y pégale los ficheros.

Esto no es consejo financiero. Es una herramienta para mirar.
