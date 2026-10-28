"""Escenas que cambian lo que hay ALREDEDOR de la persona. Pantalla completa, como b-roll.

  marco        el video se encoge a una ventana de Reels y la cabeza se sale por arriba
  verde        el cuarto desaparece: la persona queda abajo, mas chica, frente a una imagen o la marca
  papel        el fondo se vuelve una hoja cuadriculada con garabatos y un numero grande
  escritorio   baja un escritorio arriba, la persona queda abajo, y caen tarjetas una por una
  contenedor   baja un panel arriba, la persona queda abajo, y caen cosas dentro de una caja

Todas salen de la grabacion ORIGINAL del tramo (necesitan a la persona y a su fondo) y en un
.mp4 opaco sin audio; en CapCut van encima como b-roll, dentro de UN corte.

Estado: marco, verde, papel, escritorio, contenedor y gis aprobados 28-oct ("me gustaron todos")
"""
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

if __package__ in (None, ""):   # corrido como comando: que encuentre el resto del editor
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.detras import _suave
from pipeline.motion.base import marca_de
from pipeline.recorte import _medidas, capas
from pipeline.tarjetas import _resorte
from pipeline.vertigo import cuarto_vacio

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUENTES = os.path.join(RAIZ, "recursos", "fuentes")
PAPEL = (246, 243, 236)


def _f(nombre, tam):
    return ImageFont.truetype(os.path.join(FUENTES, nombre), tam)


def _tramo(video, ini, fin):
    o, c, a = [], [], []
    for x, y, z in capas(video, ini, fin):
        o.append(x)
        c.append(y)
        a.append(z)
    if not o:
        sys.exit("No se pudo leer el tramo")
    return o, c, a


def _escribir(cuadros, destino, W, H, fps_txt):
    esc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", "%dx%d" % (W, H), "-r", fps_txt, "-i", "-", "-c:v", "libx264",
                            "-crf", "16", "-pix_fmt", "yuv420p", destino], stdin=subprocess.PIPE)
    n = 0
    for c in cuadros:
        esc.stdin.write(np.ascontiguousarray(c, np.uint8).tobytes())
        n += 1
    esc.stdin.close()
    if esc.wait() != 0 or n == 0:
        sys.exit("No se pudo escribir %s" % destino)
    return n


def _encima(fondo, color, alfa):
    a = alfa[..., None].astype(np.float32) / 255
    return fondo * (1 - a) + color.astype(np.float32) * a


def _cuadricula(W, H, paso=54, color=(222, 226, 232), base=PAPEL):
    img = Image.new("RGB", (W, H), base)
    d = ImageDraw.Draw(img)
    for x in range(0, W, paso):
        d.line([(x, 0), (x, H)], fill=color, width=2)
    for y in range(0, H, paso):
        d.line([(0, y), (W, y)], fill=color, width=2)
    return np.asarray(img, np.float32)


