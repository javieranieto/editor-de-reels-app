"""Revelacion del editor: el video se encoge a una ventana y un panel palomea los pasos.

Para "este video lo edito Claude": en una palabra, el cuadro completo se encoge
a una ventana de editor sobre un escritorio claro (barra de titulo con el nombre
del archivo, el video sigue corriendo adentro), y arriba entra un panel con los
pasos del trabajo; cada uno gira mientras "trabaja" y se palomea en su segundo.

Sale un .mp4 opaco del tramo, sin audio, que en CapCut va encima como un b-roll.

Estado: aprobado 27-oct ("revisado, me gusta").
"""
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

if __package__ in (None, ""):   # corrido como comando: que encuentre el resto del editor
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.acercamiento import _leer, _medidas
from pipeline.detras import _suave
from pipeline.motion.base import marca_de

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUENTES = os.path.join(RAIZ, "recursos", "fuentes")
ESCRITORIO = (243, 240, 233)
ESCALA_FINAL = 0.60
BARRA = 46


def _f(nombre, tam):
    return ImageFont.truetype(os.path.join(FUENTES, nombre), tam)


def _suave2(t):
    """Entrada y salida suaves (ease-in-out): un movimiento de camara, no un golpe."""
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def _panel(titulo, pasos, t, m, ancho):
    """El panel de pasos en el segundo t: [(segundo_listo, texto)]. Un paso 'trabaja'
    (gira) desde que el anterior quedo listo hasta su segundo."""
    ft, fp = _f("Poppins-SemiBold.ttf", 34), _f("Poppins-Medium.ttf", 38)
    renglon = 76
    alto = 110 + renglon * len(pasos) + 24
    img = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((8, 12, ancho - 1, alto - 1), 30, fill=(0, 0, 0, 40))        # sombra corta
    d.rounded_rectangle((0, 0, ancho - 9, alto - 13), 30, fill=(255, 255, 255, 255))
    d.ellipse((36, 38, 60, 62), fill=m.ACENTO)
    d.text((76, 30), titulo, font=ft, fill=m.FONDO)
    previo = -1e9
    for i, (listo, texto) in enumerate(pasos):
        y = 100 + i * renglon
        cx, cy, r = 54, y + 26, 17
        if t >= listo:
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=m.ACENTO)
            d.line([(cx - 8, cy), (cx - 2, cy + 6), (cx + 9, cy - 7)], fill=(255, 255, 255), width=4)
            color = m.FONDO
        elif t >= previo:
            ang = (t * 360 * 1.4) % 360
            d.arc((cx - r, cy - r, cx + r, cy + r), ang, ang + 270, fill=m.ACENTO, width=4)
            color = m.FONDO
        else:
            d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(205, 210, 220), width=3)
            color = (160, 166, 180)
        d.text((cx + 36, y + 4), texto, font=fp, fill=color)
        previo = listo
    return img


