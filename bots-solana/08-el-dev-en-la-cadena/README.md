# 08 · El dev en la cadena: de dónde le viene el dinero y a dónde lo manda

Vídeo 8 de la sección "Bots de Solana" del canal **Profesor Diógenes**.
Le pegas un contrato de pump.fun y te dice: quién lo creó, cuánto SOL le ha entrado y ha sacado, quién le paga,
a quién paga él, si se ha comprado su propio token y si alguna billetera que pagó está entre los mayores holders.

## De dónde sale cada cosa (todo gratis)

- **pump.fun**: el creador con su dirección completa, y la curva y el pool del token. Está detrás de Cloudflare:
  se usa `curl_cffi`, que se hace pasar por un navegador. La ruta cambia de vez en cuando (el 17-nov-2026 pasó de
  `coins-v2` a `coins-v3`): el programa prueba las dos.
- **Nodo público de Solana**: las últimas `OPERACIONES` (40) del creador, una a una, con cada SOL que entra y sale.
  Y de cada billetera con la que se mueve, cuántos movimientos tiene y qué saldo le queda.
- **GMGN** (vale la clave pública de pruebas): los mayores holders, para cruzarlos.

## Lo que necesitas antes

- **Python 3.10 o más nuevo.**
- **Un bot de Telegram y su clave** (BotFather). Curso de Claude, capítulo 18.

## Instalar y arrancar

1. Copia `.env.ejemplo` como `.env` y pon la clave de tu bot.
2. `pip install -r requirements.txt`
3. A mano: `python3 dev.py <contrato>`. Con el bot: `python3 bot.py`.

Tarda un minuto y medio: el nodo gratis contesta más o menos una pregunta por segundo por IP.
Si no sabes programar, pídeselo a Claude: "Instálame este bot de GitHub, pon la clave de mi bot de Telegram, arráncalo y que se levante solo si se cae".

## Lo que hay que saber

- Solo ve las últimas operaciones del creador y los pagos directos (un salto). Más lejos no lo ve.
- Lo que medimos (nuestros datos, agosto de 2026): cuántos tokens ha lanzado el creador **no cambia nada**
  (0-1 tokens: 23,2 % llegaban a doblar; 50 o más: 27,7 %). En tokens recién nacidos, "solo creadores con 5 tokens o menos"
  funcionaba al revés (0,5 % frente a 2,2 %).

**Esto no es consejo financiero.** Es una herramienta para mirar.
