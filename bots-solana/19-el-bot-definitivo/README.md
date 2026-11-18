# 19 · El bot definitivo

Vídeo 19 de la sección **Bots de Solana** del canal Profesor Diógenes.

Todas las piezas de la serie en un solo bot de Telegram, con menú y botones. Un solo bot, una sola clave, un solo chat.

## Qué es (y qué no)

Aquí no hay análisis nuevo. Este programa es una **centralita**: arranca los programas de los vídeos anteriores y reparte entre ellos lo que tú escribes. Por eso necesitas la serie entera bajada, con cada carpeta en su sitio, al lado de esta.

Lo que **no** hay:

- **Ninguna inteligencia artificial.** El bot mira, apunta, avisa y juega en papel. Decidir, decides tú. (Por qué, en el vídeo 18.)
- **Ninguna compra de verdad.** Las compras son en papel (vídeo 17).
- **El lector de grupos de Telegram** (vídeo 6). Ese pide iniciar sesión con tu cuenta y va aparte.

## Ponerlo en marcha

```
pip install -r requirements.txt
cp .env.ejemplo .env      # y pon dentro la clave de tu bot de Telegram
python3 definitivo.py
```

## Cómo se usa

**Pegas un contrato o una billetera** y el bot te pregunta con botones qué quieres hacer:

| Botón | Qué hace | Vídeo |
|---|---|---|
| 🔎 Ficha | La ficha del token | 1 |
| 🔐 Seguridad | Quién puede acuñar, congelar, liquidez | 10 |
| 🩻 Holders | Cómo está repartido | 7 |
| 👤 El dev | Qué ha hecho quien lo creó | 8 |
| ⛓ Por dentro | El contrato leído del nodo | 2 |
| 👛 Analizar billetera | Qué ha hecho esa billetera | 3 |
| 👁 Seguir billetera | La mete en el vigía | 11 |
| 🔻 Vigilar ventas | Avisa de ventas gordas de ese token | 13 |
| 📒 Apuntar | Lo guarda en la libreta | 15 |
| 📝 Comprar en papel | Lo compra de mentira con tu plan | 17 |

**Con `/menu`** ves las secciones, con una luz verde si están encendidas: vigía de billeteras, tokens que nacen, señales, X, ventas gordas, criba, libreta, medir y papel. Entras en una y sus órdenes son las de su vídeo (te las recuerda al entrar).

| Orden | Qué hace |
|---|---|
| `/menu` | Las secciones |
| `/estado` | Qué piezas están encendidas |
| `/apaga senales` | Apaga una pieza: deja de avisar y de gastar preguntas |
| `/junta` | Mete en la libreta todo lo que han apuntado las demás piezas |

Las piezas se encienden solas la primera vez que las usas. La libreta y el papel arrancan encendidas. Lo que dejas encendido se guarda en `definitivo.json` y vuelve a arrancar la próxima vez.

## El límite que vas a notar

Todas las piezas tiran de las mismas fuentes gratis: el nodo público de Solana da una pregunta por segundo, y GMGN y GeckoTerminal también cortan. Si pides dos cosas seguidas del mismo contrato, alguna te contestará "no contesta". Si enciendes todas las secciones a la vez, se estorban entre ellas.

Enciende lo que estés usando y apaga lo demás. Con tu propio nodo (lo pones en el `.env`) mejora mucho.

Si una pieza falla, lo que dijo está en `pieza_<nombre>.log`, en esta carpeta.

## Si no sabes programar

Dile a Claude: *"Tengo esta carpeta con programas de Python, bots-solana. Ayúdame paso a paso a instalarlo en mi ordenador, a crear mi bot de Telegram y a arrancar el de la carpeta 19."*

Esto no es consejo financiero. Es una herramienta para mirar.
