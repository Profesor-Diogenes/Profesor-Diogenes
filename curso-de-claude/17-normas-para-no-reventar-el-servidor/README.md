# Curso de Claude 17: las normas para que Claude no te reviente el servidor

▶️ Vídeo: (enlace en la descripción del canal)

## Qué aprendes

Las normas que pusimos después de que el servidor se colgara tres días seguidos porque un par de programas se comían toda la memoria.

- **Un tope para cada uno**: cada servicio con su tope de memoria. Si uno se pasa, cae ese y no el servidor entero (en systemd, `MemoryMax=`; documentación oficial: [systemd.resource-control](https://www.freedesktop.org/software/systemd/man/latest/systemd.resource-control.html)).
- **El colchón**: memoria de reserva en el disco (*swap*). Más lenta, pero da margen en los picos.
- **El vigilante**: si la memoria se acaba, para al que más gasta antes de que se congele todo. No es perfecto, pero lo normal pasa a ser que caiga un programa y no el servidor.
- **La gráfica tiene turno**: la comparten varios trabajos. Un candado: el que la coge la suelta al terminar; si está ocupada, se espera. Y la inteligencia artificial nunca se pasa al procesador, porque se come el servidor.
- **Parar con nombre y apellido**: se para un programa por su **número de proceso**, no por su nombre. Por nombre puedes tumbar sin querer otro que se llama parecido.
- **Copia antes de tocar**: antes de cambiar un archivo, una copia. Si sale mal, se vuelve atrás en un segundo. Y nada se borra sin preguntar.
- **Apuntarlo todo**: cada cambio, en un cuaderno del proyecto: qué se cambió, por qué y cómo se deshace. Así Claude no empieza de cero ni repite errores.

## La frase para Claude (en tus instrucciones)

> Antes de tocar un archivo, haz una copia. Para parar algo, usa su número de proceso, nunca el nombre. Y si la gráfica está ocupada, espera tu turno.

Ponla en las instrucciones que Claude lee siempre al empezar (en Claude Code, el `CLAUDE.md`; ver [Curso de Claude 12](../12-claude-code-y-servidor-que-el-plan-dure/)).

## Lo que necesitas antes

- **Claude trabajando en tu servidor**: **Curso de Claude 16: conecta Claude a tu servidor para que trabaje él** → [`curso-de-claude/16-conecta-claude-a-tu-servidor`](../16-conecta-claude-a-tu-servidor/).
- **Tus programas como servicios** (ahí es donde se pone el tope de memoria): **Curso de Claude 21: que tu bot funcione 24 horas y se levante solo** → [`curso-de-claude/21-bot-24-horas`](../21-bot-24-horas/). Para programas en general, **Claude en tu día a día 24: programas que arrancan solos y no congelan tu servidor** → [`claude-en-tu-dia-a-dia/24-programas-que-arrancan-solos`](../../claude-en-tu-dia-a-dia/24-programas-que-arrancan-solos/).

## Los tres errores

1. **Servicios sin tope de memoria.**
2. **Parar programas por el nombre.**
3. **Tocar sin copia y sin apuntarlo.**

---

Esto no es consejo financiero y aquí no se señala a nadie.
