"""Biblioteca de motion graphics del editor. Ver pipeline/motion/LEEME.md.

    from pipeline import motion
    meta = motion.renderizar(spec, palabras, salida)            # .mov + hoja + json
    segs = motion.encoger_en_ventana(segmentos, meta, cara_x)   # el video se reduce al hueco
"""
import os

from .base import MARCAS, marca_de, VENTANA, W, H, Palabras, exportar, palabras_sinteticas
from .catalogo import CATALOGO
from .piezas import PIEZAS


def construir(spec, palabras, marca=None):
    """-> (cuadro, t0, t1, claves, eventos). `palabras` es la lista del clip o un Palabras."""
    if spec["pieza"] not in PIEZAS:
        raise SystemExit("motion: no existe la pieza %r. Hay: %s" % (spec["pieza"], ", ".join(PIEZAS)))
    w = palabras if isinstance(palabras, Palabras) else Palabras(palabras)
    return PIEZAS[spec["pieza"]](spec, w, marca_de(spec.get("marca") or marca))


def renderizar(spec, palabras, salida, marca=None, solo_hoja=False):
    cuadro, t0, t1, claves, eventos = construir(spec, palabras, marca)
    nombre = spec.get("nombre", spec["pieza"])
    meta = exportar(salida, nombre, cuadro, t0, t1, claves, solo_hoja=solo_hoja)
    if meta:
        meta["eventos"] = [round(e, 3) for e in eventos]
        meta["pieza"] = spec["pieza"]
    return meta or {"hoja": os.path.join(salida, "hoja_%s.png" % nombre), "t0": t0, "t1": t1}


def encoger_en_ventana(segmentos, meta, cara_x=0.5):
    """Parte los segmentos en t0 y t1 de la animacion y, dentro de ese tramo, reduce el video al
    hueco del .mov (escala y desplazamiento calculados del hueco, no a ojo). El hueco es mas alto
    que 16:9, asi que el video se recorta de los lados y se centra en la cara: `cara_x` es la
    fraccion horizontal donde esta la cara (un numero, o una funcion del segmento).
    Corte seco: el video cambia de tamano en el MISMO fotograma en que entra el fondo.
    Portado de proyectos/yt jnieto 0921 video1/armar_ventana.py (aprobado 22-sep)."""
    ven, A, B = meta["ventana"], meta["t0"], meta["t1"]
    escala = max((ven[2] - ven[0]) / W, (ven[3] - ven[1]) / (W * 9 / 16))
    desp_y = -(((ven[1] + ven[3]) / 2) - H / 2) / (H / 2)
    segs, cur = [], 0.0
    for s in segmentos:
        dur = s["fin"] - s["ini"]
        trozos = [(cur, cur + dur)]
        for corte in (A, B):
            nuevos = []
            for a, b in trozos:
                nuevos += [(a, corte), (corte, b)] if a < corte < b else [(a, b)]
            trozos = nuevos
        for a, b in trozos:
            t = dict(s, ini=round(s["ini"] + (a - cur), 3), fin=round(s["ini"] + (b - cur), 3))
            if A <= a + 0.01 and b <= B + 0.01:
                cara = cara_x(s) if callable(cara_x) else cara_x
                t["zoom"] = {"punch": round(escala, 4), "x": round(-2 * escala * (cara - 0.5), 4), "y": round(desp_y, 4)}
            segs.append(t)
        cur += dur
    return segs


def quitar_bajo_la_ventana(broll, frases, meta):
    """Nada encima de la animacion: ni b-roll ni frase clave en su tramo."""
    broll = [b for b in broll if not (b["ini"] < meta["fin"] and meta["ini"] < b["fin"])]
    frases = [f for f in frases if not (f["ini"] < meta["t1"] and meta["t0"] < f["fin"])]
    return broll, frases
