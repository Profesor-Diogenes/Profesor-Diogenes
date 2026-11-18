# Curso de Claude 12: trucos de Claude Code y del servidor para que el plan dure

▶️ Vídeo: (enlace en la descripción del canal) · Hay también un vídeo corto paso a paso: **Curso de Claude 12.2: que tu plan de Claude Code dure**.

## Qué aprendes

Si usas Claude Code, o tienes a Claude trabajando en un servidor, el plan se puede ir en una tarde. Los trucos salen de la documentación oficial de Claude Code sobre costes ([*Manage costs effectively*](https://code.claude.com/docs/en/costs), consultada a principios de noviembre de 2026; puede cambiar).

- **Mira qué gasta**: `/usage` enseña tus barras de uso y en qué se te va (habilidades, conectores, tareas), con recomendaciones. `/context` enseña qué ocupa sitio en la conversación.
- **Limpia entre tareas**: cuando cambias de tema, `/clear` empieza de cero. Lo viejo se paga en cada mensaje; empezar de cero es gratis.
- **Resume si quieres seguir**: `/compact` resume la conversación y sigue desde ahí. Puedes decirle qué guardar ("resume, pero quédate con los cambios del código"). Resumir algo enorme también gasta.
- **Instrucciones cortas**: el `CLAUDE.md` se lee entero en cada sesión. Por debajo de 200 líneas y solo lo esencial; lo de tareas concretas, a habilidades (*skills*), que solo se cargan cuando hacen falta.
- **Que lo pesado no entre**: si hay que buscar un error en un registro de diez mil líneas, que un programa pequeño filtre antes solo las líneas con error. Lo mismo con las pruebas: que solo le lleguen los fallos.
- **Los ayudantes** (subagentes): se comen el texto largo en su propia conversación y te devuelven solo el resumen. También gastan: para tareas simples, un modelo pequeño.
- **El esfuerzo justo**: para lo sencillo, baja el esfuerzo (`/effort`). Para trabajos grandes, primero el plan y lo apruebas. Si va mal, páralo en cuanto lo veas.
- **Lo que gasta sin que lo veas**: tareas programadas que se repiten, ayudantes que siguen vivos, mensajes de otras sesiones. Cada una manda la conversación entera. Revisa qué tienes encendido.

## La frase para Claude (en tus instrucciones)

> Antes de leer archivos enormes, fíltralos y quédate solo con lo que necesitas. Y antes de un trabajo grande, enséñame el plan.

Ponla en tu `CLAUDE.md` para que la tenga siempre presente.

## Lo que necesitas antes

- **Una cuenta de Claude con plan de pago** (Pro o Max): Claude Code no entra en el plan gratis. Qué plan te sirve: **Curso de Claude 1: qué es Claude y cuál te sirve (desde cero)** → [`curso-de-claude/01-que-es-claude`](../01-que-es-claude/). Cómo se paga y dónde ves el uso: **Curso de Claude 10** → [`curso-de-claude/10-por-que-se-acaba-el-plan`](../10-por-que-se-acaba-el-plan/). Precios oficiales: [claude.com/pricing](https://claude.com/pricing).
- **Claude Code instalado y con tu cuenta dentro.** Ningún capítulo lo enseña todavía paso a paso. En corto, con la guía oficial ([code.claude.com/docs/en/setup](https://code.claude.com/docs/en/setup)): instálalo con la orden que da esa página para tu sistema (Windows, Mac o Linux), abre una terminal en la carpeta de tu proyecto, escribe `claude` y, la primera vez, entra con tu cuenta de Claude cuando te lo pida.
- **Un servidor** (opcional; solo si quieres que Claude trabaje allí): lo explica el tema 4 del curso, empezando por **Curso de Claude 14: qué es un servidor y por qué lo necesitas con Claude** → [`curso-de-claude/14-que-es-un-servidor`](../14-que-es-un-servidor/).

## Los errores que más plan funden

1. **Un único chat para todo**, sin `/clear` entre tareas.
2. **Un `CLAUDE.md` kilométrico** que se paga en cada sesión.
3. **Dejar que Claude se trague registros enteros** en vez de filtrarlos antes.

---

Esto no es consejo financiero y aquí no se señala a nadie.
