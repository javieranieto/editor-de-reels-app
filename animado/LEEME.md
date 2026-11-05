# Videos animados dibujados a mano

Un video que **no se graba ni se edita: se dibuja con código**. Cada cuadro lo pinta
Chrome sobre un canvas, con trazos que tiemblan a 12 fps como en la animación a mano,
y ffmpeg lo junta en un MP4 con música y efectos.

Sirve para lo que un video grabado no puede contar bien: **lanzamientos, explicaciones,
cifras, comparativas, un personaje de marca**. Y con `--alfa` sale con fondo
transparente para ponerlo **encima** de un reel o un video largo en CapCut, como un
motion graphic: una tarjeta que se dibuja sola, una cifra que se encierra en un círculo.

## Requisitos

`pip install playwright` y **Chrome** instalado (si no lo hay, el render usa el Chromium de
Playwright: `python -m playwright install chromium`). ffmpeg/ffprobe para el MP4 y el
`.mov`; Pillow para la hoja de capturas. `render.py` dice cuál falta.

## Comandos

Desde la raíz del repo:

```bash
python animado/render.py <video> --fotos 1 5 9.5   # capturas + hoja.png para revisar
python animado/render.py <video>                   # MP4 final con audio
python animado/render.py <video> --alfa            # .mov transparente para CapCut
python animado/render.py <video> --ver             # vista previa en vivo (&t=12 = desde el 12)

python animado/render.py ejemplo-dato --fotos 0.3 1.2 2.8 --alfa   # el ejemplo más chico
python animado/render.py <video> --param narrado=1 --audio audio_narrado.json   # versión con voz

# sonido y voz
python tools/pueblo_blips.py animado/videos/ejemplo-pueblo    # sonidos de letra, golpes, game over
python tools/pueblo_musica.py animado/videos/ejemplo-pueblo   # música de 8 bits propia (0 créditos)
python tools/chiptune.py exploracion 30 salida.wav            # un tema suelto (exploracion | batalla)
python tools/narrar.py animado/videos/ejemplo-noticiero       # narración de corrido + tiempos por palabra
python tools/armar_voz.py "<carpeta con voz.mp3 y edl.json>"  # tu voz grabada, con solo las tomas buenas
```

`--param k=v` pasa valores que el video lee de la URL; `--audio` usa otro archivo de audio
del video. Los `.wav` de `ejemplo-pueblo/assets/` se generan con los dos primeros comandos
de sonido (no van en git: se rehacen iguales).

`<video>` es una carpeta de `animado/videos/`. La salida va a `proyectos/animado/<video>/`
(fuera de git); `--salida` la manda a otro lado (con `--fotos`, es la carpeta de capturas).
En la hoja, **el rosa es transparente**.

## Cómo está armado

| Archivo | Qué es |
| --- | --- |
| `motor.js` | Lo común: trazos a mano (`line`, `poly`, `rect`, `blob`, `hatch`, `arcHand`, `arrow`, `swoosh`), texto con revelado (`txt`), fondos de papel, cámara con zoom y sacudida (`cam`, `punch`, `shakeAt`), personajes de pixeles (`sprite`), utilería (monedas, bichos, trofeo, maletín, cursor, líneas de código) y el cuadro `frame(t)` |
| `videos/<nombre>/escenas.js` | Lo de ESE video: su paleta (`Object.assign(C, {...})`), `configurar({...})` (lienzo, salida, duración, fuentes, fondos) y sus escenas con `escena(inicio, fin, fn)` |
| `videos/<nombre>/audio.json` | Música, efectos con su segundo exacto y el LUFS final. Si no existe, el video sale mudo |
| `videos/<nombre>/assets/` | Logos y archivos propios del video (se cargan con `imagen()`) |
| `fuentes/` | Tipografías libres (OFL, ver su `LEEME.md`) |
| `render.py` | Captura cada cuadro con Playwright y codifica con ffmpeg |

Un video nuevo = una carpeta nueva con su `escenas.js`. El motor no se toca.

