# Curso de Claude 16: conecta Claude a tu servidor para que trabaje él

▶️ Vídeo: (enlace en la descripción del canal) · Hay también un vídeo corto paso a paso: **Curso de Claude 16.2: conecta Claude a tu servidor**.

## Qué aprendes

Cómo trabaja Claude en un servidor sin que tú escribas ni una orden: le hablas, y él trabaja allí.

- **Cómo trabaja**: Claude manda una orden al servidor, el servidor la ejecuta y Claude lee lo que contesta. Así hasta terminar la tarea.
- **La pieza**: un programa pequeño en el servidor que habla MCP (un *servidor MCP*, como el del [capítulo 9](../09-conectores-personalizados/)). El del vídeo solo tiene tres herramientas: ejecutar una orden, leer un archivo y escribir un archivo. Con eso, Claude puede hacer casi todo.
- **Dónde escucha (lo importante)**: solo dentro de la red privada del [capítulo 15](../15-prepara-tu-servidor-y-entra-seguro/). Su protección es que solo se llega desde tus aparatos. Abierto a internet, cualquiera podría mandar órdenes a tu servidor.
- **Cómo se añade (la trampa)**: un conector añadido desde la web se conecta desde los servidores de Anthropic, fuera de tu casa, y no llega a tu red privada. Por eso se añade en la **aplicación de escritorio** de Claude, en su archivo de configuración, como servidor local: lo arranca tu ordenador, que sí está dentro de la red. Guía oficial: [conectar servidores locales](https://modelcontextprotocol.io/docs/develop/connect-local-servers).
- **Que se levante solo**: el programa funciona como un servicio del sistema: arranca al encender y, si se cae, se vuelve a levantar a los pocos segundos (lo enseña, para un bot, el [Curso de Claude 21](../21-bot-24-horas/)).
- **El tiempo de cada orden**: cada orden tiene un límite (en el del vídeo, dos minutos). Lo que tarda más se deja en segundo plano, guardando lo que sale en un archivo, y Claude lo mira después.
- **Cada orden en su cajón**: cada orden corre aparte del programa que la recibe. Si una revienta, no se lleva por delante al conector.

## La frase para Claude

> Para todo lo que tarde más de un minuto, déjalo en marcha en segundo plano, guarda lo que salga en un archivo y avísame cuando acabe.

## Lo que necesitas antes

- **Un servidor preparado y una red privada**: **Curso de Claude 14** y **Curso de Claude 15** → [`14-que-es-un-servidor`](../14-que-es-un-servidor/) y [`15-prepara-tu-servidor-y-entra-seguro`](../15-prepara-tu-servidor-y-entra-seguro/).
- **La aplicación de escritorio de Claude** (Windows o Mac), con tu cuenta: [claude.com/download](https://claude.com/download). Qué es un conector y qué es MCP: **Curso de Claude 5** ([`05-que-son-los-conectores`](../05-que-son-los-conectores/)) y **Curso de Claude 9** ([`09-conectores-personalizados`](../09-conectores-personalizados/)).
- **El programa MCP en tu servidor.** El vídeo no enseña su código. Si quieres uno, pídeselo a Claude con estas condiciones: que escuche **solo** en la dirección de la red privada, con un límite de tiempo por orden y cada orden en un proceso aparte. Guía oficial para hacer servidores MCP: [modelcontextprotocol.io](https://modelcontextprotocol.io).
- **Las normas antes de darle las llaves**: **Curso de Claude 17** → [`17-normas-para-no-reventar-el-servidor`](../17-normas-para-no-reventar-el-servidor/).

## Los tres errores

1. **Abrir el conector a internet** para entrar desde cualquier sitio.
2. **Dejar órdenes largas sin segundo plano**, y que se corten a medias.
3. **Darle las llaves del servidor sin normas.** De eso va el [capítulo 17](../17-normas-para-no-reventar-el-servidor/).

---

Esto no es consejo financiero y aquí no se señala a nadie.
