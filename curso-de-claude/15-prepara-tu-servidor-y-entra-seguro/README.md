# Curso de Claude 15: prepara tu servidor y entra seguro (red privada y cortafuegos)

▶️ Vídeo: (enlace en la descripción del canal)

## Qué aprendes

Un servidor abierto a internet recibe intentos de entrada a todas horas. Cómo dejar la puerta cerrada a todo el mundo menos a tus propios aparatos.

- **El sistema**: Ubuntu de soporte largo (en el vídeo, la 24.04 LTS). Gratuito y con actualizaciones de seguridad durante años. Para un servidor, mejor soporte largo que la última novedad.
- **La red privada**: con **Tailscale** (la del vídeo), el servidor, tu ordenador y tu móvil se ven entre ellos como si estuvieran en la misma casa, estés donde estés. Entras sin abrir puertas al mundo.
- **El cortafuegos**: decide quién puede llamar a cada puerta. La puerta para dar órdenes solo acepta a quien viene por la red privada; desde internet, cerrada.
- **La puerta de entrada (SSH)**: sirve para entrar a escribir órdenes en el servidor. No tienes que aprender a usarla, la usa Claude. Pero tienes que saber que existe y quién puede entrar.
- **Compruébalo**: pídele a Claude las reglas del cortafuegos y qué puertas están escuchando. Si algo está abierto a todo el mundo y no sabes por qué, pregunta antes de seguir.
- **Las claves**: nunca en el chat. Van en archivos de secretos dentro del servidor y Claude las usa sin enseñarlas.
- **Las copias**: lo que no tiene copia, no existe. A un disco de casa dentro de la misma red privada; si el servidor muere, lo importante sigue ahí.

## La frase para Claude

> Enséñame qué puertas tiene abiertas mi servidor y desde dónde se puede entrar a cada una. No cambies nada sin preguntarme.

## Lo que necesitas antes

- **Un servidor u ordenador siempre encendido con Ubuntu**: **Curso de Claude 14: qué es un servidor y por qué lo necesitas con Claude** → [`curso-de-claude/14-que-es-un-servidor`](../14-que-es-un-servidor/).
- **Claude trabajando en ese servidor**, para que mire las puertas por ti: **Curso de Claude 16: conecta Claude a tu servidor para que trabaje él** → [`curso-de-claude/16-conecta-claude-a-tu-servidor`](../16-conecta-claude-a-tu-servidor/).
- **Una red privada entre tus aparatos** (Tailscale tiene plan gratis para uso personal). Cómo se instala en cada aparato y se entra con tu cuenta: **Claude en tu día a día 23: el ordenador de casa desde el móvil sin abrir el router** → [`claude-en-tu-dia-a-dia/23-el-ordenador-de-casa-desde-el-movil`](../../claude-en-tu-dia-a-dia/23-el-ordenador-de-casa-desde-el-movil/). Guía oficial: [tailscale.com/docs/how-to/quickstart](https://tailscale.com/docs/how-to/quickstart). No es la única; si usas otra red privada, la idea es la misma.
- **El cortafuegos de Ubuntu** viene incluido (se llama `ufw`). Guía oficial: [documentation.ubuntu.com/server/how-to/security/firewalls](https://documentation.ubuntu.com/server/how-to/security/firewalls/). Que lo toque Claude, pero solo después de enseñarte lo que va a cambiar: si cierras mal la puerta SSH, te quedas fuera.
- **Un disco para las copias**: cómo pasar lo del servidor a un disco de casa sin perder nada lo cuenta **Claude en tu día a día 22: pasar lo viejo de tu servidor al disco de casa sin perder nada** → [`claude-en-tu-dia-a-dia/22-del-servidor-al-disco-de-casa`](../../claude-en-tu-dia-a-dia/22-del-servidor-al-disco-de-casa/).

## Los tres errores

1. **Dejar la puerta de entrada abierta a todo internet.**
2. **Pegar claves en el chat** para ir más rápido.
3. **No tener ninguna copia** hasta el día que la necesitas.

---

Esto no es consejo financiero y aquí no se señala a nadie.
