"""Tarjetas que van DELANTE de la persona: la pista de encima del video.

A diferencia de pipeline/detras.py, estas no necesitan recorte: se ponen sobre
el video, en una zona que no tape la cara (el pecho, o junto a la cabeza).
Salen en .mov qtrle/argb como el resto del motion.

  lista_pasos   una tarjeta con los pasos que se palomean mientras los dices
  antes_despues una tarjetita junto a la cabeza: antes X, ahora Y

Los colores salen de la ficha de la marca (pipeline/motion/base.py, MARCAS), no
se escriben aqui. 
Estado (sube a aprobado cuando Javier lo ve sobre su video y dice que si):
  lista_pasos    aprobado 27-oct ("se ven bien")
  antes_despues  aprobado 27-oct ("se ven bien")
  grafica_vidrio aprobado 28-oct ("me gustaron todos")
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

if __package__ in (None, ""):   # corrido como comando: que encuentre el resto del editor
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.detras import FPS, H, W, _exportar, _suave
from pipeline.motion.base import marca_de

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUENTES = os.path.join(RAIZ, "recursos", "fuentes")


def _f(nombre, tam):
    return ImageFont.truetype(os.path.join(FUENTES, nombre), tam)


def _espaciar(txt):
    """Letras espaciadas para las etiquetas chicas (TE TOCA, ANTES)."""
    return " ".join(txt.upper())


def _resorte(t, dur=0.5):
    """0->1 con un pequeno rebote al llegar: para cosas que 'caen' en su lugar."""
    if t <= 0:
        return 0.0
    if t >= dur:
        return 1.0
    x = t / dur
    return 1 - np.exp(-6 * x) * np.cos(9 * x)


def _pegar(lienzo, img, x, y, escala=1.0, opacidad=1.0, giro=0.0):
    """Pega `img` (RGBA) centrada en (x, y) del lienzo, escalada, girada y con opacidad."""
    if opacidad <= 0:
        return
    if escala != 1.0:
        img = img.resize((max(1, int(img.width * escala)), max(1, int(img.height * escala))), Image.LANCZOS)
    if giro:
        img = img.rotate(giro, resample=Image.BICUBIC, expand=True)
    if opacidad < 1:
        a = np.asarray(img).copy()
        a[..., 3] = (a[..., 3] * opacidad).astype(np.uint8)
        img = Image.fromarray(a, "RGBA")
    lienzo.alpha_composite(img, (int(x - img.width / 2), int(y - img.height / 2)))


# --- lista de pasos -----------------------------------------------------------

def _tarjeta_lista(titulo, pasos, hechos, marca, ancho):
    m = marca
    ft, fc, fp = _f("Poppins-SemiBold.ttf", 28), _f("Poppins-SemiBold.ttf", 30), _f("Poppins-Medium.ttf", 40)
    renglon = 92
    alto = 150 + renglon * len(pasos) + 30
    img = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, ancho - 1, alto - 1), 36, fill=m.FONDO + (238,))
    d.rounded_rectangle((1, 1, ancho - 2, alto - 2), 36, outline=m.GRIS + (255,), width=2)
    d.text((44, 38), _espaciar(titulo), font=ft, fill=m.TENUE)
    cuenta = "%d de %d" % (hechos, len(pasos))
    d.text((ancho - 44 - fc.getlength(cuenta), 34), cuenta, font=fc, fill=m.ACENTO if hechos else m.TENUE)
    # barra de avance en segmentos
    seg_w = (ancho - 88 - 10 * (len(pasos) - 1)) / len(pasos)
    for i in range(len(pasos)):
        x0 = 44 + i * (seg_w + 10)
        d.rounded_rectangle((x0, 92, x0 + seg_w, 102), 5, fill=m.ACENTO if i < hechos else m.GRIS)
    for i, paso in enumerate(pasos):
        y = 140 + i * renglon
        listo = i < hechos
        cx, cy, r = 70, y + 30, 22
        if listo:
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=m.ACENTO)
            d.line([(cx - 10, cy), (cx - 3, cy + 8), (cx + 11, cy - 8)], fill=(255, 255, 255), width=5)
        else:
            d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=m.GRIS, width=4)
        d.text((cx + 46, y + 4), paso, font=fp, fill=m.TEXTO if listo else m.TENUE)
    return img


def lista_pasos(destino, pasos, titulo="Te toca", dur=5.0, y=1350, ancho=880, marca=None,
                entrada=0.5, salida=0.35):
    """Una tarjeta con los pasos; cada uno se palomea en su segundo.

    pasos : [(segundo, "texto")] en segundos del .mov. 3 a 5 pasos, cortos (caben ~22 letras).
    y     : centro vertical de la tarjeta (1350 = sobre el pecho en un plano medio).
    """
    m = marca_de(marca)
    pasos = sorted(pasos)
    fp = _f("Poppins-Medium.ttf", 40)
    for _, txt in pasos:
        if fp.getlength(txt) > ancho - 160:
            sys.exit("El paso «%s» no cabe en la tarjeta: acortalo" % txt)
    if not 2 <= len(pasos) <= 5:
        sys.exit("Una lista de pasos lleva de 2 a 5 pasos (trae %d)" % len(pasos))
    textos = [p[1] for p in pasos]
    cache = {}
    n = int(round(dur * FPS))

    def cuadros():
        for k in range(n):
            t = k / FPS
            hechos = sum(1 for s, _ in pasos if s <= t)
            if hechos not in cache:
                cache[hechos] = _tarjeta_lista(titulo, textos, hechos, m, ancho)
            llegada = _resorte(t, entrada)
            fuera = _suave((t - (dur - salida)) / salida) if t > dur - salida else 0.0
            # el ultimo paso palomeado da un "latido": la tarjeta crece 3% un instante
            latido = 0.0
            for s, _ in pasos:
                if 0 <= t - s < 0.25:
                    latido = np.sin((t - s) / 0.25 * np.pi) * 0.03
            lienzo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            _pegar(lienzo, cache[hechos], W / 2, y + (1 - llegada) * 60 + fuera * 40,
                   escala=(0.92 + 0.08 * llegada) + latido, opacidad=min(1.0, llegada * 1.4) * (1 - fuera),
                   giro=(1 - llegada) * 2.5)
            yield np.asarray(lienzo, np.uint8)

    return _exportar(cuadros(), destino)


# --- antes y despues ----------------------------------------------------------

def _tarjeta_ad(etiqueta, antes, despues, ver_despues, marca):
    m = marca
    fe = _f("Poppins-SemiBold.ttf", 19)
    # El AHORA es lo grande; si no cabe junto a la cara, la letra baja hasta 34 (se sigue
    # leyendo en el telefono). Mas chica ya no: ahi se aborta y se pide un texto mas corto.
    for tam in range(54, 33, -2):
        fa, fd = _f("Poppins-Medium.ttf", min(40, tam)), _f("Poppins-Bold.ttf", tam)
        if max(fe.getlength(_espaciar(etiqueta)), fa.getlength(antes) + 60, fd.getlength(despues)) + 64 <= 380:
            break
    ancho = int(max(fe.getlength(_espaciar(etiqueta)), fa.getlength(antes) + 60, fd.getlength(despues)) + 64)
    ancho = max(ancho, 300)
    alto = 250
    img = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, ancho - 1, alto - 1), 28, fill=(255, 255, 255, 250))
    d.text((32, 30), _espaciar(etiqueta), font=fe, fill=m.GRIS)
    # antes: gris, tachado
    d.text((32, 68), antes, font=fa, fill=(150, 156, 170))
    wa = fa.getlength(antes)
    d.line([(28, 98), (36 + wa, 92)], fill=m.ACENTO, width=5)
    if ver_despues:
        d.text((32, 136), despues, font=fd, fill=m.FONDO)
        d.rounded_rectangle((32, 216, 32 + min(fd.getlength(despues), ancho - 64), 222), 3, fill=m.ACENTO)
    return img


def antes_despues(destino, etiqueta, antes, despues, despues_en, dur=4.0, lado="derecha",
                  x=None, y=620, marca=None, entrada=0.5, salida=0.35):
    """Una tarjetita junto a la cabeza: la etiqueta, el ANTES tachado y, en su segundo, el AHORA.

    etiqueta   : de que se habla, corto ("Tiempo de respuesta").
    despues_en : segundo del .mov en que aparece el valor nuevo (con un pop).
    """
    m = marca_de(marca)
    vacia = _tarjeta_ad(etiqueta, antes, despues, False, m)
    llena = _tarjeta_ad(etiqueta, antes, despues, True, m)
    if x is None:
        # pegada a la orilla: en un plano medio junto a la cara quedan ~390 px libres
        x = W - llena.width / 2 - 28 if lado == "derecha" else llena.width / 2 + 28
    if llena.width > 380:
        sys.exit("La tarjeta mide %d px y taparia la cara: acorta la etiqueta o los valores" % llena.width)
    n = int(round(dur * FPS))

    def cuadros():
        for k in range(n):
            t = k / FPS
            llegada = _resorte(t, entrada)
            fuera = _suave((t - (dur - salida)) / salida) if t > dur - salida else 0.0
            pop = 0.0
            if 0 <= t - despues_en < 0.3:
                pop = np.sin((t - despues_en) / 0.3 * np.pi) * 0.06
            img = llena if t >= despues_en else vacia
            lienzo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            _pegar(lienzo, img, x, y - (1 - llegada) * 80, escala=(0.85 + 0.15 * llegada) + pop,
                   opacidad=min(1.0, llegada * 1.5) * (1 - fuera), giro=-3 + (1 - llegada) * 6)
            yield np.asarray(lienzo, np.uint8)

    return _exportar(cuadros(), destino)


# --- grafica de vidrio --------------------------------------------------------

def grafica_vidrio(destino, etiqueta, desde, hasta, sufijo="", dur=4.0, y=1440, marca=None,
                   formato="{:,.0f}"):
    """Una tarjeta ancha y translucida sobre el pecho: la etiqueta, un numero que sube de
    `desde` a `hasta` y una linea que crece con el.
    🔴 Cifras PROPIAS o del negocio demo, nunca de un cliente."""
    m = marca_de(marca)
    ancho, alto = 900, 380
    fe, fn = _f("Poppins-SemiBold.ttf", 28), _f("Poppins-Bold.ttf", 110)
    muestra = formato.format(max(abs(desde), abs(hasta))) + sufijo
    if fn.getlength(muestra) > ancho - 100:
        sys.exit("La cifra «%s» no cabe en la tarjeta" % muestra)
    n = int(round(dur * FPS))
    xs = np.linspace(0, 1, 60)
    curva = xs ** 2.2

    def cuadros():
        for k in range(n):
            t = k / FPS
            llegada = _resorte(t, 0.5)
            fuera = _suave((t - (dur - 0.35)) / 0.35) if t > dur - 0.35 else 0.0
            sube = _suave((t - 0.35) / max(0.5, dur - 1.2))
            img = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
            d = ImageDraw.Draw(img)
            d.rounded_rectangle((0, 0, ancho - 1, alto - 1), 40, fill=m.FONDO + (196,))
            d.rounded_rectangle((2, 2, ancho - 3, alto - 3), 40, outline=(255, 255, 255, 120), width=3)
            # el brillo del vidrio: una rayita en la orilla de arriba (encima de la etiqueta la tapaba)
            d.rounded_rectangle((60, 6, ancho - 60, 12), 3, fill=(255, 255, 255, 90))
            d.text((44, 34), _espaciar(etiqueta), font=fe, fill=m.TEXTO)
            valor = desde + (hasta - desde) * sube
            d.text((44, 80), formato.format(valor) + sufijo, font=fn, fill=m.TEXTO)
            # la linea que crece, abajo a la derecha
            gx0, gx1, gy0, gy1 = ancho * 0.50, ancho - 50, alto - 60, 120
            hastai = max(2, int(len(xs) * sube))
            pts = [(gx0 + (gx1 - gx0) * xs[i], gy0 - (gy0 - gy1) * curva[i] * sube) for i in range(hastai)]
            if len(pts) > 1:
                d.line(pts, fill=m.ACENTO, width=8, joint="curve")
                px, py = pts[-1]
                d.ellipse((px - 12, py - 12, px + 12, py + 12), fill=m.ACENTO)
            lienzo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            _pegar(lienzo, img, W / 2, y + (1 - llegada) * 60, escala=0.92 + 0.08 * llegada,
                   opacidad=min(1.0, llegada * 1.4) * (1 - fuera))
            yield np.asarray(lienzo, np.uint8)

    return _exportar(cuadros(), destino)