def _transformar(img, s, dx, dy, W, H, borde=0):
    M = np.float32([[s, 0, W / 2 * (1 - s) + dx], [0, s, H / 2 * (1 - s) + dy]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=borde)


# --- rompe el marco -----------------------------------------------------------

def marco(video, destino, ini=None, fin=None, usuario=None, marca=None):
    """El cuadro se encoge a una ventana de Reels sobre una copia oscura y borrosa; la
    ventana corta a la altura de la frente, y la cabeza se sale por encima del marco."""
    W, H, fps, fps_txt = _medidas(video)
    o, c, a = _tramo(video, ini, fin)
    usuario = usuario if usuario is not None else marca_de(marca).usuario   # el "usuario" de la marca
    fu = _f("Poppins-SemiBold.ttf", 30)
    S = 0.78                      # escala de la ventana
    corte_y = 0.27                # la ventana empieza a esta altura del cuadro original (la frente)

    def cuadros():
        for k in range(len(o)):
            t = k / fps
            p = _resorte(t, 0.55)
            s = 1 - (1 - S) * p
            fondo = cv2.GaussianBlur(o[k], (0, 0), 30).astype(np.float32) * (1 - 0.55 * p)
            dy = H * 0.06 * p
            vid = _transformar(o[k].astype(np.float32), s, 0, dy, W, H)
            per_c = _transformar(c[k].astype(np.float32), s, 0, dy, W, H)
            per_a = _transformar(a[k].astype(np.float32), s, 0, dy, W, H)
            # la ventana: de la frente para abajo, con esquinas redondas
            x0 = W / 2 - W * s / 2
            x1 = W / 2 + W * s / 2
            y_top = H / 2 * (1 - s) + dy + corte_y * H * s * p
            y1 = H / 2 * (1 - s) + dy + H * s
            mascara = Image.new("L", (W, H), 0)
            ImageDraw.Draw(mascara).rounded_rectangle((x0, y_top, x1, y1), int(40 * p), fill=255)
            mv = np.asarray(mascara, np.float32)[..., None] / 255
            out = fondo * (1 - mv) + vid * mv
            # la cabeza por encima del marco (solo lo que queda arriba de la ventana)
            arriba = (np.arange(H)[:, None] < y_top + 2).astype(np.float32)
            out = _encima(out, per_c, per_a * arriba)
            img = Image.fromarray(out.clip(0, 255).astype(np.uint8))
            if p > 0.6:
                d = ImageDraw.Draw(img)
                al = int(255 * min(1, (p - 0.6) / 0.3))
                if usuario:
                    d.text((x0 + 30, y1 - 70), usuario, font=fu, fill=(255, 255, 255))
                for i in range(3):   # iconos genericos del lado derecho
                    cy = y1 - 300 + i * 90
                    d.ellipse((x1 - 76, cy, x1 - 30, cy + 46), outline=(255, 255, 255), width=4)
            yield np.asarray(img)

    return _escribir(cuadros(), destino, W, H, fps_txt)


# --- pantalla verde -----------------------------------------------------------

def verde(video, destino, ini=None, fin=None, imagen=None, marca=None):
    """El cuarto se disuelve; la persona baja y se encoge al centro de abajo, delante de una
    imagen (una captura de una app, por ejemplo) o, sin imagen, del degradado de la marca."""
    m = marca_de(marca)
    W, H, fps, fps_txt = _medidas(video)
    o, c, a = _tramo(video, ini, fin)
    if imagen:
        im = Image.open(imagen).convert("RGB")
        im.thumbnail((int(W * 0.9), int(H * 0.55)))
        fondo = Image.new("RGB", (W, H), m.FONDO)
        caja = Image.new("RGB", (im.width + 24, im.height + 24), (255, 255, 255))
        caja.paste(im, (12, 12))
        fondo.paste(caja, ((W - caja.width) // 2, int(H * 0.08)))
        fondo = np.asarray(fondo, np.float32)
    else:
        g = np.linspace(0, 1, H)[:, None, None]
        claro = np.array(m.FONDO, np.float32) * 1.25
        fondo = (claro * (1 - g) + np.array(m.FONDO, np.float32) * 0.55 * g) * np.ones((1, W, 1))
    S = 0.62
    # lo que se disuelve es el cuarto VACIO: con el cuadro original se veia a la persona dos
    # veces en la transicion (la del cuarto que se iba y el recorte que se encogia)
    vacio = cuarto_vacio(o, a)[0].astype(np.float32)

    def cuadros():
        for k in range(len(o)):
            t = k / fps
            p = _suave(t / 0.7)
            s = 1 - (1 - S) * p
            dy = (H * (1 - s) / 2) * p                       # baja hasta apoyarse en el borde de abajo
            cuarto = vacio * (1 - p) + fondo * p
            pc = _transformar(c[k].astype(np.float32), s, 0, dy, W, H)
            pa = _transformar(a[k].astype(np.float32), s, 0, dy, W, H)
            yield _encima(cuarto, pc, pa).clip(0, 255)

    return _escribir(cuadros(), destino, W, H, fps_txt)


# --- papel y crayon -----------------------------------------------------------

def _garabatos(W, H, semilla, m):
    """Rayones de crayon que "hierven": se redibujan con otra semilla cada 3 cuadros."""
    rng = np.random.default_rng(semilla)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    azul, rosa = (52, 96, 210, 255), (236, 120, 170, 255)
    # un rayon grande de lado a lado arriba
    xs = np.linspace(60, W - 60, 9)
    pts = [(x + rng.normal(0, 6), 150 + 40 * np.sin(i * 1.3) + rng.normal(0, 6)) for i, x in enumerate(xs)]
    d.line(pts, fill=azul, width=14, joint="curve")
    for _ in range(3):   # crucecitas y rayitas
        x, y = rng.uniform(80, W - 80), rng.uniform(260, H * 0.5)
        d.line([(x - 22, y - 22), (x + 22, y + 22)], fill=rosa, width=9)
        d.line([(x - 22, y + 22), (x + 22, y - 22)], fill=rosa, width=9)
    return img


def papel(video, destino, texto, ini=None, fin=None, marca=None):
    """El fondo se cambia por papel cuadriculado con garabatos y un `texto` grande ("3X",
    "$0", "100%") en una tira amarilla rota; la persona sigue igual, encima."""
    m = marca_de(marca)
    W, H, fps, fps_txt = _medidas(video)
    o, c, a = _tramo(video, ini, fin)
    base = _cuadricula(W, H)
    fn = _f("Poppins-Bold.ttf", 240)
    if fn.getlength(texto) > W * 0.9:
        sys.exit("«%s» no cabe: usa una cifra corta" % texto)
    tira = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dt = ImageDraw.Draw(tira)
    y0 = int(H * 0.06)
    dt.polygon([(30, y0 + 30), (W - 40, y0), (W - 20, y0 + 300), (50, y0 + 330)], fill=(255, 214, 64, 255))
    dt.text(((W - fn.getlength(texto)) / 2, y0 + 20), texto, font=fn, fill=m.FONDO + (255,))

    def cuadros():
        for k in range(len(o)):
            t = k / fps
            p = _suave(t / 0.25)
            g = _garabatos(W, H, k // 3, m)
            hoja = Image.fromarray(base.astype(np.uint8)).convert("RGBA")
            hoja.alpha_composite(g)
            ar = np.asarray(tira).copy()
            ar[..., 3] = (ar[..., 3] * _suave((t - 0.15) / 0.3)).astype(np.uint8)
            hoja.alpha_composite(Image.fromarray(ar, "RGBA"))
            hoja = np.asarray(hoja.convert("RGB"), np.float32)
            # entra como una cortina de arriba abajo
            linea = (np.arange(H)[:, None, None] < H * p).astype(np.float32)
            fondo = o[k].astype(np.float32) * (1 - linea) + hoja * linea
            yield _encima(fondo, c[k], a[k]).clip(0, 255)

    return _escribir(cuadros(), destino, W, H, fps_txt)


# --- panel arriba, persona abajo (escritorio y contenedor) -------------------------

def _panel_arriba(o, k, fps, W, H, panel, t):
    """`panel` (RGB float) baja desde arriba y EMPUJA a la persona: el video baja pegado al
    borde de abajo del panel (si bajara antes, quedaba una franja negra arriba). Sin achicar:
    la cara se sigue viendo, se pierde el pecho. Llega SUAVE, sin rebote: en el rebote el video
    bajaba mas que el panel y quedaba un hueco negro arriba (27-oct)."""
    p = _suave(t / 0.45)
    alto = panel.shape[0]
    dy = alto * p
    vid = _transformar(o[k].astype(np.float32), 1.0, 0, dy, W, H, borde=0)
    y = int(dy - alto)
    out = vid.copy()
    y_ini, y_fin = max(0, y), min(H, y + alto)
    if y_fin > y_ini:
        out[y_ini:y_fin] = panel[y_ini - y:y_fin - y]
        # sombra corta bajo el panel
        sombra = np.linspace(0.55, 1, 30)[:, None, None]
        s0, s1 = y_fin, min(H, y_fin + 30)
        out[s0:s1] *= sombra[: s1 - s0]
    return out, p


def escritorio(video, destino, tarjetas, ini=None, fin=None, marca=None):
    """Un escritorio de papel cuadriculado baja arriba; cada tarjeta cae en su segundo,
    llega grande y girada, rebota y se queda. tarjetas: [(segundo, "texto")] del tramo."""
    m = marca_de(marca)
    W, H, fps, fps_txt = _medidas(video)
    o, c, a = _tramo(video, ini, fin)
    alto = int(H * 0.42)
    mesa = _cuadricula(W, alto)
    ft = _f("Poppins-Bold.ttf", 46)
    posiciones = [(W * 0.30, alto * 0.30, -6), (W * 0.70, alto * 0.36, 5), (W * 0.34, alto * 0.70, 4),
                  (W * 0.68, alto * 0.74, -5)]
    if len(tarjetas) > len(posiciones):
        sys.exit("El escritorio lleva hasta %d tarjetas" % len(posiciones))
    hojas = []
    for _, txt in tarjetas:
        w = int(min(ft.getlength(txt) + 80, W * 0.44))
        if ft.getlength(txt) > W * 0.44 - 80:
            sys.exit("La tarjeta «%s» no cabe: acortala" % txt)
        img = Image.new("RGBA", (w, 150), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((0, 0, w - 1, 149), 22, fill=(255, 255, 255, 255), outline=(220, 224, 230, 255), width=2)
        d.rectangle((0, 0, 14, 149), fill=m.ACENTO + (255,))
        d.text((40, 44), txt, font=ft, fill=m.FONDO + (255,))
        hojas.append(img)

    def cuadros():
        for k in range(len(o)):
            t = k / fps
            panel = Image.fromarray(mesa.astype(np.uint8)).convert("RGBA")
            for (s_t, _), img, (x, y, giro) in zip(tarjetas, hojas, posiciones):
                r = _resorte(t - s_t, 0.45)
                if r <= 0:
                    continue
                esc = 1.6 - 0.6 * r
                g = giro * (1 + (1 - r) * 3)
                im = img.resize((int(img.width * esc), int(img.height * esc))).rotate(g, expand=True, resample=Image.BICUBIC)
                panel.alpha_composite(im, (int(x - im.width / 2), int(y - im.height / 2)))
            out, _ = _panel_arriba(o, k, fps, W, H, np.asarray(panel.convert("RGB"), np.float32), t)
            yield out.clip(0, 255)

    return _escribir(cuadros(), destino, W, H, fps_txt)


def contenedor(video, destino, cosas, ini=None, fin=None, marca=None):
    """Un panel baja arriba con una caja negra abierta; cada cosa cae dentro en su segundo.
    cosas: [(segundo, "texto")] del tramo (correos, archivos, clientes...)."""
    m = marca_de(marca)
    W, H, fps, fps_txt = _medidas(video)
    o, c, a = _tramo(video, ini, fin)
    alto = int(H * 0.42)
    base = _cuadricula(W, alto)
    fc = _f("Poppins-SemiBold.ttf", 36)
    caja = (W * 0.22, alto * 0.42, W * 0.78, alto * 0.94)

    def cuadros():
        for k in range(len(o)):
            t = k / fps
            panel = Image.fromarray(base.astype(np.uint8)).convert("RGBA")
            d = ImageDraw.Draw(panel)
            dentro = sum(1 for s, _ in cosas if t >= s + 0.45)
            for i, (s_t, txt) in enumerate(cosas):
                u = (t - s_t) / 0.45
                if u <= 0:
                    continue
                w = fc.getlength(txt) + 50
                x = W / 2 + ((i % 3) - 1) * 140
                y = -60 + (caja[1] + 40 - (-60)) * min(1.0, u * u)
                if u >= 1:
                    y = caja[1] + 40 + (i // 3) * 6
                d.rounded_rectangle((x - w / 2, y - 30, x + w / 2, y + 30), 30, fill=m.ACENTO if u < 1 else m.GRIS)
                d.text((x - fc.getlength(txt) / 2, y - 23), txt, font=fc, fill=(255, 255, 255))
            # la caja va DELANTE de lo que ya cayo: tapa la mitad de abajo
            d.rounded_rectangle((caja[0], caja[1] + 40, caja[2], caja[3]), 26, fill=(26, 28, 34))
            d.text((caja[0] + 30, caja[1] + 70), "%d" % dentro, font=_f("Poppins-Bold.ttf", 70), fill=m.ACENTO)
            out, _ = _panel_arriba(o, k, fps, W, H, np.asarray(panel.convert("RGB"), np.float32), t)
            yield out.clip(0, 255)

    return _escribir(cuadros(), destino, W, H, fps_txt)


# --- contorno de gis ----------------------------------------------------------

def _dibujito(d, tipo, cx, cy, tam, rng, color, ancho):
    """Un dibujito hecho a mano (tiembla con rng): estrella, corazon, corona o flecha."""
    def j(x, y):
        return (x + rng.normal(0, 2.5), y + rng.normal(0, 2.5))
    if tipo == "estrella":
        pts = []
        for i in range(11):
            r = tam if i % 2 == 0 else tam * 0.45
            a = -np.pi / 2 + i * np.pi / 5
            pts.append(j(cx + r * np.cos(a), cy + r * np.sin(a)))
        d.line(pts, fill=color, width=ancho, joint="curve")
    elif tipo == "corazon":
        tt = np.linspace(0, 2 * np.pi, 40)
        pts = [j(cx + tam * 0.06 * 16 * np.sin(x) ** 3,
                 cy - tam * 0.06 * (13 * np.cos(x) - 5 * np.cos(2 * x) - 2 * np.cos(3 * x) - np.cos(4 * x)))
               for x in tt]
        d.line(pts, fill=color, width=ancho, joint="curve")
    elif tipo == "corona":
        b = cy + tam * 0.4
        pts = [(cx - tam, b), (cx - tam, cy - tam * 0.4), (cx - tam * 0.5, cy + tam * 0.05), (cx, cy - tam * 0.6),
               (cx + tam * 0.5, cy + tam * 0.05), (cx + tam, cy - tam * 0.4), (cx + tam, b), (cx - tam, b)]
        d.line([j(*p) for p in pts], fill=color, width=ancho, joint="curve")
    else:  # flecha que apunta a la persona
        d.line([j(cx + tam, cy - tam), j(cx - tam * 0.6, cy + tam * 0.6)], fill=color, width=ancho)
        d.line([j(cx - tam * 0.6, cy + tam * 0.6), j(cx - tam * 0.6, cy - tam * 0.1)], fill=color, width=ancho)
        d.line([j(cx - tam * 0.6, cy + tam * 0.6), j(cx + tam * 0.1, cy + tam * 0.6)], fill=color, width=ancho)


def gis(video, destino, dibujo="estrella", ini=None, fin=None, marca=None):
    """El video tal cual, con una linea de gis blanca alrededor de la silueta (unos pixeles
    por fuera) y un dibujito junto a la cabeza. Todo "hierve": se redibuja cada 3 cuadros."""
    if dibujo not in ("estrella", "corazon", "corona", "flecha"):
        sys.exit("dibujo: estrella, corazon, corona o flecha")
    W, H, fps, fps_txt = _medidas(video)
    o, c, a = _tramo(video, ini, fin)

    def cuadros():
        for k in range(len(o)):
            t = k / fps
            rng = np.random.default_rng(k // 3)
            m = (a[k] > 128).astype(np.uint8)
            m = cv2.dilate(m, np.ones((15, 15), np.uint8))          # unos pixeles por fuera del cuerpo
            cont, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            img = Image.fromarray(o[k])
            d = ImageDraw.Draw(img)
            aparece = _suave(t / 0.4)
            if cont:
                cnt = max(cont, key=cv2.contourArea)[:, 0, :]
                paso = max(1, len(cnt) // 140)
                pts = cnt[::paso].astype(np.float32)
                # sin la orilla del cuadro: la silueta toca abajo y los lados, y ahi no va linea
                visibles = (pts[:, 1] < H - 12) & (pts[:, 0] > 8) & (pts[:, 0] < W - 8)
                tramo = []
                for p, v in zip(pts, visibles):
                    if v:
                        tramo.append((p[0] + rng.normal(0, 2.2), p[1] + rng.normal(0, 2.2)))
                    elif len(tramo) > 1:
                        d.line(tramo, fill=(255, 255, 255), width=7, joint="curve")
                        tramo = []
                    else:
                        tramo = []
                hasta = int(len(tramo) * aparece)
                if hasta > 1:
                    d.line(tramo[:hasta], fill=(255, 255, 255), width=7, joint="curve")
                # el dibujito: arriba a la derecha de la cabeza
                ys, xs = np.nonzero(m[: H // 2])
                if len(xs) and t > 0.25:
                    top = ys.min()
                    x_cab = xs[ys < top + 60].max() if (ys < top + 60).any() else xs.max()
                    tam = 85 * _resorte(t - 0.25, 0.35)
                    _dibujito(d, dibujo, min(W - 90, x_cab + 110), max(90, top + 40), tam, rng, (255, 255, 255), 7)
            yield np.asarray(img)

    return _escribir(cuadros(), destino, W, H, fps_txt)
