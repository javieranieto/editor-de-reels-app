"""Vertigo: la persona se queda quieta y el cuarto se acerca (o se aleja) detras.

Es el "dolly zoom" de cine, para una frase de revelacion ("y ahi me di cuenta").
La persona es el video real; el cuarto es una FOTO DEL CUARTO VACIO que se
reconstruye del mismo tramo y se agranda poco a poco detras de ella.

🔑 Por que hace falta el cuarto vacio: si se agranda el cuadro completo, tambien
se agranda la silueta de la persona, y alrededor del recorte queda un "fantasma"
mas grande que ella. Asi que el fondo se arma sin ella:
  - por cada pixel, el cuadro del tramo donde ESE pixel se ve con menos persona
    encima (la gente se mueve al hablar, asi que se va destapando);
  - lo que nunca se destapa (siempre detras del cuerpo) se rellena con lo de
    alrededor. Casi no se ve: el recorte queda encima y solo asoma una franja.

Sale un .mp4 opaco del tramo, sin audio, que en CapCut va encima como b-roll,
dentro de UN corte. 
Estado: aprobado 27-oct ("se ve bien").
"""
import os
import subprocess
import sys

import cv2
import numpy as np

if __package__ in (None, ""):   # corrido como comando: que encuentre el resto del editor
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.recorte import _medidas, capas


def _suave2(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def cuarto_vacio(cuadros, alfas, cada=3):
    """El fondo sin la persona, de una lista de cuadros RGB y sus alfas (0-255).
    Devuelve (imagen RGB, fraccion que hubo que inventar)."""
    sel = list(range(0, len(cuadros), cada))
    A = np.stack([alfas[i] for i in sel])                  # (n, H, W)
    mejor = A.argmin(axis=0)                              # el cuadro con menos persona en cada pixel
    C = np.stack([cuadros[i] for i in sel])               # (n, H, W, 3)
    H, W = mejor.shape
    fondo = C[mejor, np.arange(H)[:, None], np.arange(W)[None, :]]
    tapado = A.min(axis=0) > 40                           # nunca se vio sin la persona
    # el relleno se hace a un cuarto del tamano (rapido) y se sube suavizado: es una zona
    # que casi no se ve, y un relleno nitido llamaria la atencion
    chico = cv2.resize(fondo, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    m = cv2.resize(tapado.astype(np.uint8) * 255, (W // 4, H // 4), interpolation=cv2.INTER_NEAREST)
    m = cv2.dilate(m, np.ones((5, 5), np.uint8))
    relleno = cv2.inpaint(chico, m, 9, cv2.INPAINT_TELEA)
    relleno = cv2.GaussianBlur(cv2.resize(relleno, (W, H), interpolation=cv2.INTER_CUBIC), (0, 0), 6)
    mezcla = cv2.GaussianBlur(cv2.dilate(tapado.astype(np.float32), np.ones((15, 15), np.uint8)), (0, 0), 8)[..., None]
    fondo = (fondo * (1 - mezcla) + relleno * mezcla).astype(np.uint8)
    return fondo, float(tapado.mean())


def vertigo(video, destino, ini=None, fin=None, modo="acerca", escala=1.22, cuarto=None):
    """Escribe en `destino` (.mp4 opaco, sin audio) el tramo con el cuarto moviendose.

    modo   : "acerca" (el cuarto se viene encima) o "aleja" (se va hacia atras).
    escala : cuanto crece el cuarto de punta a punta (1.15-1.30).
    cuarto : si se da una ruta, ahi se guarda la imagen del cuarto vacio (para revisarla).
    """
    if modo not in ("acerca", "aleja"):
        sys.exit("modo tiene que ser 'acerca' o 'aleja'")
    if not 1.05 <= escala <= 1.40:
        sys.exit("escala %.2f fuera de rango (1.05-1.40)" % escala)
    W, H, fps, fps_txt = _medidas(video)
    originales, colores, alfas = [], [], []
    for o, c, a in capas(video, ini, fin):
        originales.append(o)
        colores.append(c)
        alfas.append(a)
    if not originales:
        sys.exit("No se pudo leer el tramo")
    fondo, inventado = cuarto_vacio(originales, alfas)
    print("  vertigo: cuarto vacio armado (%.0f%% rellenado, casi todo detras del cuerpo)" % (inventado * 100))
    if cuarto:
        cv2.imwrite(cuarto, cv2.cvtColor(fondo, cv2.COLOR_RGB2BGR))
    n = len(originales)
    esc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", "%dx%d" % (W, H), "-r", fps_txt, "-i", "-", "-c:v", "libx264",
                            "-crf", "16", "-pix_fmt", "yuv420p", destino], stdin=subprocess.PIPE)
    # el centro del zoom: a la altura de la cabeza (los ojos al 30%), para que el cuarto
    # "se abra" alrededor de la cara y no del pecho
    cy = H * 0.30
    for k in range(n):
        u = _suave2(k / max(1, n - 1))
        s = 1 + (escala - 1) * (u if modo == "acerca" else 1 - u)
        M = np.float32([[s, 0, W / 2 * (1 - s)], [0, s, cy * (1 - s)]])
        atras = cv2.warpAffine(fondo, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        a = alfas[k][..., None].astype(np.float32) / 255
        out = (atras * (1 - a) + colores[k] * a).clip(0, 255).astype(np.uint8)
        esc.stdin.write(out.tobytes())
    esc.stdin.close()
    if esc.wait() != 0:
        sys.exit("No se pudo escribir %s" % destino)
    return n


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Vertigo: el cuarto se acerca detras de la persona (.mp4)")
    p.add_argument("video")
    p.add_argument("--salida", required=True)
    p.add_argument("--ini", type=float)
    p.add_argument("--fin", type=float)
    p.add_argument("--modo", default="acerca", choices=["acerca", "aleja"])
    p.add_argument("--escala", type=float, default=1.22)
    p.add_argument("--cuarto", help="guardar aqui la imagen del cuarto vacio")
    a = p.parse_args()
    print(vertigo(a.video, a.salida, a.ini, a.fin, a.modo, a.escala, a.cuarto), "cuadros")
