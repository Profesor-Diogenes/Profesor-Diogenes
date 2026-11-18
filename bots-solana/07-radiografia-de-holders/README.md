# 07 · Radiografía de los holders: granjas, supply escondido y repartos calcados

Vídeo 7 de la sección "Bots de Solana" del canal **Profesor Diógenes**.
Le pegas un contrato a tu bot y te dice cuánto del token está en manos de un mismo bolsillo.

## Qué mira

1. **Granjas**: holders a los que les mandó el primer SOL la misma billetera. Y un paso más atrás, en el nodo de Solana:
   si dos pagadores los pagó a su vez la misma billetera, se juntan en la misma banda. Si el que paga es un exchange
   (Binance, OKX…), no cuenta: paga a millones de personas.
2. **Supply escondido**: billeteras que tienen el token y no lo han comprado nunca (se lo pasaron), o que lo han ido
   sacando a otras billeteras.
3. **Repartos calcados**: tres o más billeteras con exactamente el mismo % del supply (a tres decimales). Eso es un reparto a mano.

## Lo que necesitas antes

- **Python 3.10 o más nuevo.**
- **Un bot de Telegram y su clave** (BotFather). Lo enseñamos en el Curso de Claude, capítulo 18.
- **Clave de GMGN** (opcional): sin clave usa la pública de pruebas de GMGN. La tuya se saca gratis en https://gmgn.ai/ai

## Instalar y arrancar

1. Copia `.env.ejemplo` como `.env` y pon la clave de tu bot.
2. `pip install -r requirements.txt`
3. A mano: `python3 radiografia.py <contrato>`. Con el bot: `python3 bot.py` y le pegas el contrato.
   Escríbele y te dirá tu número de usuario: ponlo en `TELEGRAM_MI_ID` y vuelve a arrancarlo.

Tarda alrededor de un minuto: al nodo público de Solana se le pregunta despacio (unas 100 preguntas cada 10 segundos por IP).
Si no sabes programar, pídeselo a Claude: "Instálame este bot de GitHub, pon la clave de mi bot de Telegram, arráncalo y que se levante solo si se cae".

## Lo que hay que saber

- GMGN solo da los holders **de ahora**: los que compraron y ya se fueron del todo no aparecen.
- Lo que medimos (nuestros datos, agosto de 2026): un top 10 concentrado **no predice** si un token sube
  (menos del 10 % en el top: 24,1 % llegaban a doblar; más del 30 %: 25,5 %). Y en tokens recién nacidos, la regla de
  "pocos bundlers" funcionaba al revés (1,4 % doblaban cumpliéndola, 3,6 % sin cumplirla).
- Esta radiografía te dice **quién puede tirarte el precio encima**, no si el token va a subir.

**Esto no es consejo financiero.** Es una herramienta para mirar.