def revelar(video, destino, pasos, en, ini=None, fin=None, titulo="Editor de reels",
            archivo="mi-video.mp4", marca=None, achicar=0.8):
    """Escribe en `destino` (.mp4 opaco, sin audio) el tramo con la revelacion.

    pasos : [(segundo, "texto")] en segundos del tramo: cuando queda palomeado cada uno. 2 a 5.
    en    : segundo del tramo en que el video empieza a encogerse.
    """
    m = marca_de(marca)
    W, H, fps, fps_txt = _medidas(video)
    pasos = sorted(pasos)
    if not 2 <= len(pasos) <= 5:
        sys.exit("La revelacion lleva de 2 a 5 pasos (trae %d)" % len(pasos))
    fp = _f("Poppins-Medium.ttf", 38)
    ancho_panel = int(W * 0.84)
    for _, txt in pasos:
        if fp.getlength(txt) > ancho_panel - 150:
            sys.exit("El paso «%s» no cabe en el panel: acortalo" % txt)
    fb = _f("Poppins-Medium.ttf", 24)
    # donde queda la ventana al final: centrada abajo, con aire para el panel arriba
    ww, wh = int(W * ESCALA_FINAL), int(H * ESCALA_FINAL)
    destino_cx, destino_cy = W / 2, H - 70 - wh / 2
    esc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", "%dx%d" % (W, H), "-r", fps_txt, "-i", "-", "-c:v", "libx264",
                            "-crf", "16", "-pix_fmt", "yuv420p", destino], stdin=subprocess.PIPE)
    n = 0
    for k, cuadro in enumerate(_leer(video, ini, fin, W, H)):
        t = k / fps
        a = _suave2((t - en) / achicar)                  # 0 = pantalla completa, 1 = ventana
        if a <= 0:
            esc.stdin.write(cv2.cvtColor(cuadro, cv2.COLOR_BGR2RGB).tobytes())
            n += 1
            continue
        s = 1 - (1 - ESCALA_FINAL) * a
        cx = W / 2 + (destino_cx - W / 2) * a
        cy = H / 2 + (destino_cy - H / 2) * a
        lienzo = Image.new("RGBA", (W, H), ESCRITORIO + (255,))
        vw, vh = int(W * s), int(H * s)
        vid = Image.fromarray(cv2.cvtColor(cv2.resize(cuadro, (vw, vh), interpolation=cv2.INTER_AREA),
                                           cv2.COLOR_BGR2RGB)).convert("RGBA")
        # la barra de la ventana aparece conforme se encoge (a pantalla completa no hay ventana)
        barra = int(BARRA * a)
        ventana = Image.new("RGBA", (vw, vh + barra), (0, 0, 0, 0))
        dv = ImageDraw.Draw(ventana)
        dv.rounded_rectangle((0, 0, vw - 1, vh + barra - 1), int(22 * a), fill=(255, 255, 255, 255))
        if barra > 12:
            for i, col in enumerate(((236, 95, 90), (245, 190, 80), (98, 200, 110))):
                dv.ellipse((18 + i * 26, barra / 2 - 7, 32 + i * 26, barra / 2 + 7), fill=col)
            dv.text(((vw - fb.getlength(archivo)) / 2, barra / 2 - 15), archivo, font=fb, fill=(110, 116, 130))
        ventana.paste(vid, (0, barra))
        sombra = Image.new("RGBA", (vw + 80, vh + barra + 80), (0, 0, 0, 0))
        ImageDraw.Draw(sombra).rounded_rectangle((40, 54, vw + 40, vh + barra + 54), 24, fill=(0, 0, 0, int(70 * a)))
        sombra = Image.fromarray(cv2.GaussianBlur(np.asarray(sombra), (0, 0), 18))
        lienzo.alpha_composite(sombra, (int(cx - vw / 2 - 40), int(cy - (vh + barra) / 2 - 40)))
        lienzo.alpha_composite(ventana, (int(cx - vw / 2), int(cy - (vh + barra) / 2)))
        # panel: baja desde arriba cuando la ventana ya va a la mitad
        p_a = _suave((t - en - achicar * 0.5) / 0.45)
        if p_a > 0:
            panel = _panel(titulo, pasos, t, m, ancho_panel)
            py = 70 + (1 - p_a) * -60
            arr = np.asarray(panel).copy()
            arr[..., 3] = (arr[..., 3] * p_a).astype(np.uint8)
            lienzo.alpha_composite(Image.fromarray(arr, "RGBA"), (int((W - ancho_panel) / 2), int(py)))
        esc.stdin.write(np.asarray(lienzo.convert("RGB"), np.uint8).tobytes())
        n += 1
    esc.stdin.close()
    if esc.wait() != 0 or n == 0:
        sys.exit("No se pudo escribir %s" % destino)
    return n


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Revelacion del editor (.mp4 para CapCut)")
    p.add_argument("video")
    p.add_argument("--salida", required=True)
    p.add_argument("--ini", type=float)
    p.add_argument("--fin", type=float)
    p.add_argument("--en", type=float, required=True, help="segundo del tramo en que se encoge")
    p.add_argument("--paso", action="append", required=True, metavar="SEG:TEXTO")
    a = p.parse_args()
    pasos = [(float(x.split(":", 1)[0]), x.split(":", 1)[1]) for x in a.paso]
    print(revelar(a.video, a.salida, pasos, a.en, a.ini, a.fin), "cuadros")
