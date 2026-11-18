# 22 · Quién pagó a quién

Vídeo 22 de la sección **Bots de Solana** del canal Profesor Diógenes. Primer vídeo de la segunda parte.

Le pegas una billetera a tu bot y sigue su dinero: hacia atrás, hacia los lados y hacia delante. Todo con el nodo público de Solana, gratis y sin clave.

## Qué te contesta

1. **Hacia atrás.** Quién le puso el primer SOL, quién se lo puso a ese, y así hasta 6 saltos. Se para al llegar a una billetera con miles de movimientos (una casa de cambio o un repartidor): ahí se pierde el rastro.
2. **Hermanas.** A quién más ha mandado SOL su pagador hace poco. Si el pagador es una persona y no una casa de cambio, es muy probable que sean del mismo bolsillo.
3. **Hijas.** A quién ha mandado SOL esta billetera, y si esas billeteras estaban recién hechas.

## Ponerlo en marcha

```
pip install -r requirements.txt
cp .env.ejemplo .env      # y pon dentro la clave de tu bot de Telegram
python3 bot.py
```

Sin Telegram, para probar: `python3 pagos.py <billetera>`

Tarda cerca de un minuto por billetera, porque el nodo público da una pregunta por segundo. Con tu propio nodo (lo pones en `SOLANA_RPC`), segundos.

## Lo que no ve

- El dinero que pasa por una casa de cambio o por un mezclador. Esconderse cuesta unos céntimos.
- Las billeteras que se pagan con tokens en vez de con SOL.
- Que dos billeteras salgan del mismo pagador **no prueba** que sean de la misma persona. Es una pista.

## Lo que medimos (nuestros datos, agosto de 2026)

De 2.951 tokens recién nacidos miramos sus holders principales: 27.050 holders de los que se sabe quién les puso el primer SOL, pagados por 6.916 billeteras distintas.

- **El 57 % de esos holders los pagaron las mismas 129 billeteras** (las que pagan a holders de 20 tokens o más: repartidores y casas de cambio). Solo 22 billeteras pagaron al 37 %. Una sola pagó a 2.798 holders, en 941 tokens.
- Quitando a esos repartidores, en el 4,9 % de los tokens había al menos dos holders pagados por la misma billetera, y en el 0,8 % cuatro o más.
- ¿Suben menos esos tokens? No se puede decir: solo 59 se pudieron medir bien (volumen real y velas después de la foto), y con grupo había 9. Doblaron 2 de 9, contra 13 de 50 de los que no tenían grupo.

Así que este bot caza al que reparte desde su billetera sin disimular. Al que pasa por una casa de cambio, no lo ves. Y que no veas el grupo no quiere decir que no esté.

## Si no sabes programar

Dile a Claude: *"Tengo estos programas de Python, pagos.py y bot.py. Ayúdame paso a paso a instalarlos en mi ordenador y a crear mi bot de Telegram para usarlos."* y pégale los ficheros.

Esto no es consejo financiero. Es una herramienta para mirar.
