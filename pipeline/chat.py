"""Chat en pantalla: una ventana de chat de IA sobre el pecho, delante de la persona.

Para las demos ("le paso mis clips y le escribo esto"): una ventana de chat
generica entra arriba; un recuadro punteado pide los archivos, unas miniaturas
del propio video vuelan adentro y se vuelven adjuntos, el prompt se escribe letra
por letra con su cursor, se manda, y sale una respuesta corta.

Va ENCIMA del video, sobre el pecho (como pipeline/tarjetas.py), sin recorte.
🔑 Se probo primero arriba y detras de la persona, como el original, y NO sirve con
el encuadre de Javier: su cabeza esta en el tercio de arriba y tapaba justo el
recuadro del prompt, que es lo unico que hay que leer (27-oct). Sobre el pecho la
cara queda libre y el prompt se lee entero.

🔴 Chat GENERICO: sin el logo, el nombre ni los colores de ninguna app real.

Estado: aprobado 27-oct ("me gusta. Se ve bien").
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

if __package__ in (None, ""):   # corrido como comando: que encuentre el resto del editor
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.cierre import _redondear, miniatura
from pipeline.detras import FPS, H, W, _exportar, _suave
from pipeline.motion.base import marca_de

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUENTES = os.path.join(RAIZ, "recursos", "fuentes")
PW, PH, PX, PY = 960, 820, 60, 1010       # la ventana: ancho, alto y esquina de arriba (sobre el pecho)
CREMA = (250, 247, 240)
LETRAS_POR_SEG = 30                       # al escribir el prompt, si no se le da un tiempo


def _f(nombre, tam):
    return ImageFont.truetype(os.path.join(FUENTES, nombre), tam)


def _partir(texto, fuente, ancho):
    lineas, linea = [], ""
    for p in texto.split():
        prueba = (linea + " " + p).strip()
        if fuente.getlength(prueba) <= ancho:
            linea = prueba
        else:
            if linea:
                lineas.append(linea)
            linea = p
    if linea:
        lineas.append(linea)
    return lineas


def _punteado(d, caja, color, tramo=18, hueco=12, ancho=3):
    x0, y0, x1, y1 = caja
    for x in range(int(x0), int(x1), tramo + hueco):
        d.line([(x, y0), (min(x + tramo, x1), y0)], fill=color, width=ancho)
        d.line([(x, y1), (min(x + tramo, x1), y1)], fill=color, width=ancho)
    for y in range(int(y0), int(y1), tramo + hueco):
        d.line([(x0, y), (x0, min(y + tramo, y1))], fill=color, width=ancho)
        d.line([(x1, y), (x1, min(y + tramo, y1))], fill=color, width=ancho)


def chat_pantalla(destino, prompt, dur=6.0, app="Tu asistente", miniaturas_de=None, archivos_en=0.6,
                  escribe_en=1.6, enviar_en=None, respuesta=None, marca=None):
    """Escribe en `destino` (.mov qtrle/argb) la ventana de chat.

    prompt        : lo que se escribe (corto: cabe en 3-4 lineas).
    miniaturas_de : videos o imagenes de donde salen los 3 adjuntos (None = sin adjuntos).
    archivos_en / escribe_en / enviar_en : segundos del .mov. enviar_en None = al terminar de escribir.
    respuesta     : texto corto que aparece despues de enviar (None = sin respuesta).
    """
    m = marca_de(marca)
    fp = _f("OpenSans-VF.ttf", 34)
    caja = (PX + 40, PY + PH - 300, PX + PW - 40, PY + PH - 40)     # el compositor, abajo de la ventana
    lineas = _partir(prompt, fp, caja[2] - caja[0] - 130)
    if len(lineas) > 4:
        sys.exit("El prompt ocupa %d lineas y caben 4: acortalo" % len(lineas))
    if enviar_en is None:
        enviar_en = escribe_en + len(prompt) / LETRAS_POR_SEG + 0.3
    vel = len(prompt) / max(0.3, enviar_en - 0.3 - escribe_en)
    # los adjuntos: 3 miniaturas que salen de la cara de la persona y caen en el chat
    tw, th = 120, 214
    minis = []
    if miniaturas_de:
        for i in range(3):
            fuente = miniaturas_de[i % len(miniaturas_de)]
            minis.append(_redondear(miniatura(fuente, tw, th, 0.25 + 0.25 * i), 14))
    n = int(round(dur * FPS))
    fh, fr = _f("Poppins-SemiBold.ttf", 34), _f("OpenSans-VF.ttf", 32)

    def cuadros():
        for k in range(n):
            t = k / FPS
            entra = _suave(t / 0.5)
            sale = _suave((t - (dur - 0.35)) / 0.35) if t > dur - 0.35 else 0.0
            lienzo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            v = Image.new("RGBA", (PW, PH), (0, 0, 0, 0))
            d = ImageDraw.Draw(v)
            d.rounded_rectangle((0, 0, PW - 1, PH - 1), 40, fill=CREMA + (250,))
            # cabecera: un logo de puntos (generico) y el nombre
            for i in range(3):
                d.ellipse((40 + i * 20, 46, 54 + i * 20, 60), fill=m.ACENTO)
            d.text((120, 32), app, font=fh, fill=m.FONDO)
            d.line([(30, 100), (PW - 30, 100)], fill=(228, 222, 210), width=2)
            cx0, cy0, cx1, cy1 = (caja[0] - PX, caja[1] - PY, caja[2] - PX, caja[3] - PY)
            adjuntos = t >= archivos_en + 0.8 and minis
            if t < escribe_en and not adjuntos:
                _punteado(d, (cx0, cy0, cx1, cy1), m.TENUE)
                txt = "Suelta tus archivos aquí"
                d.text(((cx0 + cx1 - _f("Poppins-Medium.ttf", 32).getlength(txt)) / 2, (cy0 + cy1) / 2 - 20),
                       txt, font=_f("Poppins-Medium.ttf", 32), fill=m.TENUE)
            else:
                d.rounded_rectangle((cx0, cy0, cx1, cy1), 28, fill=(255, 255, 255, 255),
                                    outline=(222, 216, 204), width=2)
                y_txt = cy0 + 24
                if adjuntos:
                    for i, mi in enumerate(minis):
                        chico = mi.resize((60, 107))
                        v.alpha_composite(chico, (int(cx0 + 24 + i * 72), int(cy0 + 20)))
                    y_txt = cy0 + 140
                escrito = prompt[: max(0, int((t - escribe_en) * vel))] if t < enviar_en else ""
                if t >= escribe_en and t < enviar_en:
                    ls = _partir(escrito, fp, cx1 - cx0 - 130) or [""]
                    for j, l in enumerate(ls[-3:] if adjuntos else ls):
                        d.text((cx0 + 26, y_txt + j * 44), l, font=fp, fill=(30, 34, 44))
                    if int(t * 2.5) % 2 == 0:       # el cursor parpadea
                        ult = (ls[-3:] if adjuntos else ls)[-1]
                        xc = cx0 + 28 + fp.getlength(ult)
                        yl = y_txt + (len(ls[-3:] if adjuntos else ls) - 1) * 44
                        d.line([(xc, yl + 4), (xc, yl + 40)], fill=m.ACENTO, width=3)
                # boton de enviar
                enviado = t >= enviar_en
                d.ellipse((cx1 - 84, cy1 - 84, cx1 - 24, cy1 - 24), fill=m.ACENTO if not enviado else m.GRIS)
                d.polygon([(cx1 - 63, cy1 - 68), (cx1 - 63, cy1 - 40), (cx1 - 38, cy1 - 54)], fill=(255, 255, 255))
            # lo enviado sube como burbuja, y la respuesta aparece debajo
            if t >= enviar_en:
                sube = _suave((t - enviar_en) / 0.35)
                ls = _partir(prompt, fr, PW * 0.62)
                alto_b = 36 + 42 * len(ls)
                bx1 = PW - 40
                bx0 = bx1 - max(fr.getlength(l) for l in ls) - 56
                by0 = 130 + (1 - sube) * 260
                d.rounded_rectangle((bx0, by0, bx1, by0 + alto_b), 26, fill=m.FONDO)
                for j, l in enumerate(ls):
                    d.text((bx0 + 28, by0 + 18 + j * 42), l, font=fr, fill=m.TEXTO)
                if respuesta and t >= enviar_en + 0.6:
                    lr = _partir(respuesta, fr, PW * 0.70)
                    ry0 = by0 + alto_b + 28
                    letras = int((t - enviar_en - 0.6) * 45)
                    resto, mostradas = letras, []
                    for l in lr:
                        mostradas.append(l[: max(0, resto)])
                        resto -= len(l)
                    d.ellipse((40, ry0 + 6, 70, ry0 + 36), fill=m.ACENTO)
                    for j, l in enumerate(mostradas):
                        d.text((88, ry0 + j * 42), l, font=fr, fill=(40, 44, 56))
            # adjuntos en vuelo: de la cara hasta el compositor, en arco
            if minis and archivos_en <= t < archivos_en + 0.8:
                for i, mi in enumerate(minis):
                    u = _suave((t - archivos_en - i * 0.08) / 0.6)
                    if u <= 0:
                        continue
                    x = (W / 2 + (i - 1) * 160) * (1 - u) + (caja[0] + 54 + i * 72) * u
                    y = (H * 0.25) * (1 - u) + (caja[1] + 73) * u - np.sin(u * np.pi) * 160
                    s = 1 - 0.5 * u
                    chico = mi.resize((max(1, int(tw * s)), max(1, int(th * s))))
                    lienzo.alpha_composite(chico, (int(x - chico.width / 2), int(y - chico.height / 2)))
            # la ventana entra bajando y sale subiendo
            a = np.asarray(v).copy()
            a[..., 3] = (a[..., 3] * entra * (1 - sale)).astype(np.uint8)
            base = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            base.alpha_composite(Image.fromarray(a, "RGBA"), (PX, int(PY + (1 - entra) * 80 + sale * 40)))
            base.alpha_composite(lienzo)
            yield np.asarray(base, np.uint8)

    return _exportar(cuadros(), destino)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Chat de IA en pantalla, sobre el pecho (.mov con alfa)")
    p.add_argument("prompt")
    p.add_argument("--salida", required=True)
    p.add_argument("--dur", type=float, default=6.0)
    p.add_argument("--app", default="Tu asistente")
    p.add_argument("--miniaturas", nargs="*")
    p.add_argument("--respuesta")
    a = p.parse_args()
    print(chat_pantalla(a.salida, a.prompt, a.dur, a.app, a.miniaturas, respuesta=a.respuesta), "cuadros")
