"""Efectos que van DETRAS de la persona: la pista de en medio.

En CapCut van tres pistas, de abajo arriba:

    1. el video original
    2. uno de estos .mov (letras, tarjetas, graficas)
    3. el recorte de la persona (pipeline/recorte.py), que tapa lo de la 2

Estos .mov no traen a la persona ni el fondo: solo el grafico, con alfa. Por eso
son qtrle/argb como el resto del motion (colores casi planos, pesan poco) y no
ProRes como el recorte.

Los colores y las letras salen de la marca (marca/colores.json): ver pipeline/motion/base.py.

Estado de cada efecto (sube a aprobado solo cuando Javier lo ve sobre su video y dice que si):
  letras_vidrio   aprobado 27-oct ("si, se ven bien", probado en CapCut con las 3 pistas)
  portada         aprobado 27-oct ("si, se ven bien todos esos")
  telefono        aprobado 27-oct (pipeline/telefono.py; va en esta misma pista de en medio)
  acercamiento    aprobado 27-oct; NO va aqui: es un mp4 del tramo encima del video (pipeline/acercamiento.py).
                  Lo vio y le parecio bien, aunque en agosto rechazo los zooms animados de CapCut: el golpe
                  de 5 cuadros con desenfoque se lee como camara, no como efecto.
"""
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUENTES = os.path.join(RAIZ, "recursos", "fuentes")
W, H, FPS = 1080, 1920, 30


def _suave(t):
    """Salida rapida y llegada lenta (ease-out cubico): se siente puesto, no deslizado."""
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 3


def _exportar(cuadros, destino):
    """Escribe una lista (o generador) de cuadros RGBA uint8 HxWx4 a .mov qtrle/argb."""
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba",
                           "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-",
                           "-c:v", "qtrle", "-pix_fmt", "argb", destino], stdin=subprocess.PIPE)
    n = 0
    for c in cuadros:
        ff.stdin.write(c.tobytes())
        n += 1
    ff.stdin.close()
    if ff.wait() != 0 or n == 0:
        sys.exit("No se pudo escribir %s" % destino)
    return n


# --- letras de vidrio ---------------------------------------------------------

def _capa_palabra(palabra, alto_letra, fuente, cabe=0.88, tope=330):
    """Mascaras (0-1) de cada letra en un lienzo del ancho del cuadro, centradas.
    `fuente` es un nombre de recursos/fuentes o una ruta completa. Sin `alto_letra`
    usa el mas grande que quepa en `cabe` del ancho, hasta `tope`. Aborta si no cabe."""
    ruta = fuente if os.path.isabs(fuente) else os.path.join(FUENTES, fuente)
    if alto_letra is None:
        alto_letra = tope
        while ImageFont.truetype(ruta, alto_letra).getlength(palabra) > W * cabe:
            alto_letra -= 6
    f = ImageFont.truetype(ruta, alto_letra)
    ancho = f.getlength(palabra)
    if ancho > W * 0.96:
        sys.exit("«%s» no cabe a %d px (mide %d de %d). Usa menos letras o un tamano menor."
                 % (palabra, alto_letra, ancho, W * 0.96))
    x0 = (W - ancho) / 2
    # Lienzo de solo la franja de la palabra (no el cuadro entero): 4 veces menos
    # pixeles por letra y por cuadro. Arriba cabe el filo; abajo, el canto.
    caja = f.getbbox(palabra)
    alto = (caja[3] - caja[1]) + 2 * BORDE + PROFUNDIDAD
    letras = []
    for i, ch in enumerate(palabra):
        if ch == " ":
            continue
        lienzo = Image.new("L", (W, alto), 0)
        ImageDraw.Draw(lienzo).text((x0 + f.getlength(palabra[:i]), BORDE - caja[1]), ch, font=f, fill=255)
        letras.append(np.asarray(lienzo, np.float32) / 255.0)
    return letras


BORDE = 24          # aire arriba y a los lados de la letra, para el filo y el desenfoque
PROFUNDIDAD = 18    # grosor del canto: lo que la hace leerse como un letrero de acrilico


def _correr(m, dy, dx):
    """La mascara corrida dy hacia abajo y dx a la derecha, sin dar la vuelta por el otro lado."""
    out = np.zeros_like(m)
    out[dy:, dx:] = m[: m.shape[0] - dy, : m.shape[1] - dx]
    return out


