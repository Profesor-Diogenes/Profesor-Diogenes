# Claude en tu día a día 5: que Claude encuentre todos tus recibos y seguros

▶️ Vídeo: (enlace en la descripción del canal)

## Qué hace

¿Sabes cuántos seguros pagas y cuándo se renuevan? Este programa lee los movimientos que ya bajas del banco (los del [capítulo 2](../02-banco-en-solo-lectura/)) y:

- se queda con los que llevan **tus** palabras: seguro, devolución, anulación y el nombre de tus aseguradoras;
- **tapa los números de cuenta** antes de enseñarte nada (pone `[IBAN]`);
- te lo ordena por fecha, en positivo lo que entra y en negativo lo que sale;
- te **marca aparte cada devolución**, que es la alarma;
- te saca los recibos de quien no reconoces;
- y te dice qué recibos se acaban y cuáles se renuevan (y hacia qué fecha).

Viene con **movimientos de ejemplo inventados** para que lo pruebes sin tocar tu banco.

## La frase para Claude

> Busca en mis movimientos todo lo que pago a aseguradoras, y todas las devoluciones y anulaciones. Tapa los números de cuenta. Ordénalo por fecha, márcame cada devolución y dime qué recibos se acaban y cuáles se renuevan.

## Lo que necesitas antes

- **Python 3.10 o más nuevo** (gratis). Entra en [python.org/downloads](https://www.python.org/downloads/), baja la última versión e instálala. En Windows, **marca la casilla *Add python.exe to PATH*** antes de pulsar *Install*. Para comprobarlo, abre una terminal y escribe `python --version` (en Mac y Linux, `python3 --version`): tiene que salir 3.10 o un número mayor.
- **Una cuenta de Claude** (vale la gratis). Cómo se crea y qué plan te sirve: **Curso de Claude 1: qué es Claude y cuál te sirve (desde cero)** → [`curso-de-claude/01-que-es-claude`](../../curso-de-claude/01-que-es-claude/).
- **Tus movimientos del banco** (para usarlo de verdad): los baja cada mañana **Claude en tu día a día 2: conectar Claude a tu banco en solo lectura** → [`claude-en-tu-dia-a-dia/02-banco-en-solo-lectura`](../02-banco-en-solo-lectura/). También vale el archivo que te descargas a mano desde la web de tu banco, si lo guardas como CSV con las columnas `fecha`, `concepto` e `importe`. Para probar no hace falta: viene un archivo de ejemplo inventado.
- **Las condiciones de tus pólizas** (el PDF o el papel), para cuando quieras saber qué cubren. Este capítulo no necesita ninguna clave.

## Qué hay en la carpeta

| Archivo | Para qué |
|---|---|
| `seguros.py` | Busca, tapa, ordena, marca devoluciones, saca lo que no reconoces y lo que se renueva. |
| `palabras.txt` | **Tu** lista de palabras: seguro, devolución, anulación y tus aseguradoras. |
| `conocidos.txt` | Recibos que sí reconoces y no son seguros (luz, gimnasio…), para que no salgan como raros. |
| `se_acaban.txt` | Los recibos que se acaban solos (un pago y ya). Lo demás se da por renovable. |
| `movimientos_ejemplo.csv` | Movimientos inventados (con un recibo devuelto dos veces, uno anulado, uno repetido y un emisor desconocido, a propósito). |

## Cómo se usa

**1. Instala lo necesario** (una vez), abriendo una terminal en esta carpeta:

```
pip install -r requirements.txt
```

**2. Pruébalo con el ejemplo** (no necesita claves):

```
python seguros.py
```

Si va bien verás la lista por fecha con los números de cuenta tapados (`RECIBO HOGAR ASEG. EJEMPLO A [IBAN]`), `DEVOLUCIONES Y ANULACIONES: 3`, la línea `HOGAR ASEG. EJEMPLO A: 2 veces`, el `RECIBO EMISOR EJEMPLO X [IBAN]` entre los que no reconoces y, al final, `HOGAR … mensual, se renueva: próximo hacia el 2026-05-05` y `VIAJE … se acaba`.

**3. Pon tus palabras.** En `palabras.txt`, el nombre de tus aseguradoras **tal y como sale en el concepto del banco** (míralo en un recibo). Tú sabes con quién tienes póliza. En `conocidos.txt`, los recibos que sí reconoces. En `se_acaban.txt`, los que son de un solo pago.

**4. Copia `.env.ejemplo` a `.env`** y pon en `MOVIMIENTOS` tu archivo (por ejemplo `../02-banco-en-solo-lectura/datos/movimientos.csv`). O pásaselo directamente: `python seguros.py mi_archivo.csv`.

## Qué hacer con lo que sale

- **Una devolución es la alarma.** Un recibo cobrado y devuelto deja el saldo igual, pero no la póliza: si dejas de pagar una prima, la cobertura puede quedar en suspenso. Nada de suponer: **pide por escrito** a la aseguradora que la póliza está al corriente.
- **Un cargo que no reconoces.** Devolver el recibo no cancela nada: vuelve el mes siguiente. **Bloquea a ese emisor en la app de tu banco** y pide por escrito que anulen la orden de cobro. Y antes, pregunta en casa: un cargo raro no siempre es malo.
- **Antes de cada renovación**, compara lo que pagas, lo que cubre y lo que te ofrecen otros.
- **La letra pequeña, antes del parte.** No des por hecho que algo está cubierto: lee las condiciones antes de dar parte, y en la renovación pregunta cuánto cuesta añadir lo que te falte (por ejemplo, daños accidentales).
- **Seguro de salud:** pregunta a tu empresa o a tu gestor si te lo pueden pagar en la nómina, como retribución en especie. Según la ley del IRPF, no tributa hasta 500 € al año por cada persona asegurada, pero **sí cotiza a la Seguridad Social** y depende de que tu empresa lo ofrezca. Antes de nada, pregúntaselo a tu gestor.

## Cómo lo compruebas

Coge un recibo que conozcas bien y búscalo en la lista: tiene que salir una sola vez por cada cobro, con su fecha, y sin el número de cuenta a la vista. Compara las devoluciones con lo que te enseña la app de tu banco.

## Los tres fallos

1. **Claude te enseña los números de cuenta tal cual vienen.** Corrección: que los tape siempre, antes de sacar nada (es lo primero que hace `seguros.py` al leer cada movimiento).
2. **Suma lo cobrado y lo devuelto y te dice que todo está bien.** Corrección: que te marque aparte cada devolución.
3. **Te dice qué cubre tu póliza sin haberla leído.** Corrección: pásale las condiciones y que te cite la cláusula.

---

Esto no es consejo financiero y aquí no se señala a nadie.
