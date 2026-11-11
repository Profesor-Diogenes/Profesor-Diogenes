# Curso de Claude 9: conecta Claude a tu propio servidor (conectores personalizados)

▶️ Vídeo: (enlace en la descripción del canal)

## Qué aprendes

Un conector personalizado es uno que añades tú, a un servicio que no está en el catálogo (por ejemplo, un programa en tu propio servidor). Ese programa tiene que hablar **MCP**, un idioma común: como un enchufe estándar.

- **Quién puede**: todos los planes. En el gratis, solo uno; en los de pago, los que quieras.
- **Cómo se añade**: *Personalizar* → *Conectores* → *Añadir* → *Añadir conector personalizado*. Le pones nombre y la dirección de tu servidor, y eliges cómo entra (iniciando sesión ahora, cuando haga falta, o sin iniciar sesión). Si usa una clave, va en su apartado, nunca en el chat.
- **Lo que se puede hacer**: desde el chat, que Claude lea archivos, lance programas o revise que tus bots funcionan, mientras el trabajo pesado lo hace el servidor. (Montarlo paso a paso llega en un tema posterior del curso.)
- **El aviso de seguridad**: estos conectores no los ha revisado Anthropic. Un servidor malicioso puede esconder instrucciones para que Claude haga cosas que no has pedido. Solo servidores tuyos o de total confianza.
- **Permisos mínimos**: dale solo lo que necesite, vigila lo que hace al principio, y "permitir siempre" solo con herramientas que no pueden romper nada. Quien mantiene un servidor puede cambiar cómo funciona sin avisar.

## La frase para Claude (en las instrucciones del proyecto)

> Antes de ejecutar nada en mi servidor, dime qué vas a hacer y espera mi visto bueno. Nunca borres nada sin preguntarme.

## Lo que necesitas antes

- **Una cuenta de Claude** (vale la gratis). Cómo se crea y qué plan te sirve: **Curso de Claude 1: qué es Claude y cuál te sirve (desde cero)** → [`curso-de-claude/01-que-es-claude`](../01-que-es-claude/).
- **Un servidor tuyo con un programa que hable MCP**, con su dirección en internet. Qué es un servidor, cómo prepararlo con seguridad y cómo conectarle Claude, en el tema 4 del curso: **Curso de Claude 14: qué es un servidor y por qué lo necesitas con Claude**, **Curso de Claude 15: prepara tu servidor y entra seguro (red privada y cortafuegos)** y **Curso de Claude 16: conecta Claude a tu servidor para que trabaje él** → [`14-que-es-un-servidor`](../14-que-es-un-servidor/), [`15-prepara-tu-servidor-y-entra-seguro`](../15-prepara-tu-servidor-y-entra-seguro/), [`16-conecta-claude-a-tu-servidor`](../16-conecta-claude-a-tu-servidor/), y el short *Lo que protege el conector de mi servidor*. Qué es MCP, en su web oficial: [modelcontextprotocol.io](https://modelcontextprotocol.io).
- **Si tu servidor usa clave**: la creas tú en tu servidor y va en el apartado de la clave al añadir el conector, nunca en el chat.

## Los tres errores

1. **Abrir tu servidor a todo internet sin protección.**
2. **Pegar las claves en el chat.** Las claves van en su sitio, nunca en la conversación.
3. **Conectar el servidor de un desconocido porque promete maravillas.** Si no sabes quién está detrás, no.

---

Esto no es consejo financiero y aquí no se señala a nadie.
