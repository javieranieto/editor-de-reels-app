"""Tarjetas de pantalla completa que no necesitan el video: cortan a otra imagen.

  articulo  una pagina de articulo desenfocada salvo una palabra resaltada ("Claude", "GitHub")
  pixeles   una pantalla vista de cerca: cada palabra se enciende cuando se dice

Salen en .mp4 opaco, sin audio; en CapCut van encima como b-roll (la voz sigue abajo).

🔴 La pagina es GENERICA: sin el nombre, el logo ni el diseno de ningun sitio real.

Estado: articulo y pixeles aprobados 28-oct ("me gustaron todos")
"""
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

if __package__ in (None, ""):   # corrido como comando: que encuentre el resto del editor
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.detras import FPS, H, W, _suave
from pipeline.motion.base import marca_de

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUENTES = os.path.join(RAIZ, "recursos", "fuentes")

# texto de relleno PROPIO para la pagina (sale desenfocado; solo se lee la palabra resaltada)
# 🔴 Con acentos: las lineas junto a la palabra se leen nitidas, y una falta de ortografia ahi se nota.
RELLENO = ("Los negocios que contestan rápido cierran más ventas que los que tienen mejores anuncios. "
           "La diferencia casi nunca está en la publicidad sino en lo que pasa después del primer mensaje. "
           "Un cliente que pregunta el precio ya decidió que le interesa, y lo que sigue es darle una razón "
           "para quedarse. Medir cuánto se tarda la respuesta es el primer paso para mejorarla. ")


def _f(nombre, tam):
    return ImageFont.truetype(os.path.join(FUENTES, nombre), tam)


def _escribir(cuadros, destino):
    esc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-", "-c:v", "libx264",
                            "-crf", "16", "-pix_fmt", "yuv420p", destino], stdin=subprocess.PIPE)
    n = 0
    for c in cuadros:
        esc.stdin.write(c.tobytes())
        n += 1
    esc.stdin.close()
    if esc.wait() != 0 or n == 0:
        sys.exit("No se pudo escribir %s" % destino)
    return n


# --- corte a articulo ---------------------------------------------------------

def articulo(destino, palabra, dur=2.5, marca=None):
    """La pagina de un articulo, desenfocada lejos de la linea del centro, con `palabra`
    en un recuadro de acento. La camara se acerca despacio a la palabra."""
    m = marca_de(marca)
    fp = _f("OpenSans-VF.ttf", 40)
    if fp.getlength(palabra) > W * 0.6:
        sys.exit("«%s» es muy larga para resaltarla" % palabra)
    # la pagina, mas grande que el cuadro, para tener de donde acercarse
    PWp, PHp = int(W * 1.3), int(H * 1.3)
    pag = Image.new("RGB", (PWp, PHp), (252, 251, 248))
    d = ImageDraw.Draw(pag)
    renglon = 62
    margen = 110
    palabras = (RELLENO * 12).split()
    y, k, centro_y = 160, 0, PHp // 2
    fila_centro = None
    while y < PHp - 120:
        linea, x = [], margen
        while k < len(palabras) and x + fp.getlength(palabras[k] + " ") < PWp - margen:
            linea.append(palabras[k])
            x += fp.getlength(palabras[k] + " ")
            k += 1
        if fila_centro is None and y >= centro_y - renglon // 2:
            fila_centro = y
            # la linea del centro lleva la palabra, en su recuadro
            antes = " ".join(linea[:3]) + " "
            despues = " " + " ".join(linea[3:6])
            x0 = (PWp - fp.getlength(antes + palabra + despues)) / 2
            d.text((x0, y), antes, font=fp, fill=(70, 74, 86))
            xp = x0 + fp.getlength(antes)
            d.rounded_rectangle((xp - 14, y - 8, xp + fp.getlength(palabra) + 14, y + 54), 12, fill=m.ACENTO)
            d.text((xp, y), palabra, font=fp, fill=(255, 255, 255))
            d.text((xp + fp.getlength(palabra), y), despues, font=fp, fill=(70, 74, 86))
        else:
            d.text((margen, y), " ".join(linea), font=fp, fill=(70, 74, 86))
        y += renglon
    base = np.asarray(pag)
    # desenfoque por distancia a la linea del centro: nitida en medio, borrosa lejos
    borrosa = cv2.GaussianBlur(base, (0, 0), 9)
    yy = np.abs(np.arange(PHp) - (fila_centro + 22))[:, None, None]
    peso = np.clip((yy - 40) / 260, 0, 1).astype(np.float32)
    pag = (base * (1 - peso) + borrosa * peso).astype(np.uint8)
    cx = PWp / 2
    cy = fila_centro + 22
    n = int(round(dur * FPS))

    def cuadros():
        for k2 in range(n):
            t = k2 / FPS
            s = 1.0 + 0.25 * _suave(t / dur)              # se acerca despacio
            w, h = W / s, H / s
            x0, y0 = cx - w / 2, cy - h / 2
            M = np.float32([[s, 0, -x0 * s], [0, s, -y0 * s]])
            yield cv2.warpAffine(pag, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=(252, 251, 248))

    return _escribir(cuadros(), destino)


