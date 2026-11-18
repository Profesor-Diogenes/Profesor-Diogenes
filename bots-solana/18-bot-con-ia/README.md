# 18 · Un bot con una IA dentro (y el examen que no pasa)

Vídeo 18 de la sección **Bots de Solana** del canal Profesor Diógenes.

Dos programas:

- **`ia.py`** — el bot de Telegram. Le pegas un contrato, recoge la ficha en GMGN y le pide opinión a la IA que tú elijas.
- **`examen.py`** — le pasa a esa IA fichas de tokens reales de los que ya se sabe qué hicieron, y cuenta cuántas acierta.

La IA aquí **opina**. No decide ni compra nada.

## Qué IA usa

La que pongas en el `.env`, con tres líneas: `IA_URL`, `IA_MODELO`, `IA_CLAVE`. Vale cualquiera que hable el idioma de OpenAI, que son casi todas:

| | IA_URL |
|---|---|
| En tu ordenador, gratis, con [Ollama](https://ollama.com) | `http://localhost:11434/v1` |
| OpenAI | `https://api.openai.com/v1` |
| Gemini | `https://generativelanguage.googleapis.com/v1beta/openai` |
| Grok | `https://api.x.ai/v1` |
| Claude | `https://api.anthropic.com/v1` |

## Ponerlo en marcha

```
pip install -r requirements.txt
cp .env.ejemplo .env      # la clave de tu bot y las tres líneas de la IA
python3 ia.py             # el bot
python3 examen.py 200     # el examen, sin Telegram, con las 200 primeras fichas
```

## Órdenes del bot

| Orden | Qué hace |
|---|---|
| (pegar un contrato) | Ficha de GMGN y lo que opina la IA |
| `/modelo` | Con qué IA está hablando |
| `/examen 100` | Examina a la IA con 100 tokens reales |

## El examen

`examen.json` trae 965 tokens de pump.fun que vimos en agosto de 2026. De cada uno, la ficha tal como estaba **en el momento de verlo** (capitalización, liquidez, holders, bundlers, el creador…) y si llegó a doblar en las 6 horas siguientes. Sin contratos y sin nada de lo que pasó después. Solo cuentan los que movieron dinero de verdad (más de 1.000 dólares), y se entra en la vela siguiente a verlo.

**Doblaron 236 de 965: el 24,5 %.** Eso es lo que aciertas comprando a ciegas.

Lo que sacaron los modelos que probamos nosotros en noviembre de 2026, preguntando "¿doblará en las próximas 6 horas?":

| Modelo | Dijo SÍ | De esos, doblaron |
|---|---|---|
| qwen2.5 de 14b, en local | 313 de 965 | 24,9 % |
| gpt-oss de 20b, en local | 180 de 400 | 23,9 % |
| Gemini Pro | 17 de 400 | 23,5 % |
| Claude Sonnet | 199 de 965 | 28,1 % |

Ninguno se separa de tirar una moneda, y ninguno llega al 35 % que hace falta para no perder dinero entrando con objetivo de doblar y corte a la mitad. Cuando dicen NO, los tokens doblan igual que la media.

No te lo creas: pásale el examen a tu modelo.

## Si no sabes programar

Dile a Claude: *"Tengo estos dos programas de Python, ia.py y examen.py. Ayúdame paso a paso a instalarlos en mi ordenador, a crear mi bot de Telegram y a conectarles una IA."* y pégale los ficheros.

Esto no es consejo financiero. Es una herramienta para mirar.
