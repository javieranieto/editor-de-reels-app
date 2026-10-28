"""Lo comun de los motion graphics: marca, tiempos, palabras ancla, el lienzo VENTANA y exportar.

Nacio de proyectos/yt jnieto 0921 video1/motion_lib.py + motion_ventana.py (aprobados el 22-sep:
"ya me gusto, se quedo muy bien"). Ahi vivian dentro de un proyecto -fuera de git- y cada video
los volvia a escribir. Aqui quedan una sola vez; las piezas viven en piezas.py.

Reglas que vienen de lo aprobado y no se tocan sin preguntarle:
- .mov qtrle/argb 1080x1920: la animacion va DENTRO del archivo (los keyframes de pycapcut no se aplican).
- VENTANA: fondo de color con un HUECO transparente abajo donde el video se reduce; la grafica vive
  arriba. Corte SECO al entrar y salir (un fundido deja un fantasma del fondo encima de el).
- Tiempos leidos de las palabras del clip, nunca copiados a mano, y buscando DESPUES de un ancla.
- Todo texto se mide: si se sale de la franja, aborta (un texto mochado no da ningun error).
"""
import json
import os
import subprocess

from PIL import Image, ImageDraw, ImageFont

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FUENTES = os.path.join(RAIZ, "recursos", "fuentes")
W, H, FPS = 1080, 1920, 30
VENTANA = (40, 840, 1040, 1620)      # el hueco del video, el del clip 1 aprobado
MARGEN = 90


class Marca:
    """Colores y firma de una marca. Las piezas nunca escriben un color a mano: lo piden aqui."""

    def __init__(self, nombre, fondo, texto, acento, tenue, gris, hueco, firma):
        self.nombre, self.firma = nombre, firma
        self.FONDO, self.TEXTO, self.ACENTO = fondo, texto, acento
        self.TENUE, self.GRIS, self.HUECO = tenue, gris, hueco


# Las marcas salen de recursos/marcas/<id>.json (el mismo archivo que usan las escenas y los iconos):
# copia ejemplo.json como mi_marca.json, pon tus colores, y en el plan escribe "marca": "mi_marca".
# Sin "marca", sale "ejemplo". Ver recursos/marcas/LEEME.md.
MARCA_POR_DEFECTO = "ejemplo"
_activa = [None]


def _rgb(c):
    c = c.strip()
    if c.startswith("#"):
        c = c[1:]
        return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))
    nums = [float(x) for x in c[c.index("(") + 1:c.index(")")].split(",")[:3]]
    return tuple(int(x) for x in nums)


def _mezcla(a, b, f):
    return tuple(int(x + (y - x) * f) for x, y in zip(a, b))


class _Marcas(dict):
    """MARCAS["mi_marca"] lee recursos/marcas/mi_marca.json la primera vez que se pide."""

    def __missing__(self, id_):
        ruta = os.path.join(RAIZ, "recursos", "marcas", "%s.json" % id_)
        if not os.path.exists(ruta):
            raise SystemExit("No existe la marca %r: copia recursos/marcas/ejemplo.json como %s.json" % (id_, id_))
        d = json.load(open(ruta, encoding="utf-8"))
        c = d["colores"]
        fondo, texto = _rgb(c.get("marca", c["fondo1"])), _rgb(c["texto"])
        m = Marca(d.get("nombre", id_), fondo=fondo, texto=texto, acento=_rgb(c["acento"]),
                  tenue=_rgb(c.get("tenue", c["texto"])), gris=_mezcla(fondo, texto, 0.25),
                  hueco=_rgb(c.get("fondo2", c["fondo1"])), firma=d.get("firma", ""))
        m.usuario = d.get("usuario", "")
        self[id_] = m
        return m


MARCAS = _Marcas()


def usar(id_):
    """La marca de todo lo que se arme a partir de aqui (la fija el plan)."""
    _activa[0] = id_ or None


def marca_de(id_=None):
    """La marca pedida, o la del plan, o la de ejemplo."""
    return MARCAS[id_ or _activa[0] or MARCA_POR_DEFECTO]


def _f(archivo):
    return lambda s: ImageFont.truetype(os.path.join(FUENTES, archivo), s)


fb, fs, fm, fmono = _f("Poppins-Bold.ttf"), _f("Poppins-SemiBold.ttf"), _f("Poppins-Medium.ttf"), _f("RobotoMono.ttf")


