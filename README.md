# Profesor Diógenes — el código de los vídeos

Diógenes es un viejo filósofo que vive en un barril y explica las cosas sin adornos. En el canal enseña a usar **Claude**, la inteligencia artificial de Anthropic, para montarte tus propias herramientas **sin saber programar**.

📺 YouTube: [youtube.com/@profesordiogenes](https://www.youtube.com/@profesordiogenes) · 𝕏: [x.com/Profe_Diogenes](https://x.com/Profe_Diogenes)

Aquí tienes, capítulo a capítulo, las frases exactas para pedírselo a Claude y, cuando el capítulo construye algo, el código listo para usarlo **en tu propio ordenador** (Windows, Mac o Linux, con Python 3.10 o más nuevo).

## Las dos series

- **Curso de Claude** (los miércoles): desde cero, paso a paso.
- **Claude en tu día a día** (los viernes): cosas concretas que te ahorran tiempo.

## Índice

### Curso de Claude

| Nº | Capítulo | Código |
|----|----------|--------|
| 1 | [Qué es Claude y cuál te sirve](curso-de-claude/01-que-es-claude/) | — |
| 2 | [Proyectos, manuales y memoria](curso-de-claude/02-proyectos-manuales-y-memoria/) | — |
| 3 | [Cómo pedirle las cosas para que acierte a la primera](curso-de-claude/03-como-pedirle-las-cosas/) | — |
| 4 | [Archivos, fotos y capturas](curso-de-claude/04-archivos-fotos-y-capturas/) | — |
| 5 | [Qué son los conectores](curso-de-claude/05-que-son-los-conectores/) | — |
| 6 | [Conecta tu Gmail](curso-de-claude/06-conecta-tu-gmail/) | — |
| 7 | [Tu calendario y tu Google Drive](curso-de-claude/07-calendario-y-google-drive/) | — |
| 8 | [Cualquier aplicación del catálogo](curso-de-claude/08-catalogo-de-conectores/) | — |
| 9 | [Conectores personalizados](curso-de-claude/09-conectores-personalizados/) | — |

### Claude en tu día a día

| Nº | Capítulo | Código |
|----|----------|--------|

Se irán añadiendo capítulos.

## Cómo usar el código (para no programadores)

1. Arriba, en el botón verde **Code**, pulsa **Download ZIP** y descomprímelo. O baja solo la carpeta del capítulo.
2. Instala Python (3.10 o más nuevo) desde la web oficial python.org.
3. Abre una terminal dentro de la carpeta del capítulo y sigue su `README.md`. Empieza por su apartado **Lo que necesitas antes**: ahí está todo lo que hace falta (cuentas, claves, programas) y en qué capítulo se enseña a sacarlo.
4. Tus claves van en un archivo `.env` que creas tú copiando `.env.ejemplo`. **Ese archivo no se comparte nunca.**

## Usa tu plan de Claude en tus programas

Algunos capítulos (por ejemplo el [25](curso-de-claude/25-la-ultima-hora-de-bitcoin/)) llevan programas que le preguntan a Claude. Tienes dos maneras:

- **A) Clave de API de la Consola** ([platform.claude.com](https://platform.claude.com/settings/keys)): se paga por uso, con saldo que recargas tú. Cómo se paga y dónde se ve el gasto: [ayuda oficial](https://support.claude.com/en/articles/8977456-how-do-i-pay-for-my-claude-api-usage).
- **B) Tu plan mensual (Pro o Max)**, sin saldo aparte: gasta de los límites de tu plan ([ayuda oficial](https://support.claude.com/en/articles/15036540)).
  1. Instala Claude Code ([guía oficial](https://code.claude.com/docs/en/setup)).
  2. En una terminal, escribe `claude setup-token`. Se abre el navegador, aceptas y te da un token que dura un año. No se guarda solo: cópialo ([documentación](https://code.claude.com/docs/en/authentication#generate-a-long-lived-token)).
  3. Guárdalo en el `.env` del capítulo como `CLAUDE_CODE_OAUTH_TOKEN`. **No lo compartas nunca.**
  4. El programa llama a `claude -p "tu pregunta"` ([documentación](https://code.claude.com/docs/en/headless)).

  Ojo: si tienes puesta una `ANTHROPIC_API_KEY` en el ordenador, Claude Code la usa antes que el plan.

Desde el 7 de octubre de 2026, los planes **Max, Ultra y Team** (no Pro) traen **créditos de API cada mes** si enlazas una organización de la Consola desde *Settings → Billing* en claude.ai. Se gastan con una clave de API de esa organización, no se acumulan de un mes a otro y se usan antes que el saldo comprado ([ayuda oficial](https://support.claude.com/en/articles/17154008)).

## Aviso

- Nunca pegues contraseñas, claves ni palabras de recuperación en ningún chat, tampoco en el de Claude.
- Lo que haga Claude, compruébalo. Se equivoca, y cuando se equivoca lo dice muy seguro.
- Nadie paga por estos vídeos ni por este repositorio.
- Los capítulos de cripto y de Polymarket van **todo en papel, sin dinero real**: solo leen datos públicos y no ponen órdenes.
- **Esto no es consejo financiero y aquí no se señala a nadie.** No se recomienda ninguna moneda, acción, plataforma ni momento para comprar o vender.

## Licencia

MIT: úsalo, cámbialo y compártelo como quieras. Ver [LICENSE](LICENSE).
