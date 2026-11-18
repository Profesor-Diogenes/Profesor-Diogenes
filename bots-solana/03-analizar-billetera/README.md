# 03 · Analizar una billetera de Solana

Vídeo 3 de la sección "Bots de Solana" del canal **Profesor Diógenes**.
En los vídeos 1 y 2 mirábamos un contrato. Aquí miramos **a una de las billeteras que hay dentro**: quién es, cómo juega
y de dónde le viene el dinero. Y comprobamos en la propia cadena si lo que dice GMGN es verdad.

## Qué saca

1. **La ficha**: desde cuándo existe, su saldo, las etiquetas que le pone GMGN y cuántos tokens ha creado.
2. **Cómo le va**: lo ganado en 30 días, el porcentaje de aciertos y el reparto de resultados.
3. **Cómo juega**: cuántas operaciones hace por token y cuánto aguanta dentro.
4. **Sus últimos tokens**: cuántos están muertos hoy y en cuántos de esos salió ganando (vendió antes de que se hundieran).
5. **¿Lo que dice GMGN es verdad?**: sus últimas 25 compras y ventas en SOL, una a una en la cadena. Te dice cuántas cuadran y cuáles no.
6. **De dónde le vino el dinero**, según GMGN y comprobado en la cadena.
7. **El veredicto**: normal, bot, víctima, sospechosa o tumbadora (gana en la mayoría de los tokens que se mueren).

## Como bot de Telegram (lo normal)

Para qué sirve: ves una billetera dentro de un contrato (en GMGN, en el bot del vídeo 1 o donde sea), la copias,
se la pegas a TU bot de Telegram y te dice con quién te estás jugando el dinero.

1. Crea tu bot en BotFather (lo explicamos en el Curso de Claude del canal, capítulo 18) y copia su clave.
2. Copia `.env.ejemplo` como `.env` y pega la clave en `TELEGRAM_BOT_TOKEN`.
3. Arranca `python3 bot.py`, escríbele y te dirá tu número de usuario: ponlo en `TELEGRAM_MI_ID`
   y vuelve a arrancarlo. Así solo te contesta a ti.
4. Pégale una billetera. Tarda un par de minutos.

Si lo quieres funcionando las 24 horas, necesitas el ordenador encendido o un servidor en la nube.
Y si no sabes programar, pídeselo a Claude: "Instálame este bot de GitHub, pon la clave de mi bot de Telegram, arráncalo y que se levante solo si se cae".

## A mano, sin Telegram

```
pip install -r requirements.txt
python3 billetera.py <DIRECCION_DE_LA_BILLETERA>
```

## Lo que hay que saber

- Con la clave pública de pruebas de GMGN no se puede pedir la lista de tokens de una billetera: por eso el programa
  la reconstruye con sus últimas 200 operaciones. Es una foto de lo reciente, no de toda su vida.
- "Muerto" = menos de 1.000 $ de liquidez hoy en DexScreener. Puedes cambiarlo arriba del programa.
- El nodo público de Solana deja más o menos una pregunta por segundo **por IP**: abrir más conexiones no sirve.
  Por eso tarda un par de minutos.
- Ahora hay transacciones de "versión 1" en Solana: hay que pedirlas con `maxSupportedTransactionVersion: 1`
  o el nodo no te las da.
- Las billeteras con más de 5.000 movimientos no se pueden seguir hacia atrás en el nodo gratis: son máquinas.
- El veredicto es una etiqueta de lo que se ve en los datos, no una acusación.

## Los datos

Los datos de todos los contratos que hemos guardado están en Hugging Face (enlace en el README general de la sección),
para que cualquiera compruebe con su IA lo que contamos en los vídeos.

**Esto no es consejo financiero.** Es una herramienta para mirar.
