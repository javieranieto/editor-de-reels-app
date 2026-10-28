"""Tarjeta de cierre con un muro de miniaturas: "comenta REPO y te lo mando".

Llena la pantalla (no es una capa con alfa): fondo de la marca, un titular con
la raya de acento, una linea opcional abajo, y un muro de 5 x 4 miniaturas en
vertical que aparecen en diagonal y suben despacio. Las miniaturas salen de
videos propios (un cuadro de cada uno) o de imagenes.

En CapCut va como b-roll sobre el final: la voz sigue sonando debajo.
Sale en .mp4 opaco.

🔴 Las miniaturas son de material PROPIO. Nunca de un cliente: en un muro se ven
pequenas pero se reconocen (un taller, un logo, una cara).

Estado: aprobado 27-oct ("me gusta, quedo bien").
"""
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

if __package__ in (None, ""):   # corrido como comando: que encuentre el resto del editor
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.detras import FPS, H, W, _suave
from pipeline.motion.base import marca_de

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUENTES = os.path.join(RAIZ, "recursos", "fuentes")
COLS, FILAS, HUECO, ORILLA = 5, 4, 14, 50
DERIVA = 14     # px por segundo que sube el muro


def _f(nombre, tam):
    return ImageFont.truetype(os.path.join(FUENTES, nombre), tam)


