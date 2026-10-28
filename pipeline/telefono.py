"""Un telefono que entra junto a la persona, con una conversacion adentro.

Para la parte de mensajes de las fugas ("te escribio y nadie contesto"): un
celular generico con una pantalla de chat donde los mensajes aparecen uno por
uno, en los segundos que se le digan. Entra de lado con un rebote, un poco
inclinado, flota mientras esta y sale por donde entro.

Va en la pista de EN MEDIO (como pipeline/detras.py): el video abajo, el
telefono, y el recorte de la persona encima, para que las manos le pasen por
delante. Tambien sirve encima de todo si no hay recorte.

🔴 Es un telefono y un chat GENERICOS: sin el logo, el nombre ni el verde exacto
de ninguna app: no se imita el producto de una empresa real en un anuncio.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

if __package__ in (None, ""):   # corrido como comando: que encuentre el resto del editor
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.detras import FPS, H, W, _exportar, _suave

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUENTES = os.path.join(RAIZ, "recursos", "fuentes")

# Medidas del telefono (a escala de un cuadro 1080x1920)
TW, TH = 430, 880          # cuerpo
RADIO = 64
MARCO = 14                 # grosor del marco metalico
COLORES = {
    "marco": (44, 48, 56), "filo": (120, 126, 138), "pantalla": (236, 229, 221),
    "barra": (38, 52, 74), "barra_txt": (240, 244, 250),
    "ellos": (255, 255, 255), "yo": (216, 240, 214), "txt": (24, 28, 36), "hora": (120, 128, 140),
    "visto": (52, 152, 230), "no_visto": (150, 156, 166),
}


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


def _pantalla(contacto, mensajes, visibles, visto):
    """Dibuja la pantalla con los primeros `visibles` mensajes. RGBA del tamano del cuerpo."""
    img = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # cuerpo y marco
    d.rounded_rectangle((0, 0, TW - 1, TH - 1), RADIO, fill=COLORES["marco"])
    d.rounded_rectangle((3, 3, TW - 4, TH - 4), RADIO - 3, outline=COLORES["filo"], width=2)
    x0, y0, x1, y1 = MARCO, MARCO, TW - MARCO, TH - MARCO
    pantalla = Image.new("RGBA", (x1 - x0, y1 - y0), COLORES["pantalla"] + (255,))
    p = ImageDraw.Draw(pantalla)
    pw = x1 - x0
    # barra de arriba con el contacto
    p.rectangle((0, 0, pw, 118), fill=COLORES["barra"])
    p.ellipse((24, 54, 74, 104), fill=(150, 170, 200))
    p.text((88, 58), contacto, font=_f("Poppins-SemiBold.ttf", 26), fill=COLORES["barra_txt"])
    p.text((88, 88), "en línea", font=_f("Poppins-Medium.ttf", 18), fill=(190, 200, 215))
    # isla de la camara
    p.rounded_rectangle((pw / 2 - 58, 14, pw / 2 + 58, 46), 16, fill=(10, 10, 12))
    # mensajes
    f = _f("OpenSans-VF.ttf", 25)
    fh = _f("OpenSans-VF.ttf", 16)
    y = 140
    for i, (quien, texto, hora) in enumerate(mensajes[:visibles]):
        lineas = _partir(texto, f, pw * 0.62)
        alto = 18 + 32 * len(lineas) + 24
        ancho = max(f.getlength(l) for l in lineas) + 40
        ancho = max(ancho, 150)
        if quien == "yo":
            bx1 = pw - 18
            bx0 = bx1 - ancho
            color = COLORES["yo"]
        else:
            bx0 = 18
            bx1 = bx0 + ancho
            color = COLORES["ellos"]
        p.rounded_rectangle((bx0, y, bx1, y + alto), 18, fill=color)
        for j, l in enumerate(lineas):
            p.text((bx0 + 20, y + 12 + 32 * j), l, font=f, fill=COLORES["txt"])
        # la hora va a la izquierda de las palomitas (en "yo") para no encimarse
        p.text((bx1 - 96 if quien == "yo" else bx1 - 58, y + alto - 26), hora, font=fh, fill=COLORES["hora"])
        if quien == "yo":
            col = COLORES["visto"] if visto and i == visibles - 1 else COLORES["no_visto"]
            cx, cy = bx1 - 22, y + alto - 16
            for dx in (0, 8):   # las dos palomitas
                p.line([(cx - 14 + dx, cy - 2), (cx - 9 + dx, cy + 3), (cx + dx, cy - 7)], fill=col, width=3)
        y += alto + 14
        if y > TH - 80:
            sys.exit("Demasiados mensajes para la pantalla: deja 3 o 4, cortos")
    # esquinas redondas de la pantalla
    mascara = Image.new("L", pantalla.size, 0)
    ImageDraw.Draw(mascara).rounded_rectangle((0, 0, pw - 1, y1 - y0 - 1), RADIO - MARCO, fill=255)
    img.paste(pantalla, (x0, y0), mascara)
    return img


def telefono(destino, mensajes, contacto="Cliente", visto_en=None, dur=5.0, lado="derecha",
             x=None, y=560, giro=-5.0, tam=0.85, entrada=0.45, salida=0.35):
    """Escribe en `destino` (.mov qtrle/argb) el telefono con la conversacion.

    mensajes : [(segundo, "ellos"|"yo", "texto", "hora")] en segundos del .mov.
    visto_en : segundo en que las palomitas del ultimo mensaje "yo" se ponen azules (None = nunca).
    lado     : de donde entra y donde se queda ("derecha" o "izquierda").
    tam      : escala del telefono (0.85 = cabe junto a la cabeza sin taparla en un plano medio).
    """
    if lado not in ("derecha", "izquierda"):
        sys.exit("lado tiene que ser derecha o izquierda")
    mensajes = sorted(mensajes)
    tw, th = int(TW * tam), int(TH * tam)
    if x is None:
        x = W - tw - 70 if lado == "derecha" else 70
    sombra_base = Image.new("RGBA", (TW + 120, TH + 120), (0, 0, 0, 0))
    ImageDraw.Draw(sombra_base).rounded_rectangle((60, 80, TW + 60, TH + 80), RADIO, fill=(0, 0, 0, 120))
    sombra_base = sombra_base.resize((int(sombra_base.width * tam), int(sombra_base.height * tam)))
    sombra_base = sombra_base.filter(ImageFilter.GaussianBlur(26))
    cache = {}
    n = int(round(dur * FPS))
    afuera = (W + 60) if lado == "derecha" else -(tw + 200)

    def cuadros():
        for k in range(n):
            t = k / FPS
            visibles = sum(1 for m in mensajes if m[0] <= t)
            visto = visto_en is not None and t >= visto_en
            clave = (visibles, visto)
            if clave not in cache:
                cache[clave] = _pantalla(contacto, [m[1:] for m in mensajes], visibles, visto).resize((tw, th), Image.LANCZOS)
            cuerpo = cache[clave]
            # entrada con rebote: llega un poco de mas y regresa
            e = (t / entrada) if t < entrada else 1.0
            rebote = _suave(e) + np.sin(min(e, 1.0) * np.pi) * 0.06
            s = _suave((t - (dur - salida)) / salida) if t > dur - salida else 0.0
            px = afuera + (x - afuera) * rebote + (afuera - x) * s
            py = y + np.sin(t * 2.2) * 6                     # flota
            ang = giro * (1 + (1 - _suave(e)) * 1.5)         # llega mas inclinado y se acomoda
            lienzo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            sombra = sombra_base.rotate(ang, resample=Image.BICUBIC, expand=True)
            tel = cuerpo.rotate(ang, resample=Image.BICUBIC, expand=True)
            lienzo.alpha_composite(sombra, (int(px - 60 * tam - (sombra.width - sombra_base.width) / 2),
                                            int(py - 60 * tam - (sombra.height - sombra_base.height) / 2)))
            lienzo.alpha_composite(tel, (int(px - (tel.width - tw) / 2), int(py - (tel.height - th) / 2)))
            yield np.asarray(lienzo, np.uint8)

    return _exportar(cuadros(), destino)


if __name__ == "__main__":
    import argparse
    import json
    p = argparse.ArgumentParser(description="Telefono con conversacion (.mov con alfa para CapCut)")
    p.add_argument("spec", help='json: {"mensajes": [[seg, "ellos"|"yo", "texto", "hora"]], "visto_en": s, "dur": s}')
    p.add_argument("--salida", required=True)
    a = p.parse_args()
    s = json.load(open(a.spec, encoding="utf-8"))
    n = telefono(a.salida, [tuple(m) for m in s["mensajes"]], contacto=s.get("contacto", "Cliente"),
                 visto_en=s.get("visto_en"), dur=s.get("dur", 5.0), lado=s.get("lado", "derecha"))
    print("%s: %d cuadros (%.1f s)" % (a.salida, n, n / FPS))
