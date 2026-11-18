# Bots de Solana 1 · Analizar un contrato con GMGN

Le pasas la dirección de un contrato de Solana y en unos segundos te dice:

1. **La ficha**: precio, capitalización, liquidez, holders y horas de vida.
2. **La seguridad**: si pueden fabricar más tokens o congelarte, cuánto tiene el top 10, snipers, bundlers e insiders.
3. **Si cuadra con DexScreener**: si la liquidez de las dos fuentes no se parece, cuidado.
4. **Quién hay dentro**: los mayores holders, sus etiquetas y **quién le mandó el primer dinero a cada uno**. Si varias billeteras las pagó la misma, seguramente son del mismo dueño.
5. **Quién ha ganado dinero**, quién vende tokens que nunca compró y quién compra y vende contra sí mismo para inflar el volumen.
6. **El dev**: cuántos tokens ha lanzado y quién le pagó la billetera.

> Esto es para **mirar**, no para decidir por ti. Que un contrato salga limpio no significa que vaya a subir. **No es consejo financiero.**

📺 Vídeo: *(enlace cuando se publique)*
📊 Los datos para comprobarlo tú: *(enlace cuando se publiquen)*

---

## Lo que necesitas antes

- **Python 3** instalado. Si no lo tienes: *(enlace al short del canal)*
- **Una clave de GMGN** (gratis). Opcional para probar: sin clave, el programa usa la clave pública de pruebas de GMGN.

### Sacar tu clave de GMGN

1. Entra en **https://gmgn.ai/ai**.
2. Te pide una **clave pública Ed25519**. Si no sabes qué es, pídeselo a Claude con esta frase:
   > Genera un par de claves Ed25519 con OpenSSL y enséñame la clave pública para pegarla en el formulario de GMGN. La privada guárdala en un fichero que no se suba a ningún sitio.
3. Pega la pública en el formulario y te dan tu **API key**.

**Límites (noviembre de 2026, según la documentación de GMGN):** el plan gratis va a unas 5 consultas por segundo; hay planes de pago (Plus y Pro) más rápidos. Si te pasas, GMGN te frena unos minutos, y si insistes durante el castigo, lo alarga. El programa va despacio a propósito.

---

## Instalar y arrancar

```bash
git clone https://github.com/Profesor-Diogenes/Profesor-Diogenes.git
cd Profesor-Diogenes/bots-solana/01-analizar-contrato-gmgn
pip install -r requirements.txt
cp .env.ejemplo .env        # y pega tu clave dentro (o déjalo vacío para probar)
python3 analizar.py <DIRECCION_DEL_CONTRATO>
```

### Si prefieres que lo haga Claude

> Clona https://github.com/Profesor-Diogenes/Profesor-Diogenes, entra en bots-solana/01-analizar-contrato-gmgn, instala lo que pida el requirements.txt, crea el .env a partir del .env.ejemplo y analiza este contrato: <DIRECCION>. Explícame el resultado en castellano sencillo.

---

## Trampas que nos comimos nosotros

- **La capitalización no viene**: hay que multiplicar precio por tokens que existen. El programa lo hace.
- **El primer holder suele ser la pool o la curva**, no una persona. El programa las aparta mirando las pools de DexScreener.
- **Contrasta siempre**: en agosto de 2026 vimos un contrato con 145.000 $ de volumen y liquidez cero en sus tres pools, mientras otra vista de la misma web decía más de 30.000 $.
- **Solo IPv4**: si te da 401 o 403 con la clave bien puesta, mira si tu conexión sale por IPv6.

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
