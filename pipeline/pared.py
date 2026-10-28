"""Cosas en la PARED, detras de la persona (pista "fx detras", con el recorte encima).

  titulares   notas, citas y tarjetas que aparecen en la pared ("todos hablan de X")
  grafica     una linea que se dibuja detras de la cabeza y despega
  orbita      tarjetas de videos propios que giran alrededor del pecho (atras Y adelante)
  muro        un muro de miniaturas de videos propios que llena la pared desde la cabeza

Salen en .mov qtrle/argb del tamano del cuadro. La orbita saca DOS: lo de atras (va en
"fx detras") y lo de adelante (va en "fx tarjetas"), para que las tarjetas pasen por
detras del cuerpo y por delante.

🔴 Sin cifras inventadas: otros kits ponen vistas ("1.07M") en las tarjetas; aqui
solo van miniaturas y titulos reales. Una cifra de mentira en un video es mentirle a
quien lo ve. Y nunca material ni numeros de un cliente.

Estado: titulares, grafica, orbita y muro aprobados 28-oct ("me gustaron todos")
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

if __package__ in (None, ""):   # corrido como comando: que encuentre el resto del editor
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.cierre import _redondear, miniatura
from pipeline.detras import BODONI, FPS, H, W, _exportar, _suave
from pipeline.motion.base import marca_de
from pipeline.tarjetas import _resorte

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUENTES = os.path.join(RAIZ, "recursos", "fuentes")


def _f(nombre, tam):
    return ImageFont.truetype(nombre if os.path.isabs(nombre) else os.path.join(FUENTES, nombre), tam)


def _partir(texto, fuente, ancho):
    lineas, linea = [], ""
    for p in texto.split():
        prueba = (linea + " " + p).strip()
        if fuente.getlength(prueba) <= ancho or not linea:
            linea = prueba
        else:
            lineas.append(linea)
            linea = p
    if linea:
        lineas.append(linea)
    return lineas


def _pegar(lienzo, img, cx, cy, escala=1.0, opacidad=1.0, giro=0.0):
    if opacidad <= 0 or escala <= 0.01:
        return
    if escala != 1.0:
        img = img.resize((max(1, int(img.width * escala)), max(1, int(img.height * escala))), Image.LANCZOS)
    if giro:
        img = img.rotate(giro, resample=Image.BICUBIC, expand=True)
    if opacidad < 1:
        a = np.asarray(img).copy()
        a[..., 3] = (a[..., 3] * opacidad).astype(np.uint8)
        img = Image.fromarray(a, "RGBA")
    lienzo.alpha_composite(img, (int(cx - img.width / 2), int(cy - img.height / 2)))


def _sombra(img, radio=14, fuerza=90):
    """La pieza con una sombra suave debajo, para que se sienta pegada a la pared."""
    pad = radio * 2
    base = Image.new("RGBA", (img.width + pad * 2, img.height + pad * 2), (0, 0, 0, 0))
    a = np.zeros((base.height, base.width), np.uint8)
    a[pad + 8:pad + 8 + img.height, pad + 4:pad + 4 + img.width] = (np.asarray(img)[..., 3] > 0) * fuerza
    sombra = Image.fromarray(np.dstack([np.zeros_like(a)] * 3 + [a]), "RGBA").filter(ImageFilter.GaussianBlur(radio))
    sombra.alpha_composite(img, (pad, pad))
    return sombra


# --- muro de titulares --------------------------------------------------------

def _pieza(tipo, texto, m):
    """Una pieza de pared: nota de periodico, cita, publicacion, buscador o burbuja."""
    if tipo == "nota":
        fk, ft = _f("Poppins-SemiBold.ttf", 18), _f(BODONI.replace("BOD_CR", "BOD_B"), 46)
        ls = _partir(texto, ft, 380)
        img = Image.new("RGBA", (440, 90 + 54 * len(ls)), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rectangle((0, 0, img.width - 1, img.height - 1), fill=(246, 240, 226, 255))
        d.text((30, 26), "  ".join("NOTICIA"), font=fk, fill=m.ACENTO)
        for j, l in enumerate(ls):
            d.text((30, 58 + j * 54), l, font=ft, fill=(24, 24, 28))
    elif tipo == "cita":
        ft = _f("Poppins-Medium.ttf", 34)
        ls = _partir("“" + texto + "”", ft, 360)
        img = Image.new("RGBA", (420, 60 + 46 * len(ls)), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((0, 0, img.width - 1, img.height - 1), 18, fill=m.FONDO + (255,))
        for j, l in enumerate(ls):
            d.text((30, 30 + j * 46), l, font=ft, fill=m.TEXTO)
    elif tipo == "post":
        fn, ft = _f("Poppins-SemiBold.ttf", 24), _f("OpenSans-VF.ttf", 30)
        ls = _partir(texto, ft, 360)
        img = Image.new("RGBA", (430, 110 + 40 * len(ls)), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((0, 0, img.width - 1, img.height - 1), 20, fill=(255, 255, 255, 255))
        d.ellipse((24, 22, 70, 68), fill=(170, 182, 206))
        d.text((84, 32), "Alguien comento", font=fn, fill=(40, 44, 56))
        for j, l in enumerate(ls):
            d.text((24, 84 + j * 40), l, font=ft, fill=(30, 34, 44))
    elif tipo == "buscar":
        ft = _f("OpenSans-VF.ttf", 32)
        w = int(min(ft.getlength(texto) + 120, 520))
        img = Image.new("RGBA", (w, 84), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((0, 0, w - 1, 83), 42, fill=(255, 255, 255, 255))
        d.ellipse((26, 26, 52, 52), outline=(130, 136, 150), width=4)
        d.line([(48, 48), (58, 58)], fill=(130, 136, 150), width=4)
        d.text((76, 20), texto[:28], font=ft, fill=(30, 34, 44))
    else:  # burbuja
        ft = _f("OpenSans-VF.ttf", 32)
        ls = _partir(texto, ft, 340)
        img = Image.new("RGBA", (400, 44 + 42 * len(ls)), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((0, 0, img.width - 1, img.height - 1), 26, fill=(216, 240, 214, 255))
        for j, l in enumerate(ls):
            d.text((26, 20 + j * 42), l, font=ft, fill=(24, 28, 36))
    return _sombra(img)


def titulares(destino, textos, dur=4.0, marca=None, escalon=0.28):
    """Hasta 6 textos que aparecen en la pared, alrededor de la cabeza, uno tras otro."""
    m = marca_de(marca)
    if not 1 <= len(textos) <= 6:
        sys.exit("titulares lleva de 1 a 6 textos")
    tipos = ["nota", "post", "cita", "buscar", "burbuja", "nota"]
    # 🔑 lugares en la pared que de verdad se ven en un plano medio: la franja de ARRIBA de la
    # cabeza y las orillas de abajo de los hombros. A los lados de la cara no: la cara los tapa
    # (primera version, 27-oct). Los de las orillas van mas chicos.
    # arriba caben DOS lado a lado; una tercera en medio tapaba el texto de las otras dos
    lugares = [(270, 160, -4), (810, 180, 4), (950, 640, -4), (130, 650, 3), (140, 920, -2), (950, 940, 3)]
    tam = [1.0, 1.0, 0.62, 0.62, 0.62, 0.62]
    piezas = [_pieza(tipos[i], tx, m) for i, tx in enumerate(textos)]
    n = int(round(dur * FPS))

    def cuadros():
        for k in range(n):
            t = k / FPS
            fuera = _suave((t - (dur - 0.35)) / 0.35) if t > dur - 0.35 else 0
            lienzo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            for i, (pz, (x, y, g)) in enumerate(zip(piezas, lugares)):
                r = _resorte(t - i * escalon, 0.4)
                e = tam[i] * (0.6 + 0.4 * r)
                # que no se salga del cuadro: se corre hacia adentro lo que haga falta
                x = min(max(x, pz.width * e / 2 + 10), W - pz.width * e / 2 - 10)
                _pegar(lienzo, pz, x, y, escala=e, opacidad=min(1, r * 1.5) * (1 - fuera), giro=g)
            yield np.asarray(lienzo, np.uint8)

    return _exportar(cuadros(), destino)


# --- grafica que sube ---------------------------------------------------------

def grafica(destino, etiqueta="+300%", dur=4.0, despegue=0.6, dias="L M M J V S D", marca=None):
    """Lineas de guia y dias arriba; una linea blanca se dibuja de izquierda a derecha
    (pasa detras de la cabeza) y al llegar a `despegue` se vuelve acento y sube.
    🔴 `etiqueta` es una cifra PROPIA o del negocio demo, nunca de un cliente."""
    m = marca_de(marca)
    # en la franja de arriba de la cabeza: a la altura de la barbilla quedaba casi toda tapada
    x0, x1, ybase, ytop = 70, W - 70, 430, 120
    etiquetas = dias.split()
    fd, fe = _f("Poppins-SemiBold.ttf", 28), _f("Poppins-Bold.ttf", 86)
    # la forma: plana con ruido hasta el despegue, despues sube
    xs = np.linspace(0, 1, 160)
    ys = np.where(xs < despegue, 0.12 + 0.05 * np.sin(xs * 23) + 0.03 * np.sin(xs * 51),
                  0.12 + (np.clip(xs - despegue, 0, None) / (1 - despegue)) ** 1.6 * 0.85)
    n = int(round(dur * FPS))
    dibujo = 0.55 * dur

    def cuadros():
        for k in range(n):
            t = k / FPS
            fuera = _suave((t - (dur - 0.35)) / 0.35) if t > dur - 0.35 else 0
            lienzo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(lienzo)
            g = _suave(t / 0.4)
            for i, e in enumerate(etiquetas):
                x = x0 + (x1 - x0) * i / (len(etiquetas) - 1)
                d.line([(x, ytop), (x, ybase)], fill=(255, 255, 255, int(70 * g)), width=2)
                d.text((x - fd.getlength(e) / 2, ytop - 44), e, font=fd, fill=(255, 255, 255, int(170 * g)))
            avance = _suave((t - 0.3) / dibujo)
            hasta = max(2, int(len(xs) * avance))
            pts = [(x0 + (x1 - x0) * xs[i], ybase - (ybase - ytop) * ys[i]) for i in range(hasta)]
            for i in range(1, len(pts)):
                col = (255, 255, 255, 235) if xs[i] < despegue else m.ACENTO + (255,)
                d.line([pts[i - 1], pts[i]], fill=col, width=9 if xs[i] >= despegue else 6)
            for i in range(0, hasta, 26):
                d.ellipse((pts[i][0] - 7, pts[i][1] - 7, pts[i][0] + 7, pts[i][1] + 7), fill=(255, 255, 255, 235))
            if avance > 0:
                px, py = pts[-1]
                d.ellipse((px - 14, py - 14, px + 14, py + 14), fill=m.ACENTO + (255,))
            if avance >= 0.999:
                e = _resorte(t - 0.3 - dibujo, 0.35)
                tx = min(x1 - fe.getlength(etiqueta) / 2, W - 30 - fe.getlength(etiqueta)) - fe.getlength(etiqueta) / 2
                ty = max(10, ytop - 20)
                d.text((tx, ty + (1 - e) * 30), etiqueta, font=fe, fill=m.ACENTO + (int(255 * min(1, e)),))
            arr = np.asarray(lienzo).copy()
            # brillo alrededor de lo que es acento
            acento = (arr[..., 0] > 200) & (arr[..., 2] < 120) & (arr[..., 3] > 0)
            halo = (cv2.GaussianBlur(acento.astype(np.float32), (0, 0), 12) * 160).clip(0, 255).astype(np.uint8)
            solo_halo = arr[..., 3] < halo            # donde el brillo manda, su color es el acento
            arr[solo_halo, :3] = m.ACENTO
            arr[..., 3] = np.maximum(arr[..., 3], halo)
            arr[..., 3] = (arr[..., 3] * (1 - fuera)).astype(np.uint8)
            yield arr

    return _exportar(cuadros(), destino)


# --- tarjetas de videos propios -------------------------------------------------

def _tarjeta_video(fuente, titulo, ancho=200):
    alto = int(ancho * 16 / 9)
    mini = miniatura(fuente, ancho, alto, 0.4).convert("RGBA")
    if titulo:
        d = ImageDraw.Draw(mini)
        ft = _f("Poppins-SemiBold.ttf", 22)
        ls = _partir(titulo, ft, ancho - 30)[:2]
        y = alto - 24 - 30 * len(ls)
        d.rounded_rectangle((10, y - 8, ancho - 10, alto - 16), 10, fill=(255, 255, 255, 235))
        for j, l in enumerate(ls):
            d.text((20, y + j * 30), l, font=ft, fill=(20, 24, 32))
    return _sombra(_redondear(mini.convert("RGB"), 16), radio=10, fuerza=110)


def orbita(destino_atras, destino_frente, fuentes, titulos=None, dur=4.0, vueltas=0.6):
    """Seis tarjetas en un anillo inclinado alrededor del pecho. Escribe DOS .mov: las de
    atras (para "fx detras", el cuerpo las tapa) y las de adelante (para "fx tarjetas")."""
    if not fuentes:
        sys.exit("La orbita necesita videos propios")
    nt = 6
    tarjetas = [_tarjeta_video(fuentes[i % len(fuentes)], (titulos or [None] * nt)[i % len(titulos or [None])])
                for i in range(nt)]
    cx, cy, rx, ry = W / 2, H * 0.60, W * 0.47, H * 0.08
    n = int(round(dur * FPS))

    def ambos():
        for k in range(n):
            t = k / FPS
            entra = _suave(t / 0.5)
            fuera = _suave((t - (dur - 0.4)) / 0.4) if t > dur - 0.4 else 0
            atras = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            frente = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            orden = []
            for i in range(nt):
                ang = 2 * np.pi * (i / nt + vueltas * t / dur)
                x, y, z = cx + rx * np.cos(ang), cy + ry * np.sin(ang), np.sin(ang)
                orden.append((z, i, x, y))
            for z, i, x, y in sorted(orden):
                esc = (0.62 + 0.22 * (z + 1) / 2) * entra
                op = (0.55 + 0.45 * (z + 1) / 2) * (1 - fuera)
                _pegar(frente if z > 0 else atras, tarjetas[i], x, y, esc, op)
            yield np.asarray(atras, np.uint8), np.asarray(frente, np.uint8)

    cuadros = list(ambos())
    _exportar((c[0] for c in cuadros), destino_atras)
    return _exportar((c[1] for c in cuadros), destino_frente)


def muro(destino, fuentes, dur=4.0, origen=(540, 360)):
    """Miniaturas de videos propios que tapizan la pared, desde la cabeza hacia afuera."""
    if not fuentes:
        sys.exit("El muro necesita videos propios")
    tw, gap = 180, 12
    th = int(tw * 16 / 9)
    cols = W // (tw + gap) + 1
    filas = 4
    minis, celdas = [], []
    for r in range(filas):
        for col in range(cols):
            x = col * (tw + gap) + (tw / 2 if r % 2 else 0) - 30
            y = 20 + r * (th + gap) * 0.62
            celdas.append((x + tw / 2, y + th / 2))
    for i in range(len(celdas)):
        minis.append(_redondear(miniatura(fuentes[i % len(fuentes)], tw, th, 0.2 + 0.6 * ((i * 0.37) % 1)), 14))
    dist = [np.hypot(x - origen[0], y - origen[1]) for x, y in celdas]
    dmax = max(dist)
    n = int(round(dur * FPS))

    def cuadros():
        for k in range(n):
            t = k / FPS
            fuera = _suave((t - (dur - 0.35)) / 0.35) if t > dur - 0.35 else 0
            lienzo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            for (x, y), mi, dd in zip(celdas, minis, dist):
                r = _resorte(t - 0.55 * dd / dmax, 0.35)
                _pegar(lienzo, mi, x, y, escala=0.5 + 0.5 * r, opacidad=min(1, r * 1.4) * (1 - fuera))
            yield np.asarray(lienzo, np.uint8)

    return _exportar(cuadros(), destino)
