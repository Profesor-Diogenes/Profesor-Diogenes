# 12 · Quién nombra qué token en X

Vídeo 12 de la sección **Bots de Solana** del canal Profesor Diógenes.

Un bot de Telegram que te avisa cuando una cuenta de X (Twitter) nombra un token de Solana. Sin cuenta de X y sin ninguna clave.

## De dónde saca los datos

GMGN tiene en su web un apartado, el **Twitter tracker**, que sigue a miles de cuentas de X y marca en qué mensajes se nombra un token. Este bot lee ese apartado: la misma dirección que usa la web por dentro.

Dos cosas que tienes que saber:

- **No es una API oficial.** GMGN puede cambiarla o cerrarla cuando quiera. Si le preguntas demasiado deprisa, te bloquea un rato. El bot pregunta cada 20 segundos; no lo bajes de 15.
- La web está detrás de Cloudflare y solo contesta a navegadores. Por eso el programa usa `curl_cffi`, que hace la petición con la misma huella que un Chrome de verdad.

Y dos límites: solo salen las cuentas que GMGN sigue, y a veces GMGN le cuelga un token a un mensaje que en realidad no lo nombra.

## Ponerlo en marcha

```
pip install -r requirements.txt
cp .env.ejemplo .env      # y pon dentro la clave de tu bot de Telegram
python3 contratos_x.py
```

## Órdenes

| Orden | Qué hace |
|---|---|
| `/x` | Cómo lo tienes puesto |
| `/seguidores 10000` | Solo cuentas con al menos esos seguidores |
| `/minimo 20000` | Solo tokens que valgan al menos eso (dólares) cuando los nombran |
| `/sigue cuenta` | Avisa solo de esa cuenta (puedes añadir varias) |
| `/quita cuenta` | La quita de la lista (sin ninguna, valen todas) |
| `/repes si` | Avisa también cuando otra cuenta nombra un token que ya te avisó |
| `/ultimos` | Los últimos tokens nombrados y cuántas cuentas llevan |

Todo lo que nombra un token se apunta en `x.csv`, pase o no tus filtros, con la hora y lo que valía en ese momento. La libreta del vídeo 15 lo importa con `/importa`, y el medidor del vídeo 16 te dice qué hicieron después.

## Si no sabes programar

Dile a Claude: *"Tengo este programa de Python, contratos_x.py. Ayúdame paso a paso a instalarlo en mi ordenador y a crear mi bot de Telegram para usarlo."* y pégale el fichero.

Esto no es consejo financiero. Es una herramienta para mirar.
