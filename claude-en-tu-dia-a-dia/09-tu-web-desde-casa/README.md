# Claude en tu día a día 9: tu propia web desde tu casa sin abrir puertas a internet

▶️ Vídeo: (enlace en la descripción del canal)

## Qué hace

Una web sencilla con tres páginas (portada, privacidad y condiciones, las que te piden algunas plataformas para dejarte usar su API), servida desde un ordenador de tu casa **sin abrir ningún puerto del router**:

- El **servidor web** (nginx, gratuito) escucha **solo dentro de la máquina** (`127.0.0.1`). Desde internet nadie llega a él directamente.
- La gente llega por un **túnel**: un programa de tu ordenador que se conecta **hacia fuera** a un proveedor. Cuando alguien escribe tu dominio, el proveedor se lo manda por ese túnel. En el vídeo usamos el de Cloudflare (`cloudflared`).
- Dos ayudantes en Python: uno **prueba la web con un navegador sin pantalla** y saca una captura de cada página, y otro **lee las reglas del túnel** y te dice a qué apunta cada una y si hay algo escuchando detrás.

Las páginas son **de ejemplo**. Claude te da la estructura, pero lo que haces de verdad con los datos lo pones tú (hay huecos marcados en `privacidad.html` y `condiciones.html`).

## La frase para Claude

> Móntame una web estática con portada, privacidad y condiciones, en mi servidor. Que escuche solo dentro de la máquina y salga por un túnel, sin abrir puertos. Pruébala con un navegador sin pantalla y mándame capturas. Y dime a qué apunta cada regla del túnel.

## Lo que necesitas antes