- `videos/ejemplo-dato/` — el mínimo: un dato de 3 s, vertical, con fondo transparente.
- `videos/ejemplo-alcaraz/` — el que se copia para un video completo: dos escenas de 16:9
  con fondos claro y oscuro, cámara, un personaje de pixeles y un pie fijo. Es del negocio
  demo ficticio (Servicios Alcaraz).

Las rutas de `fuentes` y de `imagen()` son relativas a `animado/`; las de `audio.json`,
relativas a la raíz del repo. Una familia que el video usa y no declaró (`header()` usa `Pix`) no
da error: el navegador pone otra letra. Se ve en la hoja.

```json
{
  "musica": {"archivo": "recursos/sfx_usuario/mi_pista.mp3", "desde": 0, "volumen": 0.55, "fade_out": 1.5},
  "efectos": [
    {"archivo": "recursos/sfx/riser.wav", "en": 0, "recorte": 1.8},
    {"archivo": "recursos/sfx/whoosh.wav", "en": 2.87},
    {"archivo": "recursos/sfx/pop.wav", "en": 4.2}
  ],
  "volumen_efectos": 0.6,
  "lufs": -14
}
```

## Seis ejemplos que ya funcionan

Antes de escribir uno nuevo, se copia el ejemplo más parecido. Todos usan el negocio demo
(Servicios Alcaraz) y se pueden renderizar tal cual.

| Ejemplo | Qué es | Para qué sirve |
| --- | --- | --- |
| `ejemplo-dato` | Un dato de 3 s con fondo transparente (`--alfa`) | Motion graphic encima de un reel o video largo en CapCut |
| `ejemplo-alcaraz` | Explicación dibujada a mano: papel, cámara, personaje de pixeles | Lanzamientos, explicaciones, cifras |
| `ejemplo-pueblo` | **El pueblo de negocios**: un RPG de 16 bits (25 s, vertical, sin voz) | Serie de historias de mala (o buena) atención, para una marca personal o creativa |
| `ejemplo-noticiero` | **Noticiero del negocio**: estudio, EN VIVO, cintillo, los datos, la recomendación (20 s) | Marca de empresa con público de dueños: referencia que todos reconocen, letra grande |
| `ejemplo-loteria` | **La lotería de los negocios**: se canta una carta con el error del negocio, su verso y «¡LOTERÍA!» de la competencia (20 s) | Lo mismo, con referencia mexicana |
| `ejemplo-telenovela` | **La telenovela del negocio**: lo dejan en visto, «¡NOOO!» y «en el próximo capítulo» (20 s) | Lo mismo; pide serie |

El noticiero, la lotería y la telenovela comparten `marcas/marca_ejemplo.js` y son molde para
otros formatos de «referencia que todos reconocen». Se usa el FORMATO con dibujos propios:
las cartas tradicionales, los personajes de videojuegos y la música de las consolas tienen
dueño. Se homenajea la mecánica y los clichés del género, nunca personajes, nombres, logos
ni música reales.

## Lo de una marca vive en `marcas/`, no en cada video

`marcas/<marca>.js` trae la paleta, las letras, la firma, personajes y utilería; el video lo
pide con `configurar({ ..., usa: ['marcas/<marca>.js'] })` y queda solo su historia.

- `marcas/pueblo.js`: el mundo del RPG. Paleta, personajes de 12x16 (espalda, frente, lado,
  con paso), el empleado, el taller y la cajita de diálogo con el texto letra por letra. Se
  dibuja a 96x171 y se agranda sin suavizar. El protagonista lleva el color de tu marca
  (`PCOL.SP`) y la pestaña de la cajita dice tu marca (`marca_caja` en el `guion.json`).
- `marcas/marca_ejemplo.js`: una marca de empresa plana y limpia. Fondo, cajas, texto
  (`at`), teléfono con chat (`telefonoMarca`, con palomitas de visto), bustos con cara
  (feliz/triste/sorpresa/serio) y firma. **Para la tuya se copia este archivo** y se cambian
  los colores (del CSS de su sitio en vivo), el nombre y, si hay, el archivo real del logo.

