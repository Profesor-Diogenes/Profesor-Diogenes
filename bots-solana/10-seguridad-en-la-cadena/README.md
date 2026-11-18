# 10 · La seguridad de un token, comprobada tú mismo en la cadena

Vídeo 10 de la sección "Bots de Solana" del canal **Profesor Diógenes**.
Le pegas un contrato y en medio minuto te dice, leyéndolo directamente del nodo de Solana:

1. Si alguien puede **fabricar más tokens** (autoridad de acuñar).
2. Si alguien puede **congelar tu billetera** (autoridad de congelar).
3. Si es un token del programa nuevo (Token-2022) y lleva **extensiones peligrosas**: delegado permanente, gancho de
   transferencia, impuesto, no transferible, pausa, cuentas congeladas por defecto.
4. Cuánto tienen **los 10 primeros** (nodo; si corta, GMGN).
5. Si la **liquidez está quemada** (según GMGN, para contrastar).

## Lo que necesitas antes

- **Python 3.10 o más nuevo** y **un bot de Telegram** (BotFather; Curso de Claude, capítulo 18).

## Instalar y arrancar

1. Copia `.env.ejemplo` como `.env` y pon la clave de tu bot.
2. `pip install -r requirements.txt`
3. A mano: `python3 seguridad.py <contrato>`. Con el bot: `python3 bot.py`.

## Lo que hay que saber

- `getTokenLargestAccounts` del nodo público se corta a menudo **por método** (no por IP): por eso los holders se piden a GMGN si falla.
- Lo que medimos (nuestros datos, agosto de 2026): de 11.842 tokens, 11.824 tenían la liquidez quemada. En pump.fun las
  autoridades de acuñar y congelar vienen renunciadas de serie. Este examen **lo aprueban casi todos**, también los que acaban a cero.
- Las reglas típicas de "higiene" funcionaban al revés en 1.583 tokens recién nacidos: los que las cumplían doblaban menos
  (creador con 5 tokens o menos: 0,5 % frente a 2,2 %; pocos francotiradores: 1,4 % frente a 4,9 %; pocos bundlers: 1,4 % frente a 3,6 %).
- Si un token **suspende**, es un no. Si **aprueba**, es lo mínimo, no un sí.

**Esto no es consejo financiero.** Es una herramienta para mirar.
