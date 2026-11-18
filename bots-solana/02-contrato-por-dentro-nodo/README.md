# 02 · Mirar un contrato de Solana por dentro (gratis y sin clave)

Vídeo 2 de la sección "Bots de Solana" del canal **Profesor Diógenes**.
En el vídeo 1 mirábamos un contrato con GMGN. Aquí miramos **el mismo contrato por dentro**, sin depender de nadie:
la propia cadena de Solana (nodo público), pump.fun, GeckoTerminal y DexScreener. Todo gratis, sin registrarte.

## Qué saca

1. **pump.fun**: el creador, el máximo histórico con su hora, si ya salió de la curva, si está bloqueado.
2. **La gráfica minuto a minuto** (GeckoTerminal): cuándo tocó el máximo, cuántos minutos después de nacer y cuánto ha caído.
3. **El censo de holders contado en la cadena**, apartando las pools.
4. **Las primeras compras en orden**, con los segundos desde que nació el contrato.
5. **Seguir el dinero hacia atrás**: quién le puso el primer SOL a cada uno de los 8 más gordos, y quién a ese, hasta 3 saltos. Si varios salen del mismo sitio, avisa.
6. **¿Cuadra con GMGN?** Compara holders y creador (con la clave pública de pruebas de GMGN o la tuya).

## Como bot de Telegram (lo normal)

Para qué sirve: estás en el ordenador mirando memes en la plataforma que uses, copias un contrato,
se lo pegas a TU bot de Telegram y te lo analiza con tus reglas, también desde el móvil.

1. Crea tu bot en BotFather (lo explicamos en el Curso de Claude del canal, capítulo 18) y copia su clave.
2. Copia `.env.ejemplo` como `.env` y pega la clave en `TELEGRAM_BOT_TOKEN`.
3. Arranca `python3 bot.py`, escríbele y te dirá tu número de usuario: ponlo en `TELEGRAM_MI_ID`
   y vuelve a arrancarlo. Así solo te contesta a ti.
4. Pégale un contrato.

Si lo quieres funcionando las 24 horas, necesitas el ordenador encendido o un servidor en la nube.
Y si no sabes programar, pídeselo a Claude: "Instálame este bot de GitHub, arráncalo y que se levante solo si se cae".

## A mano, sin Telegram


```
pip install -r requirements.txt
python3 por_dentro.py <DIRECCION_DEL_CONTRATO>
```

Tarda de 1 a 3 minutos. **Es lento a propósito**: el nodo público de Solana deja más o menos
una pregunta por segundo por IP (abrir más conexiones desde la misma IP no sirve: cuentan juntas), y si corres te corta un rato.

Si tienes tu propio nodo (Helius, Alchemy, QuickNode…), pon su dirección en un fichero `.env`
o en la variable `SOLANA_RPC` (mira `.env.ejemplo`). Si tienes clave de GMGN, en `GMGN_API_KEY`.

## Lo que hay que saber

- El censo del nodo público va con algo de retraso: puede diferir un poco de lo que ves en otras webs.
- Las billeteras con más de 5.000 movimientos no se siguen hacia atrás: son máquinas y su principio queda muy lejos.
- Si el contrato tiene más de 40.000 movimientos, no llegamos a las primeras compras de verdad: el programa te lo dice.
- pump.fun está detrás de Cloudflare: por eso se usa `curl_cffi`, que se presenta como un navegador normal.

## Los datos

Los datos de todos los contratos que hemos guardado están en Hugging Face (enlace en el README general de la sección),
para que cualquiera compruebe con su IA lo que contamos en los vídeos.

**Esto no es consejo financiero.** Es una herramienta para mirar.
