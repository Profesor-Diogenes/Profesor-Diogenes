# Claude en tu día a día 6: nóminas, facturas y compras cruzadas con tu banco

▶️ Vídeo: (enlace en la descripción del canal)

## Qué hace

Lee tus nóminas en PDF y solo las apunta si **cuadran al céntimo**. Compara un mes con otro y busca en el banco si te llegó el mismo líquido. Empareja el historial de una tienda en línea con los cargos del banco **por importe y con margen de días** (la tienda cobra cuando envía, no cuando pides). Y suma la luz por mes, con dos recibos o dos compañías, y te pregunta por cada mes vacío.

Lo que no cuadra no es un error: es una **pregunta** para ti.

Viene con **nóminas, movimientos y pedidos de ejemplo inventados** para que lo pruebes sin tocar nada tuyo.

## La frase para Claude

> Lee mis nóminas en PDF y apúntalas solo si cuadran al céntimo. Cruza el historial de la tienda con el banco, por importe y con margen de días. Suma la luz por mes. Y pregúntame todo lo que no cuadre.

## Lo que necesitas antes

- **Python 3.10 o más nuevo** (gratis). Entra en [python.org/downloads](https://www.python.org/downloads/), baja la última versión e instálala. En Windows, **marca la casilla *Add python.exe to PATH*** antes de pulsar *Install*. Para comprobarlo, abre una terminal y escribe `python --version` (en Mac y Linux, `python3 --version`): tiene que salir 3.10 o un número mayor.
- **Una cuenta de Claude** (vale la gratis). Cómo se crea y qué plan te sirve: **Curso de Claude 1: qué es Claude y cuál te sirve (desde cero)** → [`curso-de-claude/01-que-es-claude`](../../curso-de-claude/01-que-es-claude/). Cómo pasarle un PDF a Claude sin que se invente nada: **Curso de Claude 4: archivos, fotos y capturas (y que no se invente nada)** → [`curso-de-claude/04-archivos-fotos-y-capturas`](../../curso-de-claude/04-archivos-fotos-y-capturas/).
- **Tus nóminas en PDF**, tal cual te llegan (de tu empresa o de su portal del empleado). Para probar no hacen falta: `crear_nominas_ejemplo.py` te crea dos inventadas.
- **Tus movimientos del banco** (opcional): los baja **Claude en tu día a día 2: conectar Claude a tu banco en solo lectura** → [`claude-en-tu-dia-a-dia/02-banco-en-solo-lectura`](../02-banco-en-solo-lectura/). Es el mismo archivo que usa el [capítulo 3](../03-movimientos-cada-manana/). Para probar, viene `movimientos_ejemplo.csv`.
- **El historial de tu tienda en línea** (opcional). Las tiendas grandes te dejan descargar tus pedidos, reembolsos y devoluciones: suele estar en *Mi cuenta* → *Pedidos*, o en la parte de *Privacidad* → *Descargar mis datos*. Cada tienda lo pone en un sitio; si no lo encuentras, busca en su ayuda "descargar historial de pedidos". Luego pídele a Claude que lo pase al formato de `pedidos_tienda_ejemplo.csv` (`pedido;fecha;tipo;importe`).

Nada de esto lleva claves ni se paga: todo se queda en tu ordenador.

## Qué hay en la carpeta

| Archivo | Para qué |
|---|---|
| `leer_nomina.py` | Lee las nóminas en PDF y las apunta en `apuntes_nominas.csv` solo si cuadran al céntimo. |
| `comparar.py` | Qué ha cambiado de un mes a otro, y si el líquido está en el banco. |
| `cruzar.py` | Empareja la tienda con el banco por importe y con margen de días. Lo que no casa, te lo pregunta. |
| `luz.py` | Suma luz y gas por mes (todas las compañías) y pregunta por cada hueco. |
| `comun.py` | Lo que comparten todos: leer el banco y los ajustes. |
| `crear_nominas_ejemplo.py` | Crea en `nominas/` dos nóminas en PDF **inventadas** (septiembre y octubre) para probar. |
| `nominas/` | Aquí van tus nóminas en PDF. |
| `movimientos_ejemplo.csv` | Movimientos inventados (mismo formato que los capítulos 2 y 3). |
| `pedidos_tienda_ejemplo.csv` | Historial de una tienda, inventado, con un reembolso y un pedido que no está en el banco. |
| `.env.ejemplo` | Ajustes: qué archivos leer, cómo sale la tienda y la luz en el banco, días de margen. |

## Cómo se usa

**1. Instala lo necesario** (una vez), abriendo una terminal en esta carpeta:

```
pip install -r requirements.txt
```

**2. Las nóminas** (pasos 1 y 2 del vídeo). Para probar, crea primero las dos de ejemplo y luego léelas:

```
python crear_nominas_ejemplo.py
python leer_nomina.py
```

Si va bien, por cada nómina verás tres comprobaciones con `OK` (conceptos = bruto, descuentos = total descontado, bruto − descuentos = líquido) y `-> cuadra al céntimo: APUNTADA`. Si una no cuadra, sale `NO CUADRA` y **no se apunta**: ha leído mal un número. Si lo vuelves a pasar, no repite los meses que ya estaban.

**3. Comparar un mes con otro** (paso 3):

```
python comparar.py 2026-09 2026-10
```

Con los de ejemplo: `NUEVO Atrasos convenio 145,50`, `CAMBIA Plus nocturnidad 120,00 -> 80,00`, y el líquido de cada mes encontrado en el banco con `OK`.

**4. La tienda contra el banco** (pasos 4, 5 y 6). Primero sin margen, para ver la trampa de las fechas:

```
python cruzar.py 0
```

Sale `Emparejados: 1 de 7`: casi nada cuadra porque la tienda cobra días después. Ahora con el margen (5 días si no cambias nada):

```
python cruzar.py
```

Sale `Emparejados: 6 de 7` y una `PREGUNTA` por el pedido P-105, que no está en el banco: ¿otra tarjeta, saldo regalo, otra persona?

**5. La luz** (paso 7):

```
python luz.py
```

Verás septiembre con dos recibos, octubre con la compañía vieja y la nueva sumadas, y una `PREGUNTA` en julio, que no tiene recibo.

**6. Con tus datos.** Borra las de ejemplo de `nominas/` y pon las tuyas, copia `.env.ejemplo` a `.env` y cambia lo que haga falta: la ruta de tus movimientos (por ejemplo `../02-banco-en-solo-lectura/datos/movimientos.csv`), tu historial de la tienda y cómo aparecen la tienda y la luz en el concepto del banco.

**Tu nómina tendrá otro formato.** `leer_nomina.py` entiende la de ejemplo. Pásale a Claude una de las tuyas (tapa antes tu nombre, DNI y cuenta) junto con `leer_nomina.py` y la frase, y que lo adapte. La regla no cambia: si no cuadra al céntimo, no se apunta.

**Placas con excedentes.** Si tienes placas, pídele a Claude que lea también el PDF de la factura de la luz y te avise si no aparece el descuento por excedentes. Con el banco solo no se ve.

## Cómo lo compruebas

Coge una nómina que conozcas y suma tú, con la calculadora, el bruto y los descuentos: tiene que darte lo mismo que dice `leer_nomina.py`. Luego busca un pedido que recuerdes con `cruzar.py` y mira en la app del banco que el cargo es ese y no otro del mismo importe.

## Los tres fallos

1. **Claude lee mal un número del PDF y lo apunta tan tranquilo.** Corrección: que cuadre al céntimo antes de apuntar (es lo que hace `leer_nomina.py`).
2. **Empareja por fecha y da por perdidas las compras que no casan.** Corrección: margen de días y por importe (`cruzar.py`).
3. **Un mes sin movimientos de algo lo da por mes sin gasto.** Corrección: que te pregunte por cada hueco (`luz.py`).

Y uno más: **lo que no cuadra es una pregunta, no una conclusión**. Si los pedidos suman más que los cargos, parte puede ser el retraso del envío, pero no todo: que Claude te pregunte, no que decida.

---

Esto no es consejo financiero y aquí no se señala a nadie.