def _vidrio(m):
    """De una mascara de letra (0-1) a una capa RGBA de vidrio grueso que se lee:
    cara blanca translucida (mas clara arriba), canto azulado abajo-derecha que da
    el grosor, y un filo de luz arriba-izquierda. Lo primero es que se LEA: con
    vidrio demasiado fino la palabra se pierde contra cualquier pared clara."""
    import cv2
    alto = m.shape[0]
    canto = np.zeros_like(m)
    for d in range(1, PROFUNDIDAD + 1):
        canto = np.maximum(canto, _correr(m, d, d // 2))
    canto = np.clip(canto - m, 0, 1)
    cara = m * np.linspace(0.78, 0.50, alto)[:, None]
    nucleo = cv2.erode(m, np.ones((7, 7), np.uint8))
    filo = np.clip(m - nucleo, 0, 1) * 0.55 + np.clip(m - _correr(m, 5, 5), 0, 1) * 0.45
    rgba = np.zeros(m.shape + (4,), np.float32)
    # de abajo arriba: canto, cara, filo (mezcla "encima" en alfa recto)
    for color, a in (((120, 138, 185), canto * 0.80), ((236, 242, 255), cara), ((255, 255, 255), filo)):
        a = a[..., None]
        sa = rgba[..., 3:]
        out = a + sa * (1 - a)
        rgba[..., :3] = np.where(out > 0, (np.array(color) * a + rgba[..., :3] * sa * (1 - a)) / np.maximum(out, 1e-4), 0)
        rgba[..., 3:] = out
    return rgba


def letras_vidrio(palabra, destino, dur=4.0, alto_letra=None, y=0.11, fuente="Poppins-Bold.ttf",
                  perspectiva=0.18, escalon=0.07, entrada=0.55, salida=0.35):
    """Una palabra grande de vidrio en la pared, detras de la persona.

    palabra     : en mayusculas se lee mejor (VISTO, FOCO, DATOS). Corta: 4-7 letras.
    dur         : segundos que dura el .mov completo (entrada + quieta + salida).
    y           : donde empieza la franja de la palabra, en fraccion del cuadro. Deja la
                  mitad de arriba de las letras asomando sobre la cabeza en un plano medio
                  (0.11 = la cabeza tapa el tercio de abajo de las letras del centro).
    perspectiva : cuanto se encoge el lado derecho (0 = de frente, 0.18 = se aleja un poco).
    escalon     : segundos entre una letra y la siguiente al entrar.
    """
    palabra = palabra.upper()
    letras = _capa_palabra(palabra, alto_letra, fuente)
    capas = [_vidrio(m) for m in letras]
    # cada capa vive en un lienzo alto como la letra; se pega en y del cuadro
    alto = capas[0].shape[0]
    top = int(H * y)

    # perspectiva: el lado derecho mas bajito, como una pared que se aleja
    import cv2
    origen = np.float32([[0, 0], [W, 0], [W, alto], [0, alto]])
    p = perspectiva * alto / 2
    meta = np.float32([[0, 0], [W, p], [W, alto - p], [0, alto]])
    M = cv2.getPerspectiveTransform(origen, meta)

    n = int(round(dur * FPS))

    def cuadros():
        for k in range(n):
            t = k / FPS
            lienzo = np.zeros((H, W, 4), np.float32)
            fuera = _suave((t - (dur - salida)) / salida) if t > dur - salida else 0.0
            # un reflejo diagonal que cruza la palabra una vez, cuando ya llegaron todas
            llegada = entrada + escalon * len(capas)
            brillo_x = (t - llegada) / 1.2 * (W + 400) - 200
            for i, c in enumerate(capas):
                avance = _suave((t - i * escalon) / entrada)
                if avance <= 0:
                    continue
                capa = c.copy()
                if 0 < brillo_x < W + 200:
                    xs = np.arange(W)[None, :] + np.arange(alto)[:, None] * 0.5
                    banda = np.exp(-((xs - brillo_x) / 60.0) ** 2) * 0.5
                    capa[..., 3] = np.clip(capa[..., 3] + banda * (c[..., 3] > 0.02), 0, 1)
                capa[..., 3] *= avance * (1 - fuera)
                img = Image.fromarray(np.dstack([capa[..., :3], capa[..., 3:] * 255])
                                      .clip(0, 255).astype(np.uint8), "RGBA")
                desenfoque = (1 - avance) * 14
                if desenfoque > 0.5:
                    img = img.filter(ImageFilter.GaussianBlur(desenfoque))
                arr = cv2.warpPerspective(np.asarray(img, np.float32), M, (W, alto))
                dy = int((1 - avance) * 70)
                y0 = top + dy
                y1 = min(H, y0 + alto)
                sub = arr[: y1 - y0]
                a = sub[..., 3:] / 255.0
                dst = lienzo[y0:y1]
                # mezcla "encima" en alfa recto
                out_a = a + dst[..., 3:] * (1 - a)
                dst[..., :3] = np.where(out_a > 0, (sub[..., :3] * a + dst[..., :3] * dst[..., 3:] * (1 - a))
                                        / np.maximum(out_a, 1e-4), 0)
                dst[..., 3:] = out_a
            out = lienzo.copy()
            out[..., 3] *= 255
            yield out.clip(0, 255).astype(np.uint8)

    return _exportar(cuadros(), destino)


# --- portada de revista -------------------------------------------------------

# Bodoni Moda (Google Fonts, licencia OFL, en recursos/fuentes). No tiene version angosta, asi
# que la portada luce mas con palabras CORTAS: con menos letras, cada una sale mas alta y la
# cabeza alcanza a taparla.
BODONI = os.path.join(FUENTES, "BodoniModa.ttf")


def portada(palabra, destino, dur=4.0, encabezado=None, y=0.12, fuente=BODONI,
            escalon=0.05, entrada=0.6, salida=0.35):
    """Una palabra gigante arriba, de lado a lado, como el nombre de una revista,
    que la cabeza tapa por en medio. Blanca y solida: aqui el chiste es el tamano.

    encabezado : linea chica opcional encima (\"EL TEMA DE HOY\"), con letras espaciadas.
    y          : donde empieza la franja de la palabra. 0.12 deja que la cabeza tape el
                 tercio de abajo de las letras del centro; con la letra ancha no se alcanzaba
                 (quedaba toda encima de la cabeza), por eso va la condensada.
    """
    import cv2
    palabra = palabra.upper()
    if not os.path.exists(fuente):
        sys.exit("No encuentro la tipografia %s" % fuente)
    letras = _capa_palabra(palabra, None, fuente, cabe=0.95, tope=620)
    alto = letras[0].shape[0]
    top = int(H * y)
    # encabezado: Poppins chica y espaciada, centrada justo encima de la palabra
    cab = None
    if encabezado:
        fc = ImageFont.truetype(os.path.join(FUENTES, "Poppins-SemiBold.ttf"), 34)
        txt = "   ".join(encabezado.upper())
        img = Image.new("L", (W, 60), 0)
        ImageDraw.Draw(img).text(((W - fc.getlength(txt)) / 2, 6), txt, font=fc, fill=235)
        cab = np.asarray(img, np.float32) / 255.0
    n = int(round(dur * FPS))
    llegada = entrada + escalon * len(letras)

    def cuadros():
        for k in range(n):
            t = k / FPS
            fuera = _suave((t - (dur - salida)) / salida) if t > dur - salida else 0.0
            a_total = np.zeros((H, W), np.float32)
            for i, m in enumerate(letras):
                avance = _suave((t - i * escalon) / entrada)
                if avance <= 0:
                    continue
                capa = m * avance
                borroso = (1 - avance) * 12
                if borroso > 0.5:
                    capa = cv2.GaussianBlur(capa, (0, 0), borroso)
                y0 = top + int((1 - avance) * 90 - fuera * 30)
                y1 = min(H, y0 + alto)
                a_total[max(0, y0):y1] = np.maximum(a_total[max(0, y0):y1], capa[: y1 - max(0, y0)])
            if cab is not None:
                av = _suave((t - llegada + 0.2) / 0.4)
                yc = max(0, top - 48)
                a_total[yc:yc + cab.shape[0]] = np.maximum(a_total[yc:yc + cab.shape[0]], cab * av)
            a_total *= 1 - fuera
            out = np.zeros((H, W, 4), np.uint8)
            out[..., :3] = 255
            out[..., 3] = (a_total * 255).clip(0, 255).astype(np.uint8)
            yield out

    return _exportar(cuadros(), destino)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Efectos detras de la persona (.mov con alfa para CapCut)")
    p.add_argument("efecto", choices=["vidrio", "portada"])
    p.add_argument("palabra")
    p.add_argument("--salida", required=True)
    p.add_argument("--dur", type=float, default=4.0)
    p.add_argument("--y", type=float, help="donde empieza la franja de la palabra (fraccion del cuadro)")
    p.add_argument("--encabezado", help="portada: linea chica encima de la palabra")
    a = p.parse_args()
    if a.efecto == "vidrio":
        n = letras_vidrio(a.palabra, a.salida, dur=a.dur, y=a.y if a.y is not None else 0.11)
    else:
        n = portada(a.palabra, a.salida, dur=a.dur, encabezado=a.encabezado,
                    y=a.y if a.y is not None else 0.12)
    print("%s: %d cuadros (%.1f s)" % (a.salida, n, n / FPS))