🔴 **La paleta por defecto del motor es neutra; un video de una marca trae la suya.** Si no,
todos los videos salen con los mismos colores y no se reconocen. Cada fondo puede declarar
su `vineta` (un color, o `null` para quitarla).

## El pueblo de negocios (RPG de 16 bits)

Un episodio = `videos/<ep>/guion.json` (diálogos con su `t0`/`t1`, menú, batalla, game over,
continuar, consejo, sonidos) + su `escenas.js`. Lo que hizo que funcionara:

- **Arranca en la acción**, con la marca en una banda arriba. Una pantalla de inicio de 1.5 s
  se quitó: en ese segundo deciden si se quedan.
- **Cámara por llaves** (`CAM`: segundo, centro, zoom) que se acerca a lo que importa (la fila,
  el teléfono, el reloj, la cara) y **temblor** en los golpes.
- **La batalla contra la barra de PACIENCIA** del cliente: el mal servicio es el enemigo que
  ataca. Después, GAME OVER → ¿CONTINUAR? ▶ SÍ → el consejo.
- **Sin voz: los sonidos de letra hacen de voz.** `python tools/pueblo_blips.py <carpeta>` lee
  el guion y escribe `assets/blips.wav` (un tono por personaje, «!», clic de menú, melodía de
  game over). `python tools/pueblo_musica.py <carpeta>` arma la música: exploración → batalla
  → silencio en el game over. Las dos son **originales, compuestas por código**
  (`tools/chiptune.py`), sin derechos de nadie y sin gastar créditos.
- Texto a ~34 letras por segundo (`vel`). La letra Silkscreen trae acentos, ñ, ¿ y ¡.

## Narración de corrido: la voz manda, el video se acomoda

Generar la voz frase por frase y pegar cada una en su escena **suena cortado**: cada frase
empieza en frío y cierra con tono de punto final. `tools/narrar.py <carpeta>` manda el texto
ENTERO en una llamada a ElevenLabs, toma el segundo de cada palabra y, con las `anclas` del
`guion.json` (palabra, ocurrencia, ajuste), calcula cuándo empieza cada escena
(`assets/tiempos.json`). El video los lee con `--param narrado=1` y dura lo que dura la voz.
Modelo: `ejemplo-noticiero` (pon el id de una voz tuya en su `guion.json`).

- 🔴 **La voz cuenta lo que la pantalla NO dice.** Si lee los titulares, sobra. La pantalla
  lleva los titulares; la voz arma la escena, pausa, pregunta.
- Los modelos expresivos (`eleven_v3`, `eleven_v4`) cuentan; el multilingüe recita. El v4
  habla más pausado: se escribe más corto, no se acelera.
- Se comprueba con Whisper sobre el MP4 final: así salen las palabras mal pronunciadas.

## El narrador con TU voz y un personaje propio (método)

Lo más fuerte que salió: un personaje de la marca (una «estampa» en pixel art con borde
blanco) que cuenta la historia con la voz **real** de la persona, grabada con el teléfono.
No viene un ejemplo listo porque el personaje es la cara de alguien; así se hace:

1. **El personaje:** base y unos 10 gestos (explica, señala, dedo arriba, cuenta, festeja…)
   generados desde fotos de la persona, sin fondo. La boca se retoca UNA vez en un gesto
   (cerrada, media, abierta) y se pasa a los demás con detección de cara (YuNet, en
   `recursos/modelos/`): la boca cae en el mismo lugar en todos.
2. **La voz:** se graba con tropiezos y retomas, sin presión. `tools/armar_voz.py <carpeta>`
   se queda con las tomas buenas (`edl.json`: tramos en segundos), ajusta cada borde al
   silencio medido y une con ruido del propio cuarto (el silencio digital se nota). Puede
   meter la frase de un cliente con otra voz, a su mismo nivel.
3. **La boca la decide la voz:** volumen por cuadro o, mejor, al ritmo de sílabas; cada
   estado dura al menos 2 cuadros para que no tiemble. La boca que solo abre y cierra con el
   volumen se ve «de muñeco».