# --- letras en pixeles --------------------------------------------------------

def _subpixeles():
    """Una textura de pantalla vista de cerca: celdas con su rojo, verde y azul apagados."""
    celda = 9
    tex = np.zeros((H, W, 3), np.uint8)
    for i, col in enumerate(((60, 8, 10), (8, 50, 14), (10, 14, 64))):
        tex[:, i * 3::celda, :] = col
        tex[:, i * 3 + 1::celda, :] = col
    tex[::celda, :, :] = 0
    return tex


def pixeles(destino, palabras, dur=None, marca=None):
    """La frase en una pantalla vista de cerca; cada palabra se enciende en su segundo.

    palabras : [(segundo, "palabra")] en segundos del .mp4 (las de la propia voz).
    """
    if not palabras:
        sys.exit("pixeles necesita las palabras de la frase")
    if dur is None:
        dur = palabras[-1][0] + 1.0
    ft = _f("Poppins-Bold.ttf", 118)
    # acomodar en lineas centradas
    lineas, linea = [], []
    for s, p in palabras:
        if ft.getlength(" ".join([x[1] for x in linea] + [p])) > W * 0.86 and linea:
            lineas.append(linea)
            linea = []
        linea.append((s, p))
    lineas.append(linea)
    if len(lineas) > 5:
        sys.exit("La frase no cabe en 5 lineas: usala mas corta")
    alto = 150
    y0 = (H - alto * len(lineas)) / 2
    tex = _subpixeles()
    n = int(round(dur * FPS))

    def cuadros():
        for k in range(n):
            t = k / FPS
            img = Image.new("L", (W, H), 0)
            d = ImageDraw.Draw(img)
            for j, l in enumerate(lineas):
                texto = " ".join(p for _, p in l)
                x = (W - ft.getlength(texto)) / 2
                for s, p in l:
                    brillo = 255 * _suave((t - s) / 0.12) if t >= s else 38
                    d.text((x, y0 + j * alto), p, font=ft, fill=int(brillo))
                    x += ft.getlength(p + " ")
            luz = np.asarray(img, np.float32) / 255
            halo = cv2.GaussianBlur(luz, (0, 0), 14) * 0.7
            luz = np.clip(luz + halo, 0, 1)[..., None]
            calido = np.array([255, 236, 214], np.float32)
            frame = tex.astype(np.float32) * (1 - luz) + calido * luz
            # la pantalla "respira": se acerca un poco
            s = 1 + 0.06 * (t / dur)
            M = np.float32([[s, 0, W / 2 * (1 - s)], [0, s, H / 2 * (1 - s)]])
            yield cv2.warpAffine(frame.clip(0, 255).astype(np.uint8), M, (W, H))

    return _escribir(cuadros(), destino)
