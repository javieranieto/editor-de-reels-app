# Biblioteca de motion graphics

Piezas de animación **con el estilo de Javier** (VENTANA: fondo azul, él sigue hablando en el
hueco de abajo y la gráfica vive arriba), listas para reutilizar en cualquier reel. Cada una
recibe el texto y las palabras en que debe pasar cada cosa desde un **spec JSON**, no desde
código.

**La idea, pedida por Javier el 20-oct-2026:** *«ir guardando cosas»*. Lo que se construye para
un video se queda aquí para el siguiente. Y se **ofrece**: al revisar un reel, Claude propone la
pieza que encaje (skill `revisar-reel`, paso 4b). Tener una pieza no obliga a usarla.

```bash
python tools/motion.py                       # el catálogo y el estado de cada pieza
python tools/motion.py --muestras            # una hoja por pieza -> proyectos/_motion_muestras/
python tools/motion.py <spec.json> --palabras <plan.json del clip>   # .mov + hoja + json
```

## El catálogo

| Pieza | Estado | Para qué |
|---|---|---|
| `lista` | aprobada 22-sep | contar cosas: «uno… dos… tres…» |
| `comparativa` | aprobada 22-sep | dos casos parecidos que no son lo mismo (✓ / ✗) |
| `titular` | aprobada 22-sep | una pregunta o tesis con UNA palabra que golpea |
| `burbujas` | aprobada 22-sep | una cantidad que baja y lo que queda vale más |
| `controles` | aprobada 22-sep | lo que todos le mueven a una herramienta |
| `sello` | **nueva** | el veredicto que cae en la palabra clave |
| `contador` | **nueva** | un número que sube mientras lo dices |
| `etapas` | **nueva** | un proceso en pasos, para no perderse |

**Aprobada** = salió de un video que él aprobó. **Nueva** = hecha con su estilo pero que todavía
no ha visto. Al proponer, se dice cuál es cuál. Una nueva sube a aprobada **solo** cuando la ve en
un video real y dice que sí: se cambia su `estado` en `catalogo.py` con la fecha y lo que dijo.

Las tres nuevas salieron del glosario de motion graphics de Carlos Martell (ver `IDEAS.md`,
20-oct). Del glosario se tomó el **nombre** de la idea, no el estilo: los colores, letras y
movimientos son los de lo aprobado.

## Un spec

```json
{"pieza": "comparativa", "nombre": "v_alcance_mensaje", "etiqueta": "Dos problemas distintos",
 "anclas": {"hay": "Y hay un problema", "din": {"en": "dinero", "despues_de": "@hay"}},
 "inicio": {"en": "@hay", "mas": -0.15},
 "filas": [...], "fin": {"en": "@din", "mas": 1.5}}
```

- **Un ancla** es una palabra del clip (`"Uno"`), un dict `{"en", "despues_de", "mas"}`, un nombre
  ya resuelto (`"@hay"`) o segundos del clip. Las `anclas` con nombre se resuelven en orden.
- 🔴 **Siempre `despues_de` cuando la palabra se repite.** «Hay TRES cosas… uno, dos, TRES» agarra
  el primero. `lista` y `etapas` **abortan** si un elemento entra antes que el anterior; las demás
  no pueden saberlo, así que **se abre la hoja**.
- `claves` (opcional) dice qué cuadros salen en la hoja; si no, se eligen solos.
- Los campos de cada pieza están en el docstring de su función en `piezas.py`.

**Muestras:** `python tools/motion.py --muestras` arma una hoja de cada pieza con palabras de ejemplo.

## Cómo se comprobó que no cambió nada

Los 5 specs de ejemplo, corridos con esta biblioteca, dan **las mismas hojas pixel por pixel** y
**los mismos cuadros a resolución completa** que los `.mov` aprobados el 22-sep (5 cuadros por
clip, diferencia máxima 0). Y la comparación se probó en el otro sentido: cambiar una palabra de
un spec la hace fallar. Los scripts originales siguen en `proyectos/yt jnieto 0921 video1/`,
que **no está en git**: esta biblioteca es la copia que sí viaja.

## Para meterlo al proyecto de CapCut

`motion.encoger_en_ventana(segmentos, meta, cara_x)` parte los cortes en `t0`/`t1` y reduce el
video al hueco durante la animación (portado de `armar_ventana.py`), y
`motion.quitar_bajo_la_ventana(broll, frases, meta)` saca lo que quedaría encima. El `.mov` va
como un b-roll más con `meta["archivo"]`, `meta["ini"]`, `meta["fin"]`.

⏳ **Todavía no lo hace `reel.py` solo:** hoy se arma con un script como `armar_ventana.py`. El
paso siguiente es que el `plan.json` acepte `"motion": [spec, ...]` y `reel.py --desde-plan` lo
renderice y lo inserte.

## Agregar una pieza

1. Su función en `piezas.py`: `(spec, w, marca) -> (cuadro, t0, t1, claves, eventos)`, dibujando
   sobre `Ventana` (que mide cada texto y aborta si se sale de la franja).
2. Los colores **siempre** de `marca` (`m.ACENTO`, `m.TEXTO`…), nunca escritos a mano.
3. Su entrada en `catalogo.py` con `estado: "nueva"` y una muestra.
4. `python tools/motion.py --muestras <pieza>` y **abrir la hoja**. Que no dé error no dice que se
   vea bien.
5. `python tools/pruebas.py` construye la muestra de todas.
