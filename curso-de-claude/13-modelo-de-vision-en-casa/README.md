# Curso de Claude 13: tu modelo de visión mira la foto y ahorras plan (prueba medida)

▶️ Vídeo: (enlace en la descripción del canal)

## Qué aprendes

Que mirar una imagen le sale caro a Claude, y que un modelo de visión gratuito en tu propio ordenador puede mirarla por él y pasarle solo el texto.

- **Cómo cobra Claude una imagen** (documentación oficial, [*Vision*](https://platform.claude.com/docs/en/build-with-claude/vision)): la corta en cuadraditos de 28 × 28 puntos y cada cuadradito cuenta como un trozo de texto: *ancho ÷ 28 × alto ÷ 28*. Más grande, más trozos; si es muy grande, la reduce, con un tope.
- **Lo que costó una captura** en nuestra prueba (1 de noviembre de 2026, medido con el contador oficial de Anthropic): una captura de pantalla grande y llena de texto, **4.735 trozos**.
- **Lo que costó el texto del modelo de casa**: le pedimos "describe todo lo que pone, ordenado y breve". Tardó menos de diez segundos y su texto, pasado por el mismo contador, fueron **558 trozos**: unas ocho veces y media menos. Con una página casi toda de texto, el ahorro bajó a unas cinco veces y media. Con capturas pequeñas, el ahorro también baja.
- **Cómo se monta**: Claude no mira la foto; le pide a tu modelo que la mire y trabaja solo con el texto que le devuelve. Con Claude conectado a tu servidor, basta una frase (abajo).
- **Cuándo merece la pena**: capturas llenas de texto, montones de fotos, documentos escaneados, todo lo que se repite cada día.
- **Cuándo no**: si lo importante es un detalle fino (un gráfico difícil, una cara). El modelo de casa es más simple y se puede equivocar. Para lo importante, que mire Claude.

## La frase para Claude

> No mires tú esta imagen. Pásasela a mi modelo de visión del servidor, que me la describa, y trabaja solo con ese texto.

## Lo que necesitas antes

- **Claude conectado a tu servidor u ordenador**, para que pueda llamar a tu modelo: **Curso de Claude 16: conecta Claude a tu servidor para que trabaje él** → [`curso-de-claude/16-conecta-claude-a-tu-servidor`](../16-conecta-claude-a-tu-servidor/). Antes, **Curso de Claude 14** y **15** ([`14-que-es-un-servidor`](../14-que-es-un-servidor/), [`15-prepara-tu-servidor-y-entra-seguro`](../15-prepara-tu-servidor-y-entra-seguro/)).
- **Un modelo de visión instalado en tu ordenador** (gratis; va mucho mejor con una tarjeta gráfica). El canal lo enseñará en el tema de la inteligencia artificial en casa; mientras tanto, un camino oficial y sencillo: si usas **Ollama**, bájalo de [ollama.com/download](https://ollama.com/download), instálalo y, en una terminal, prueba con un modelo que vea imágenes, como el del ejemplo de su guía de visión ([docs.ollama.com/capabilities/vision](https://docs.ollama.com/capabilities/vision)): `ollama run <modelo> ./captura.png "describe todo lo que pone, ordenado y breve"`. La primera vez se baja el modelo (varios gigas). No es el único programa que lo hace; si usas otro, la frase vale igual.
- **Una cuenta de Claude**: **Curso de Claude 1** → [`curso-de-claude/01-que-es-claude`](../01-que-es-claude/).

## Los tres errores

1. **Fiarte del resumen sin mirarlo nunca.** Al principio, compara de vez en cuando lo que dice con la imagen.
2. **Usarlo para todo**, aunque sea una foto suelta. El ahorro está en lo que se repite.
3. **Tener la tarjeta gráfica ocupada con otra cosa.** El modelo de casa necesita su turno (ver [Curso de Claude 17](../17-normas-para-no-reventar-el-servidor/)).

---

Esto no es consejo financiero y aquí no se señala a nadie.
