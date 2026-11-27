# Claude en tu día a día 7: publicar un vídeo en todas tus redes a la vez

▶️ Vídeo: (enlace en la descripción del canal)

## Qué hace

Subir el mismo vídeo a YouTube, Instagram, TikTok y X una por una es una tarde perdida. Hay servicios de pago que publican por ti: subes el vídeo una vez, con una sola API, y le dices a qué redes va.

Este programa lee **tu calendario** (qué sale y cuándo, con su zona horaria) y **un texto por red**, lo revisa antes de mandar nada (enlaces en X, topes de cada día, repetidos en menos de 48 horas), lo programa y **guarda el número** que devuelve el servicio por cada publicación. Si una subida tarda, **pregunta su estado: nunca la repite**.

Está hecho para **Upload-Post**, el servicio que sale en el vídeo .2. No es el único: si usas otro, pásale a Claude `publicar.py` y la documentación de tu servicio para que lo adapte. Las reglas del capítulo valen igual.

## La frase para Claude

> Escríbeme un programa que publique mis vídeos en mis redes con la API de un servicio. Lee mi calendario y un texto por red, sin enlaces en equis. Guarda el número de cada programación. Si una subida tarda, pregunta su estado: nunca la repitas.

## Lo que necesitas antes

- **Python 3.10 o más nuevo** (gratis). Entra en [python.org/downloads](https://www.python.org/downloads/), baja la última versión e instálala. En Windows, **marca la casilla *Add python.exe to PATH*** antes de pulsar *Install*. Para comprobarlo, abre una terminal y escribe `python --version` (en Mac y Linux, `python3 --version`): tiene que salir 3.10 o un número mayor.
- **Una cuenta de Claude** (vale la gratis). Cómo se crea y qué plan te sirve: **Curso de Claude 1: qué es Claude y cuál te sirve (desde cero)** → [`curso-de-claude/01-que-es-claude`](../../curso-de-claude/01-que-es-claude/).
- **Tus cuentas en las redes** (YouTube, Instagram, TikTok, X…). Para publicar por API, **Instagram tiene que ser una cuenta profesional** (de empresa o de creador). Se cambia gratis en la app: guía oficial en [help.instagram.com/502981923235522](https://help.instagram.com/502981923235522).
- **Una cuenta en un servicio de publicación y su clave de API.** Ningún capítulo enseña todavía a sacarla. Si usas Upload-Post, se hace así (documentación oficial: [docs.upload-post.com/quickstart](https://docs.upload-post.com/quickstart)):
  1. **Alta**: en [app.upload-post.com/signup](https://app.upload-post.com/signup), con Google o con tu correo. El plan gratis no pide tarjeta.
  2. **Conecta tus redes**: en [*User Management*](https://app.upload-post.com/manage-users) crea un perfil con el nombre que quieras (**ese nombre va en `UPLOAD_POST_PERFIL`**), pulsa en cada red, entra con tu cuenta y acepta todos los permisos.
  3. **La clave**: en [*API Keys*](https://app.upload-post.com/api-keys) → *Generate New API Key*. Cópiala y guárdala en el `.env` (paso 3 de *Cómo se usa*). **Nunca en el código ni en un chat.** Por qué y cómo se guardan las claves: **Curso de Claude 35: qué es una API y cómo guardar sus claves sin que te las roben** → [`curso-de-claude/35-que-es-una-api-y-guardar-claves`](../../curso-de-claude/35-que-es-una-api-y-guardar-claves/).
- **Lo que cuesta** (precios oficiales en [upload-post.com/pricing](https://www.upload-post.com/pricing), comprobados en noviembre de 2026; pueden cambiar): el plan gratis da **10 subidas al mes, sin TikTok**. Los de pago (desde 24 $ al mes, o 16 $ al mes si pagas el año) tienen subidas ilimitadas y TikTok. No es saldo que se recarga: es una **cuota mensual**.
  - **Pagar, cambiar la tarjeta o ver facturas**: en el panel, *My Profile* → *Open Billing Portal* (ahí, *Payment methods* para la tarjeta e *Invoice History* para las facturas). Para darte de baja, *My Profile* → *Cancel Subscription*.
  - **Lo que llevas gastado**: con el plan gratis, cada subida te devuelve cuántas llevas del mes, y si te pasas el servicio responde `This upload would exceed your monthly limit`. Si cancelas una programación que aún no ha salido, te devuelve esas subidas.

## Qué hay en la carpeta

| Archivo | Para qué |
|---|---|
| `publicar.py` | El programa: `revisar`, `programar`, `estado`, `lista` y `cancelar`. |
| `calendario.csv` | **Tu** calendario: vídeo, fecha, hora, zona horaria y redes. El de ejemplo es inventado. |
| `textos.json` | Un texto por vídeo y por red. En X, sin enlaces; en Instagram y TikTok, "enlace en el perfil". |
| `videos/` | Aquí pones tus vídeos, con el mismo nombre que en el calendario. |
| `.env.ejemplo` | Para tu clave y tu perfil. Cópialo a `.env`. |
| `numeros.json` | Lo crea el programa: el número de cada programación. **No lo borres**: sin ese número no puedes tocarla. |

## Cómo se usa

**1. Instala lo necesario** (una vez), abriendo una terminal en esta carpeta:

```
pip install -r requirements.txt
```

**2. Revisa sin mandar nada** (no necesita clave):

```
python publicar.py revisar
```

Mira los textos red por red, que cada fila tenga fecha, hora y **zona horaria** y que no haya pasado, **cuántas salen cada día en cada red** contra el tope de esa red, y los **repetidos** (mismo vídeo y misma red en menos de 48 horas). Si todo está bien, acaba con `Todo bien: puedes programar.` Si no, te dice qué arreglar. Las fechas del ejemplo son de diciembre de 2026: cámbialas por las tuyas.

**3. Copia `.env.ejemplo` a `.env`** y rellena:
- `UPLOAD_POST_CLAVE`: tu clave.
- `UPLOAD_POST_PERFIL`: el nombre del perfil donde conectaste tus redes.

**4. Pon tus vídeos en `videos/`** y tus textos en `textos.json`. Repasa **antes**: en Instagram y TikTok lo que sale no se puede editar ni borrar desde aquí.

**5. Programa:**

```
python publicar.py programar
```

Vuelve a revisar y, si está limpio, programa cada fila y te enseña su número: `2026-12-04 18:00 Europe/Madrid  youtube instagram tiktok x   n.º …`. Si lo lanzas otra vez, **no vuelve a mandar** lo que ya tiene número.

**6. Si una subida tarda** y sale `SIN RESPUESTA`, **no la repitas**: puede que haya llegado y se haya ido a segundo plano. Pregunta:

```
python publicar.py estado
```

**7. Compara lo programado con tu calendario**, red por red:

```
python publicar.py lista
```

Acaba con `Cuadra con tu calendario.` o te dice qué falta y qué sobra.

**8. Si algo cambia** (otra hora, otro texto), no lo subas otra vez: cancélalo con su número, cambia el calendario y vuelve a programar.

```
python publicar.py cancelar NÚMERO
python publicar.py programar
```

## Las conexiones caducan

Las redes conectadas no duran para siempre: **Instagram y TikTok, unos 60 días; YouTube, unos seis meses** (X suele aguantar). Cuando caducan, el servicio da un error de sesión caducada y hay que volver a conectarlas en [*User Management*](https://app.upload-post.com/manage-users). Apúntate la fecha.

## Cómo lo compruebas

Después de programar, `python publicar.py lista` y luego mira el calendario del panel del servicio: tiene que salir lo mismo, red por red, a la hora que pusiste **en tu zona horaria**. El primer vídeo, prográmalo solo en una red y míralo salir.

## Los tres fallos

1. **Una subida tarda, Claude cree que ha fallado y la repite.** La subida se había ido a segundo plano y el vídeo sale dos veces. Corrección: preguntar su estado con su número y nunca volver a enviarla (el programa guarda el número **antes** de mandar y avisa a la API para que no la duplique).
2. **Copia el mismo texto en todas las redes, enlace incluido.** Corrección: un texto por red, y en X, sin enlaces.
3. **Programa sin zona horaria y el vídeo sale a otra hora.** Corrección: la zona horaria, siempre escrita (si falta, `revisar` no te deja seguir).

Y dos reglas del servicio: **nada repetido** (el mismo contenido en la misma cuenta y la misma red se rechaza si no han pasado 48 horas: cambia el texto y espera) y **los topes de cada día** (TikTok 15, YouTube 30, Instagram 50 y X 10 en el plan gratis, según su documentación de noviembre de 2026; se miran cuando sale, no cuando lo programas).

---

Esto no es consejo financiero y aquí no se señala a nadie.