- **Python 3.10 o más nuevo** (gratis). Entra en [python.org/downloads](https://www.python.org/downloads/), baja la última versión e instálala. En Windows, **marca la casilla *Add python.exe to PATH*** antes de pulsar *Install*. Para comprobarlo, abre una terminal y escribe `python --version` (en Mac y Linux, `python3 --version`): tiene que salir 3.10 o un número mayor.
- **Un ordenador en casa que esté siempre encendido** (vale uno viejo). Qué es y por qué lo necesitas: **Curso de Claude 14: qué es un servidor y por qué lo necesitas con Claude** → [`curso-de-claude/14-que-es-un-servidor`](../../curso-de-claude/14-que-es-un-servidor/); cómo prepararlo y entrar seguro: **Curso de Claude 15: prepara tu servidor y entra seguro (red privada y cortafuegos)** → [`curso-de-claude/15-prepara-tu-servidor-y-entra-seguro`](../../curso-de-claude/15-prepara-tu-servidor-y-entra-seguro/). Para probar, te vale tu propio ordenador.
- **nginx** (gratis). Descarga oficial: [nginx.org/en/download.html](https://nginx.org/en/download.html) (en Windows, baja el zip de la versión *Stable* y descomprímelo: [nginx.org/en/docs/windows.html](https://nginx.org/en/docs/windows.html)). En Mac, `brew install nginx`; en Ubuntu o Debian, `sudo apt install nginx`. Para probar sin instalar nada, mira el paso 2 de *Cómo se usa*.
- **El navegador sin pantalla (Playwright)** para `probar.py`. Qué es: **Curso de Claude 33: un navegador que va solo para las webs que se rellenan (Playwright)** → [`curso-de-claude/33-navegador-que-va-solo-playwright`](../../curso-de-claude/33-navegador-que-va-solo-playwright/). Se instala con el `requirements.txt` y una orden más (paso 1).
- **Para publicarla de verdad: una cuenta de Cloudflare, un dominio y `cloudflared`.** Ningún capítulo lo enseña paso a paso todavía. En corto, con la guía oficial ([developers.cloudflare.com/tunnel](https://developers.cloudflare.com/tunnel/) y la de un túnel gestionado desde tu ordenador, [crear un túnel local](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/local-management/create-local-tunnel/)):
  1. Crea una cuenta en [cloudflare.com](https://www.cloudflare.com/plans/) (tiene plan gratis; según su documentación, el túnel está *disponible en todos los planes*).
  2. **El dominio sí se paga** (es un alquiler al año). Si ya tienes uno, lo añades a Cloudflare y cambias sus servidores de nombres ([añadir un sitio](https://developers.cloudflare.com/fundamentals/manage-domains/add-site/)); si no, lo puedes registrar desde el propio panel ([Cloudflare Registrar](https://developers.cloudflare.com/registrar/)) o en cualquier otro registrador.
  3. Instala `cloudflared` ([descargas oficiales](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/downloads/)) y, en la terminal: `cloudflared tunnel login` (te abre el navegador para entrar), `cloudflared tunnel create NOMBRE` (te da el archivo `.json` de credenciales: **es una llave, no se comparte**), y `cloudflared tunnel route dns NOMBRE web.tudominio.es`.
  4. **Método de pago, facturas y gasto**: en el panel de Cloudflare, en la parte de facturación (*Billing*) de tu cuenta: ahí pones o cambias la tarjeta, ves las facturas y la renovación del dominio. Guía oficial: [developers.cloudflare.com/billing](https://developers.cloudflare.com/billing/).

  Si usas otro proveedor de túneles, la idea es la misma: un programa que sale hacia fuera y un archivo de reglas; pídele a Claude que lo adapte con su documentación.

## Qué hay en la carpeta

| Archivo | Para qué |
|---|---|
| `web/` | Las tres páginas (`index.html`, `privacidad.html`, `condiciones.html`) y la hoja de estilo `estilo.css`. Solo archivos: sin base de datos ni programa detrás. |
| `nginx.conf` | El servidor web, escuchando solo en `127.0.0.1:8099`. |
| `config.yml` | El archivo de reglas del túnel, **de ejemplo** (dominios `example.com`, que no son de nadie). Lleva a propósito una regla que apunta a un puerto donde no escucha nadie. |
| `probar.py` | Abre las tres páginas con un navegador sin pantalla, mira que responden y saca una captura de cada una en `capturas/`. |
| `revisar_reglas.py` | Lee las reglas del túnel una por una y te dice si hay algo escuchando en cada puerto, si hay nombres repetidos, si una general tapa a una concreta y si falta el 404 final. |
| `logs/` y `temp/` | Donde nginx guarda su registro y sus temporales (tienen que existir). |

## Cómo se usa

**1. Instala lo necesario** (una vez), abriendo una terminal en esta carpeta:

```
pip install -r requirements.txt
python -m playwright install chromium
```

**2. Arranca el servidor web**, desde esta carpeta:

```
nginx -p . -c nginx.conf
```

(En Windows, `nginx.exe -p . -c nginx.conf` con la ruta a tu `nginx.exe`.) Para pararlo: `nginx -p . -c nginx.conf -s stop`.

¿Solo quieres probar y no tienes nginx? Python trae un servidor de juguete que también escucha solo dentro de la máquina: `python -m http.server 8099 --bind 127.0.0.1 --directory web` (se para con `Ctrl+C`). Para tenerla publicada, mejor nginx.

Abre `http://127.0.0.1:8099/` en tu navegador: tiene que salir la portada. Desde otro aparato de tu casa **no** tiene que abrir: es lo que queremos.

**3. Pruébala con el navegador sin pantalla:**

```
python probar.py
```

Si va bien verás las tres páginas con `200` y su título (`Portada · Web de ejemplo`, `Privacidad · …`, `Condiciones · …`), `Todo bien: tres páginas, tres capturas.` y las tres fotos en la carpeta `capturas/`. Si el servidor no está arrancado, sale `NO RESPONDE`. Cuando el túnel funcione, pruébala por fuera: `python probar.py https://web.tudominio.es/`.

**4. Revisa las reglas del túnel:**

```
python revisar_reglas.py
```

Con el `config.yml` de ejemplo y nginx arrancado verás `#0 web.example.com -> 127.0.0.1:8099  OK, escucha`, `#1 blog.example.com -> 127.0.0.1:8098  NADIE ESCUCHA` y, abajo, el aviso de que esa regla manda a un puerto donde no hay nada.

**5. Pon tus reglas y arranca el túnel.** Antes de tocar `config.yml`, **haz una copia con fecha**:
- **Windows**: `copy config.yml config.yml.bak_2026-11-09`
- **Mac / Linux**: `cp config.yml config.yml.bak_$(date +%F)`

Cambia `tunnel:` por el nombre de tu túnel, `credentials-file:` por la ruta del `.json` que te dio `tunnel create`, y los `hostname:` por los tuyos: **las concretas arriba, la general abajo, y al final el 404**. Comprueba con `cloudflared tunnel --config config.yml ingress validate` (tiene que decir `OK`) y a qué regla va un nombre con `cloudflared tunnel --config config.yml ingress rule https://web.tudominio.es`. Luego arráncalo: `cloudflared tunnel --config config.yml run`.

Para que nginx y el túnel sigan funcionando al reiniciar el ordenador, que arranquen solos: lo explica, para un bot, **Curso de Claude 21: que tu bot funcione 24 horas y se levante solo** → [`curso-de-claude/21-bot-24-horas`](../../curso-de-claude/21-bot-24-horas/); para el túnel, `cloudflared service install` según su guía oficial.

## Cómo lo compruebas

Pídele a Claude (o ejecuta tú `python revisar_reglas.py`) que lea las reglas **una por una** y te diga si hay algo escuchando en cada puerto. En nuestro servidor, dos túneles declaraban el mismo nombre y uno mandaba a un puerto donde ya no escuchaba nadie: a uno de cada dos visitantes le habría salido la nada. Y abre `capturas/` para ver las tres páginas sin salir del chat.

## Los tres fallos

1. **Claude deja el servidor web escuchando para todo el mundo**, o te dice que abras un puerto en el router. Corrección: que escuche solo dentro de la máquina (`listen 127.0.0.1:…`) y que salga por el túnel.
2. **Pone la regla general arriba**, y la concreta no se usa nunca (gana la primera que encaja). Corrección: las concretas, primero; la general, abajo; y el 404, al final.
3. **Toca el archivo del túnel sin guardar una copia**, y si algo se rompe no hay vuelta atrás. Corrección: una copia con fecha antes de cada cambio.

---

Esto no es consejo financiero y aquí no se señala a nadie.
