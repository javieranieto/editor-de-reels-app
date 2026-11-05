# Fuentes del video animado

| Archivo | Familia | Autores (según el archivo) | Licencia |
|---|---|---|---|
| `Caveat-Bold.ttf` | Caveat Bold | The Caveat Project Authors | SIL Open Font License 1.1 |
| `Inter.ttf` | Inter (variable, 100-900) | The Inter Project Authors | SIL Open Font License 1.1 |
| `SilkscreenBold.ttf` | Silkscreen Bold | The Silkscreen Project Authors | SIL Open Font License 1.1 |
| `SourceSerif4.ttf` | Source Serif 4 (variable, 200-900) | Adobe, con nombre reservado «Source» | SIL Open Font License 1.1 |
| `Montserrat-Bold.ttf`, `-ExtraBold.ttf`, `-Black.ttf` | Montserrat 700/800/900 | The Montserrat Project Authors | SIL Open Font License 1.1 |

La licencia se leyó de la tabla `name` de cada `.ttf` (campos de copyright y de licencia),
no del nombre del archivo. Todas están en [Google Fonts](https://fonts.google.com).
La **OFL** permite usarlas, incrustarlas en videos e imágenes y redistribuirlas junto con
software; **no se venden solas** y, si se modifican, no pueden llevar el mismo nombre
(«Source» es nombre reservado). Texto completo: <https://openfontlicense.org>.

## Para qué es cada una

- **Source Serif 4** (`SSerif`): los titulares, la letra por defecto de `txt()`.
- **Inter** (`Inter`): cifras, rótulos y pies; `coin()` y `trophy()` la usan.
- **Caveat** (`Hand`): lo escrito a mano, las notas al margen.
- **Silkscreen** (`Pix`): lo de 8 bits; `header()` y el pueblo de negocios la usan.
- **Montserrat** (`Mont`, `MontX`, `MontB`): la letra de la marca de ejemplo (`marcas/marca_ejemplo.js`) y del noticiero.

Cada video declara las que usa en `configurar({ fuentes: {...} })`. Si la marca del video
tiene tipografías de licencia privada, se busca un parecido libre, se pone aquí con su
licencia comprobada igual que estas, y se dice al entregar.