4. **El gesto cambia por frase**, en el segundo de la palabra que lo pide, con un saltito; y
   cambia de lugar y tamaño cada 1.3-3 s. Quieto se siente lento.
5. **Fondos:** ilustraciones generadas por escena con movimiento lento; lo dibujado por código
   se vio «muy sencillo» para este formato. Pedir siempre «no text, no letters» y revisarlas
   en hoja antes de armar: salen letreros inventados y gráficas que dicen lo contrario de la
   historia.

- 🔴 **Buscar la palabra ancla CON acentos.** Sin acentos, «sí» casaba con «si un…» y el
  personaje se quedó en un solo gesto casi todo el video. Si la palabra se repite, se pide la
  ocurrencia exacta.
- ⚠️ **Whisper esconde arranques falsos** dentro de una palabra larga y adelanta los tiempos:
  los cortes se deciden con la energía de la grabación y transcribiendo la ventana suelta; al
  final se transcribe la voz armada y se lee de corrido contra el guion.
- Repetir en todos los videos lo que hace que se reconozca a la persona: el personaje, la
  tira de título con una palabra en color, su @ arriba y la misma tarjeta de cierre.

## Lo que costó el primero, y vale para todos

- 🔑 **`frame(t)` es determinista.** El azar de los trazos se siembra con el cuadro y el
  lienzo se limpia en cada cuadro, así que la vista previa y el render dibujan exactamente
  lo mismo, y un cambio en el motor se comprueba comparando capturas de antes y después
  píxel a píxel.
- 🔑 **Los cortes caen en la música.** La rejilla sale de `pipeline/musica.py`
  (`analizar` + `rejilla`) y las escenas se declaran por tiempos de beat, no a ojo.
- 🔴 **Las cifras se sacan de la fuente primaria**, y se anotan en `escenas.js` con su URL
  y la fecha en que se comprobaron. Un agregador puede citar un número que la página
  oficial no tiene: ese número no entra.
- 🔴 **El logo es el archivo real, nunca dibujado ni generado.** Las tipografías de una
  marca suelen tener licencia privada: se usa un parecido libre y se dice.
- ⚠️ **Un personaje que imita una terminal lleva pixeles de 1:2.** Hecho con pixeles
  cuadrados sale aplastado: en la terminal cada bloque es el doble de alto que de ancho.
  `sprite(..., { aspecto: 2 })`.
- ⚠️ **Lo que va fijo en pantalla (créditos, pies) se dibuja FUERA de `cam()`.** Con el
  zoom lento de un cierre, los pies de página se salen del cuadro en el último segundo.
- ⚠️ **Tachar un dato de comparación dice «falso».** El dato viejo contra el nuevo va en
  gris, sin tachar.
- 🔑 **Se revisa por capturas antes del render completo** (`--fotos`, una al final de cada
  escena, y se abre `hoja.png`), y al terminar se sacan cuadros **del MP4 final**, no de
  los PNG. Así salen monedas encima del texto, un «%» fuera de su sello o un personaje
  parado donde no va. Ninguno da error.
- ⚠️ **Para revisar un `.mov` transparente, `-ss` puede mentir.** Con qtrle, pedir un
  segundo puede devolver un cuadro anterior. La comprobación buena lee **todos** los
  cuadros y cuenta los píxeles opacos de cada uno.
- 📌 **Música libre de verdad**: la de Kevin MacLeod (CC BY) exige el crédito, y va en el
  pie del cierre. La de un pack de recursos no es libre solo por venir en el pack.
- 📌 **Música CC BY (Kevin MacLeod y similares): el crédito va en la descripción del post**
  («Música: Kevin MacLeod (incompetech.com), CC BY»). Es la condición de la licencia y es fácil
  olvidarlo al programar.
- ⚠️ **Inter no trae ★ ni ✓**: se dibujan (`palomita()`), no se confía en la letra.
- ⚠️ **En vertical, el viñeteado salía como una rueda gris** en el centro: el círculo se
  calculaba con el alto y el ancho mezclados. Ya usa el lado menor y el mayor.