# ------------------------------------------------------------------ tiempos
def ease(x):
    return 0.0 if x <= 0 else 1.0 if x >= 1 else 1 - (1 - x) ** 3


def rebote(x):
    """Pop con overshoot: se pasa un poco de su tamano y regresa."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    c = 1.70158 * 1.2
    x -= 1
    return 1 + (c + 1) * x ** 3 + c * x ** 2


def prog(t, a, dur=0.3):
    return ease((t - a) / dur)


def _limpia(s):
    return s.lower().strip("¿?¡!.,;:")


class Palabras:
    """Busca palabras del clip por texto. `despues_de` evita agarrar una aparicion anterior:
    «¿a quien» caso con «a quien le ibas a hablar» y la pregunta salio antes de tiempo."""

    def __init__(self, palabras):
        self.p = palabras
        self.ws = [_limpia(w["word"]) for w in palabras]

    @classmethod
    def de_archivo(cls, ruta):
        """Un plan.json o un clips/<clip>.json: cualquier JSON con la lista 'palabras'."""
        return cls(json.load(open(ruta, encoding="utf-8"))["palabras"])

    def _indice(self, texto, despues_de):
        q = [_limpia(x) for x in texto.split()]
        for i in range(len(self.ws) - len(q) + 1):
            if self.p[i]["start"] > despues_de and self.ws[i:i + len(q)] == q:
                return i
        raise SystemExit("motion: no encuentro %r despues de %.2f s" % (texto, despues_de))

    def __call__(self, texto, despues_de=-1.0):
        return self.p[self._indice(texto, despues_de)]["start"]

    def fin(self, texto, despues_de=-1.0):
        i = self._indice(texto, despues_de)
        return self.p[i + len(texto.split()) - 1]["end"]

    def ancla(self, a, despues_de=-1.0):
        """Un ancla del spec: "palabra" o {"en": "palabra", "despues_de": "otra"}. Los numeros
        pasan tal cual (segundos del clip), para cuando no hay palabra que buscar."""
        if isinstance(a, (int, float)):
            return float(a)
        if isinstance(a, dict):
            if "despues_de" in a:
                despues_de = self.ancla(a["despues_de"], despues_de)
            return self(a["en"], despues_de) + a.get("mas", 0.0)
        return self(a, despues_de)


def palabras_sinteticas(frase, inicio=0.5, dur=0.3, hueco=0.08):
    """Para las muestras del catalogo: una frase con tiempos regulares."""
    salida, t = [], inicio
    for p in frase.split():
        salida.append({"word": p, "start": round(t, 3), "end": round(t + dur, 3)})
        t += dur + hueco
    return salida


# ------------------------------------------------------------------ el lienzo VENTANA
class Ventana:
    """Un cuadro del estilo aprobado: fondo de la marca con el hueco del video abajo; se dibuja en
    la franja de arriba. Fuera de [t0, t1] el cuadro es transparente (corte seco)."""

    def __init__(self, t, t0, t1, etiqueta, marca, ventana=VENTANA):
        self.t, self.fuera, self.m, self.ven = t, (t < t0 or t > t1), marca, ventana
        self.tope = ventana[1] - 60
        self.im = Image.new("RGBA", (W, H), marca.FONDO + (255,))
        self.d = ImageDraw.Draw(self.im)
        if marca.firma:
            self.texto((MARGEN, 96), marca.firma, fmono(28), marca.TENUE)
        if etiqueta:
            self.texto((MARGEN, 152), etiqueta.upper(), fmono(36), marca.TENUE)

    def texto(self, xy, s, font, col, a=1.0):
        if a <= 0:
            return
        x1, y1 = self.d.textbbox(xy, s, font=font)[2:]
        assert x1 < W - 60 and y1 < self.tope, "se sale de la franja: %r (x=%d, y=%d de %d)" % (s, x1, y1, self.tope)
        self.d.text(xy, s, font=font, fill=col + (int(255 * min(1, a)),))

    def ancho(self, s, font):
        return self.d.textlength(s, font=font)

    def pegar(self, im, xy):
        assert xy[1] + im.height < self.tope + 40, "el adorno baja hasta y=%d" % (xy[1] + im.height)
        self.im.alpha_composite(im, (int(xy[0]), int(xy[1])))

    def cerrar(self):
        if self.fuera:
            return Image.new("RGBA", (W, H), (0, 0, 0, 0))
        hueco = Image.new("L", (W, H), 0)
        ImageDraw.Draw(hueco).rounded_rectangle(list(self.ven), 28, fill=255)
        al = self.im.getchannel("A")
        al.paste(0, (0, 0), hueco)
        self.im.putalpha(al)
        return self.im


def partir(a, texto, font, maximo):
    lineas = [[]]
    for p in texto.split():
        if lineas[-1] and a.ancho(" ".join(lineas[-1] + [p]), font) > maximo:
            lineas.append([])
        lineas[-1].append(p)
    return [" ".join(l) for l in lineas]


# ------------------------------------------------------------------ dibujos (Poppins no trae ✓ ✗ ≠)
def palomita(d, x, y, s, col, grosor=14):
    d.line([(x, y + s * 0.55), (x + s * 0.38, y + s * 0.9), (x + s, y + s * 0.1)], fill=col + (255,), width=grosor, joint="curve")


def tache(d, x, y, s, col, grosor=14):
    d.line([(x, y), (x + s, y + s)], fill=col + (255,), width=grosor)
    d.line([(x + s, y), (x, y + s)], fill=col + (255,), width=grosor)


def signo_distinto(d, x, y, s, col):
    g = max(8, s // 9)
    d.line([(x, y + s * 0.36), (x + s, y + s * 0.36)], fill=col + (255,), width=g)
    d.line([(x, y + s * 0.64), (x + s, y + s * 0.64)], fill=col + (255,), width=g)
    d.line([(x + s * 0.72, y + s * 0.08), (x + s * 0.28, y + s * 0.92)], fill=col + (255,), width=g)


def escalar(im, s):
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)


# ------------------------------------------------------------------ exportar
SALE = 0.32     # cola que se renderiza despues de t1 (heredada de motion_lib; en VENTANA ya es transparente)


def hoja(cuadro, claves, destino):
    """Cuadros clave sobre rosa (= donde se ve el video). Se ABRE antes de dar algo por bueno."""
    tw, th = 270, 480
    im = Image.new("RGBA", ((tw + 10) * len(claves), th), (40, 40, 40, 255))
    for k, c in enumerate(claves):
        fondo = Image.new("RGBA", (W, H), (200, 120, 120, 255))
        fondo.alpha_composite(cuadro(c))
        im.paste(fondo.resize((tw, th)), (k * (tw + 10), 0))
    im.convert("RGB").save(destino)
    return destino


def exportar(salida, nombre, cuadro, t0, t1, claves, ventana=VENTANA, solo_hoja=False):
    """Hoja + .mov + <nombre>.json (archivo, ini, fin en tiempo del clip, y el layout que necesita
    quien lo arma: el hueco y el tramo en que el video va reducido). Verifica el alfa al terminar."""
    os.makedirs(salida, exist_ok=True)
    hoja(cuadro, claves, os.path.join(salida, "hoja_%s.png" % nombre))
    if solo_hoja:
        return None
    ini, fin = t0, t1 + SALE
    n = int(round((fin - ini) * FPS)) + 1
    dest = os.path.join(salida, nombre + ".mov")
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", "%dx%d" % (W, H),
                           "-r", str(FPS), "-i", "-", "-c:v", "qtrle", "-pix_fmt", "argb", dest], stdin=subprocess.PIPE)
    for i in range(n):
        ff.stdin.write(cuadro(ini + i / FPS).tobytes())
    ff.stdin.close()
    ff.wait()

    def opaco(seg):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(seg), "-i", dest, "-frames:v", "1",
                              "-vf", "alphaextract,scale=108:192", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                             capture_output=True).stdout
        return sum(1 for x in raw if x > 128) / max(1, len(raw))

    medio, final = opaco((fin - ini) / 2), opaco(fin - ini - 0.02)
    assert 0.6 < medio < 0.95 and final < 0.01, \
        "%s: el alfa no quedo bien para una ventana (medio %.2f, final %.2f)" % (nombre, medio, final)
    meta = {"archivo": dest, "ini": round(ini, 3), "fin": round(ini + n / FPS, 3),
            "ventana": list(ventana), "t0": round(t0, 3), "t1": round(t1, 3)}
    json.dump(meta, open(os.path.join(salida, nombre + ".json"), "w"))
    print("%-22s %4d cuadros | clip %.2f-%.2f s | alfa ok" % (nombre, n, ini, ini + n / FPS))
    return meta