def miniatura(origen, ancho, alto, momento=0.35):
    """Un cuadro vertical de `origen` (video o imagen), recortado al centro a ancho x alto."""
    if origen.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
        img = Image.open(origen).convert("RGB")
    else:
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                    "-of", "csv=p=0", origen], capture_output=True, text=True).stdout or 0)
        r = subprocess.run(["ffmpeg", "-v", "error", "-ss", "%.2f" % (dur * momento), "-i", origen,
                            "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True)
        if not r.stdout:
            sys.exit("No pude sacar un cuadro de %s" % origen)
        import io
        img = Image.open(io.BytesIO(r.stdout)).convert("RGB")
        # un cuadro casi negro (un corte, un fundido) no sirve de miniatura: se busca otro momento
        # (se mira tambien la mitad de arriba: un reel con un fundido arriba promedia bien y se ve roto)
        arr = np.asarray(img)
        negros_arriba = (arr[: arr.shape[0] // 2].max(axis=-1) < 45).mean()
        if (arr.mean() < 35 or negros_arriba > 0.5) and momento < 0.9:
            return miniatura(origen, ancho, alto, momento + 0.13)
    # recorte al centro con la proporcion de la miniatura
    rel = ancho / alto
    w, h = img.size
    if w / h > rel:
        nw = int(h * rel)
        img = img.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else:
        nh = int(w / rel)
        img = img.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    return img.resize((ancho, alto), Image.LANCZOS)


def _redondear(img, radio):
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, img.width - 1, img.height - 1), radio, fill=255)
    out = img.convert("RGBA")
    out.putalpha(m)
    return out


def cierre_muro(destino, titular, fuentes, linea=None, dur=4.0, marca=None):
    """Escribe en `destino` (.mp4 opaco, sin audio) la tarjeta de cierre.

    titular : 1 o 2 lineas cortas ("Te lo regalo", "Comenta REPO").
    fuentes : videos o imagenes propios para el muro (se repiten si son menos de 20).
    linea   : texto chico opcional bajo el titular.
    """
    m = marca_de(marca)
    if not fuentes:
        sys.exit("El cierre necesita al menos un video o imagen para el muro")
    tw = int((W - 2 * ORILLA - (COLS - 1) * HUECO) / COLS)
    th = int(tw * 16 / 9)
    minis = []
    for i in range(COLS * FILAS):
        f = fuentes[i % len(fuentes)]
        # si un video se repite, se toma otro momento para que no salgan dos iguales
        momento = 0.2 + 0.6 * ((i // len(fuentes)) * 0.37 % 1)
        minis.append(_redondear(miniatura(f, tw, th, momento), 16))

    ft = _f("Poppins-Bold.ttf", 104)
    lineas = titular.split("\n") if "\n" in titular else [titular]
    for l in lineas:
        if ft.getlength(l) > W - 2 * ORILLA:
            sys.exit("El titular «%s» no cabe: partelo con \\n o acortalo" % l)
    fondo = tuple(int(c * 0.62) for c in m.FONDO)   # el azul de la marca, mas oscuro para que el muro resalte
    alto_tit = 126 * len(lineas)
    y_tit = 170
    # el muro sube despacio todo el tiempo (DERIVA px/s): arranca esa distancia mas abajo
    # para que al final no tape la linea de abajo del titular
    y_muro = y_tit + alto_tit + (110 if linea else 60) + int(DERIVA * dur)
    n = int(round(dur * FPS))
    grad = np.zeros((H, W, 4), np.uint8)
    grad[..., :3] = fondo
    grad[H - 240:, :, 3] = (np.linspace(0, 255, 240) ** 1.2 / 255 ** 0.2).clip(0, 255).astype(np.uint8)[:, None]
    desvanecido = Image.fromarray(grad, "RGBA")

    esc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-", "-c:v", "libx264",
                            "-crf", "16", "-pix_fmt", "yuv420p", destino], stdin=subprocess.PIPE)
    for k in range(n):
        t = k / FPS
        img = Image.new("RGBA", (W, H), fondo + (255,))
        d = ImageDraw.Draw(img)
        # titular: entra primero
        a_tit = _suave(t / 0.4)
        capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dc = ImageDraw.Draw(capa)
        for j, l in enumerate(lineas):
            dc.text(((W - ft.getlength(l)) / 2, y_tit + j * 126 + (1 - a_tit) * 30), l, font=ft, fill=m.TEXTO)
        ancho_raya = min(ft.getlength(lineas[-1]), 260) * _suave((t - 0.2) / 0.4)
        dc.rounded_rectangle(((W - ancho_raya) / 2, y_tit + alto_tit + 6, (W + ancho_raya) / 2, y_tit + alto_tit + 14),
                             4, fill=m.ACENTO)
        if linea:
            fl = _f("Poppins-Medium.ttf", 44)
            dc.text(((W - fl.getlength(linea)) / 2, y_tit + alto_tit + 40), linea, font=fl, fill=m.TENUE)
        a = np.asarray(capa).copy()
        a[..., 3] = (a[..., 3] * a_tit).astype(np.uint8)
        img.alpha_composite(Image.fromarray(a, "RGBA"))
        # muro: en diagonal, desde arriba a la izquierda; sube despacio todo el tiempo
        deriva = -t * DERIVA
        for i, mini in enumerate(minis):
            fila, col = divmod(i, COLS)
            avance = _suave((t - 0.35 - (fila + col) * 0.06) / 0.35)
            if avance <= 0:
                continue
            s = 0.8 + 0.2 * avance
            mi = mini.resize((int(tw * s), int(th * s)), Image.LANCZOS) if s < 0.999 else mini
            if avance < 1:
                arr = np.asarray(mi).copy()
                arr[..., 3] = (arr[..., 3] * avance).astype(np.uint8)
                mi = Image.fromarray(arr, "RGBA")
            cx = ORILLA + col * (tw + HUECO) + tw / 2
            cy = y_muro + fila * (th + HUECO) + th / 2 + deriva
            img.alpha_composite(mi, (int(cx - mi.width / 2), int(cy - mi.height / 2)))
        # el muro se desvanece hacia abajo, para que no se corte seco en la orilla
        img.alpha_composite(desvanecido)
        esc.stdin.write(np.asarray(img.convert("RGB"), np.uint8).tobytes())
    esc.stdin.close()
    if esc.wait() != 0:
        sys.exit("No se pudo escribir %s" % destino)
    return n


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Tarjeta de cierre con muro de miniaturas (.mp4)")
    p.add_argument("titular")
    p.add_argument("fuentes", nargs="+", help="videos o imagenes propios")
    p.add_argument("--linea")
    p.add_argument("--dur", type=float, default=4.0)
    p.add_argument("--salida", required=True)
    a = p.parse_args()
    print(cierre_muro(a.salida, a.titular.replace("\\n", "\n"), a.fuentes, a.linea, a.dur), "cuadros")
