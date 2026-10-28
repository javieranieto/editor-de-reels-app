"""Las piezas de motion: cada una recibe un SPEC (texto + palabras ancla) y devuelve sus cuadros.

Un spec es un JSON:
    {"pieza": "lista", "nombre": "v_preguntas", "etiqueta": "Las 4 preguntas",
     "anclas": {"n4": {"en": "cuatro", "despues_de": 7}, "u1": {"en": "la uno", "despues_de": "@n4"}},
     "items": [{"texto": "...", "en": "Uno"}, ...], "fin": {"en": "Una cosa", "despues_de": "@u1", "mas": 0.25}}

Un ancla es una palabra del clip ("Uno"), un dict {"en", "despues_de", "mas"}, un nombre ya
resuelto ("@n4") o segundos del clip (7.2). Las `anclas` con nombre se resuelven en orden, asi
que una puede buscar despues de la anterior. Cada pieza documenta sus campos en su funcion.

ESTADO de cada pieza en CATALOGO: "aprobada" = salio de un video que el aprobo; "nueva" = hecha
con su estilo pero que todavia no ha visto. Al proponer motion, se ofrecen las dos, diciendo cual es cual.
Una pieza nueva sube a "aprobada" solo cuando el la ve en un video y dice que si.
"""
import random

from PIL import Image, ImageDraw

from .base import (MARGEN, W, Ventana, ease, escalar, fb, fm, fmono, fs, palomita, partir, prog,
                   rebote, signo_distinto, tache)


class Anclas:
    def __init__(self, w, spec):
        self.w, self.nombres = w, {}
        for k, v in spec.get("anclas", {}).items():
            self.nombres[k] = self(v)

    def __call__(self, a, despues_de=-1.0):
        if isinstance(a, str) and a.startswith("@"):
            return self.nombres[a[1:]]
        if isinstance(a, dict):
            base = despues_de
            if "despues_de" in a:
                base = self(a["despues_de"])
            if isinstance(a["en"], str) and a["en"].startswith("@"):
                t = self.nombres[a["en"][1:]]
            else:
                t = self.w(a["en"], base)
            return t + a.get("mas", 0.0)
        return self.w.ancla(a, despues_de)


def _en_orden(pieza, tiempos):
    """Si el 3 entra antes que el 2, el ancla agarro una aparicion anterior ("hay TRES cosas…
    uno, dos, TRES"). No da ningun error por si solo: se ve en la hoja, si alguien la abre."""
    for k in range(1, len(tiempos)):
        if tiempos[k] <= tiempos[k - 1]:
            raise SystemExit("%s: el elemento %d entra en %.2f s, antes que el %d (%.2f s). Probablemente el "
                             "ancla agarro una aparicion anterior: ponle 'despues_de'." % (pieza, k + 1, tiempos[k], k, tiempos[k - 1]))


def _claves(spec, A, auto):
    if "claves" in spec:
        return [A(c) for c in spec["claves"]]
    return auto


# ---------------------------------------------------------------- lista (aprobada: reel 2)
def lista(spec, w, m):
    """Items numerados que entran uno por palabra, el numero con pop y el texto escribiendose.
    items[{texto, en}] · resaltar {item, palabra, en}: una palabra del item cambia al acento ·
    enfocar [{items, en}]: despues de contarlos, se quedan encendidos esos y los demas se apagan ·
    distinto {items: [a, b], en}: corchete con ≠ entre dos items · fin."""
    A = Anclas(w, spec)
    TN = [A(it["en"]) for it in spec["items"]]
    n = len(TN)
    _en_orden("lista", TN)
    res = spec.get("resaltar")
    T_RES = A(res["en"]) if res else None
    enf = [(set(e["items"]), A(e["en"])) for e in spec.get("enfocar", [])]
    foco_final = set().union(*[s for s, _ in enf]) if enf else set()
    dis = spec.get("distinto")
    T_DIS = A(dis["en"]) if dis else None
    t0, t1 = TN[0] - 0.3, A(spec["fin"])
    P = [it["texto"] for it in spec["items"]]
    f = fs(42)
    ANCHO = W - 90 - 110 - 140
    a0 = Ventana(t0 + 1, t0, t1, "x", m)
    ys = [228]
    for k in range(n - 1):
        ys.append(ys[-1] + len(partir(a0, P[k], f, ANCHO)) * int(f.size * 1.22) + 26)

    def cuadro(t):
        a = Ventana(t, t0, t1, spec.get("etiqueta", ""), m)
        if a.fuera:
            return a.cerrar()
        en_foco = [s for s, te in enf if t >= te]
        for k in range(n):
            if t < TN[k] - 0.05:
                continue
            if not en_foco:
                activo = k == max(j for j in range(n) if t >= TN[j] - 0.05)
            else:
                activo = k in set().union(*en_foco)
            alfa = 0.35 if (en_foco and k not in foco_final) else 1.0
            r = rebote((t - TN[k] + 0.05) / 0.4)
            esc = 0.4 + 0.6 * r
            num = Image.new("RGBA", (110, 110), (0, 0, 0, 0))
            ImageDraw.Draw(num).text((0, 0), str(k + 1), font=fb(70), fill=(m.ACENTO if activo else m.TENUE) + (int(255 * alfa),))
            num = num.resize((max(1, int(110 * esc)),) * 2, Image.LANCZOS)
            a.pegar(num, (90 + (110 - num.width) / 2, ys[k] - 8 + (110 - num.height) / 2))
            vis = int(len(P[k]) * prog(t, TN[k] + 0.08, 0.55))
            y = ys[k]
            for l in partir(a, P[k][:vis], f, ANCHO):
                x = 200
                for p in l.split():
                    col = m.ACENTO if (res and p == res["palabra"] and k == res["item"] and t >= T_RES) else (m.TEXTO if activo else m.TENUE)
                    a.texto((x, y), p, f, col, alfa)
                    x += a.ancho(p + " ", f)
                y += int(f.size * 1.22)
        if dis and t >= T_DIS - 0.05:
            i, j = dis["items"]
            al = prog(t, T_DIS - 0.05, 0.3)
            x = W - 150
            a.d.line([(x, ys[i] + 26), (x + 26, ys[i] + 26), (x + 26, ys[j] + 70), (x, ys[j] + 70)], fill=m.ACENTO + (int(255 * al),), width=6)
            s = int(90 * (0.5 + 0.5 * rebote((t - T_DIS + 0.05) / 0.4)))
            capa = Image.new("RGBA", (110, 110), (0, 0, 0, 0))
            signo_distinto(ImageDraw.Draw(capa), (110 - s) / 2, (110 - s) / 2, s, m.ACENTO)
            a.pegar(capa, (x - 120, (ys[i] + ys[j] + 70) / 2 - 55))
        return a.cerrar()

    auto = [x + 0.6 for x in TN] + [t1 - 0.2]
    return cuadro, t0, t1, _claves(spec, A, auto), TN


# ---------------------------------------------------------------- comparativa (aprobada: reel 3)
def comparativa(spec, w, m):
    """Dos (o tres) filas: subtitulo tenue + palabra grande, y en su palabra cae ✓ o ✗ con la
    respuesta. inicio · filas[{sub, grande, respuesta, bien, entra (s desde inicio), en}] · fin."""
    A = Anclas(w, spec)
    t0, t1 = A(spec["inicio"]), A(spec["fin"])
    filas = [(f["sub"], f["grande"], f["respuesta"], t0 + f.get("entra", 0.3 + 0.4 * k), A(f["en"]), f.get("bien", k == 0), 210 + 280 * k)
             for k, f in enumerate(spec["filas"])]

    def cuadro(t):
        a = Ventana(t, t0, t1, spec.get("etiqueta", ""), m)
        if a.fuera:
            return a.cerrar()
        for sub, grande, resp, t_in, t_marca, bien, y in filas:
            al = prog(t, t_in, 0.3)
            dx = int(-50 * (1 - al))
            a.texto((90 + dx, y), sub, fm(44), m.TENUE, al)
            a.texto((90 + dx, y + 58), grande, fb(96), m.TEXTO, al)
            if t >= t_marca - 0.05:
                r = rebote((t - t_marca + 0.05) / 0.4)
                mk = Image.new("RGBA", (86, 86), (0, 0, 0, 0))
                (palomita if bien else tache)(ImageDraw.Draw(mk), 8, 8, 68, m.ACENTO if bien else m.TENUE, 12)
                mk = mk.resize((max(1, int(86 * (0.4 + 0.6 * r))),) * 2, Image.LANCZOS)
                a.pegar(mk, (90 + (86 - mk.width) / 2, y + 168 + (86 - mk.height) / 2))
                a.texto((190, y + 180), resp, fs(48), m.ACENTO if bien else m.TEXTO, prog(t, t_marca, 0.3))
        return a.cerrar()

    marcas = [f[4] for f in filas]
    auto = [t0 + 0.5] + [x + 0.5 for x in marcas] + [t1 - 0.2]
    return cuadro, t0, t1, _claves(spec, A, auto), marcas


# ---------------------------------------------------------------- titular (aprobada: reel 4)
def titular(spec, w, m):
    """Una pregunta o frase en lineas que entran en su palabra; la primera puede llevar un SELLO
    (una palabra en acento que cae desde el doble de tamano). Opcional, arriba, una tarjeta de
    anuncio que entra deslizando. anuncio {titulo, etiqueta, boton, en} · lineas[{texto, en}] ·
    sello {texto, en} (va pegado a la primera linea) · inicio · fin."""
    A = Anclas(w, spec)
    t0, t1 = A(spec["inicio"]), A(spec["fin"])
    an = spec.get("anuncio")
    T_AN = A(an["en"]) if an else None
    lineas = [(l["texto"], A(l["en"])) for l in spec["lineas"]]
    se = spec.get("sello")
    T_SE = A(se["en"]) if se else None
    y0 = 486 if an else 240

    def cuadro(t):
        a = Ventana(t, t0, t1, spec.get("etiqueta", ""), m)
        if a.fuera:
            return a.cerrar()
        if an:
            al = prog(t, T_AN - 0.1, 0.35)
            x0 = 90 + int(-300 * (1 - al))
            ya = 210
            if al > 0:
                d = a.d
                AL = int(255 * al)
                d.rounded_rectangle([x0, ya, x0 + 900, ya + 240], 24, fill=m.HUECO + (AL,), outline=m.TENUE + (AL,), width=3)
                a.texto((x0 + 30, ya + 22), an["titulo"], fs(44), m.TEXTO, al)
                a.texto((x0 + 30, ya + 78), an.get("etiqueta", "PATROCINADO"), fmono(26), m.TENUE, al)
                d.rounded_rectangle([x0 + 30, ya + 124, x0 + 30 + 640, ya + 142], 9, fill=m.GRIS + (AL,))
                d.rounded_rectangle([x0 + 30, ya + 182, x0 + 330, ya + 226], 22, fill=m.ACENTO + (AL,))
                a.texto((x0 + 54, ya + 188), an.get("boton", "Enviar mensaje"), fs(32), m.TEXTO, al)
        f = fb(80)
        for k, (txt, te) in enumerate(lineas):
            if k == 0:
                a.texto((90, y0), txt, f, m.TEXTO, prog(t, te, 0.25))
                if se and t >= T_SE - 0.05:
                    r = rebote((t - T_SE + 0.05) / 0.4)
                    s = 2.0 - 1.0 * min(1.0, r) if r < 1 else 1.0
                    g = Image.new("RGBA", (220, 120), (0, 0, 0, 0))
                    ImageDraw.Draw(g).text((0, 0), se["texto"], font=f, fill=m.ACENTO + (255,))
                    g = g.resize((max(1, int(220 * s)), max(1, int(120 * s))), Image.LANCZOS)
                    a.pegar(g, (90 + a.ancho(txt + " ", f) - (g.width - 220) / 2, y0 - (g.height - 120) / 2))
            else:
                al = prog(t, te, 0.3)
                a.texto((90, y0 + 96 + 86 * (k - 1) + int(24 * (1 - al))), txt, fb(72), m.TEXTO, al)
        return a.cerrar()

    eventos = ([T_SE] if se else []) + [te for _, te in lineas[1:]]
    auto = ([T_AN + 0.5] if an else []) + [lineas[0][1] + 0.35] + [x + 0.5 for x in eventos] + [t1 - 0.2]
    return cuadro, t0, t1, _claves(spec, A, auto), eventos


# ---------------------------------------------------------------- burbujas (aprobada: reel 5)
def burbujas(spec, w, m):
    """Una rejilla de N burbujas de mensaje con su conteo grande; en cada ancla se van N, y al
    cierre las que quedan se pintan del acento. total (max 20) · aparece · semilla · unidad
    ("mensajes") · titulo [antes, despues] + titulo_cambia · etiqueta2 {texto, en} · cambios
    [{a, en}] · cierre {lineas[2], en} · inicio · fin."""
    A = Anclas(w, spec)
    total = spec.get("total", 20)
    assert total <= 20, "burbujas: caben 20 (2 filas de 10) sin tocar el cierre"
    t0, t1 = A(spec["inicio"]), A(spec["fin"])
    T_20 = A(spec["aparece"])
    e2 = spec.get("etiqueta2")
    T_E2 = A(e2["en"]) if e2 else None
    tit = spec.get("titulo", ["Al inicio", "Afinando"])
    T_TIT = A(spec["titulo_cambia"]) if "titulo_cambia" in spec else None
    cambios = [(c["a"], A(c["en"])) for c in spec["cambios"]]
    T_CIE = A(spec["cierre"]["en"])
    random.seed(spec.get("semilla", 7))
    orden = list(range(total))
    random.shuffle(orden)
    fuera, quedan, pos = {}, total, 0
    for a_, tq in cambios:
        for i in orden[pos:pos + quedan - a_]:
            fuera[i] = tq
        pos += quedan - a_
        quedan = a_
    COLS, BW, BH, GAP = 10, 82, 60, 16
    GX, GY = 90, 400

    def burbuja(col):
        b = Image.new("RGBA", (BW, BH + 12), (0, 0, 0, 0))
        d = ImageDraw.Draw(b)
        d.rounded_rectangle([0, 0, BW - 1, BH - 1], 16, fill=col + (255,))
        d.polygon([(16, BH - 3), (16, BH + 10), (36, BH - 3)], fill=col + (255,))
        for k, an in enumerate((0.7, 0.45)):
            d.rounded_rectangle([12, 14 + k * 18, 12 + int((BW - 24) * an), 24 + k * 18], 5, fill=m.FONDO + (150,))
        return b

    def cuadro(t):
        et = e2["texto"] if (e2 and t >= T_E2 - 0.1) else spec.get("etiqueta", "")
        a = Ventana(t, t0, t1, et, m)
        if a.fuera:
            return a.cerrar()
        n = total
        for q, tq in cambios:
            if t >= tq:
                n = q
        a.texto((90, 226), tit[1] if (T_TIT is not None and t >= T_TIT - 0.05) else tit[0], fm(52), m.TENUE, prog(t, t0 + 0.2, 0.3))
        if t >= T_20 - 0.05:
            a.texto((90, 286), "%d %s" % (n, spec.get("unidad", "mensajes")), fb(84), m.TEXTO)
        nar = prog(t, T_CIE, 0.4)
        for i in range(total):
            ti = T_20 + 0.03 * i
            if t < ti:
                continue
            s = rebote((t - ti) / 0.3)
            if i in fuera and t >= fuera[i]:
                s *= 1 - ease((t - fuera[i]) / 0.3)
                if s <= 0.02:
                    continue
            col = m.GRIS if i in fuera else tuple(int(m.GRIS[c] + (m.ACENTO[c] - m.GRIS[c]) * nar) for c in range(3))
            b = escalar(burbuja(col), s)
            cx = GX + (i % COLS) * (BW + GAP) + BW / 2
            cy = GY + (i // COLS) * (BH + GAP + 12) + BH / 2
            a.pegar(b, (cx - b.width / 2, cy - b.height / 2))
        al = prog(t, T_CIE + 0.2, 0.3)
        l1, l2 = spec["cierre"]["lineas"]
        a.texto((90, 590), l1, fs(62), m.ACENTO, al)
        a.texto((90, 662), l2, fs(62), m.TEXTO, al)
        return a.cerrar()

    eventos = [tq for _, tq in cambios]
    auto = [T_20 + 0.8] + [x + 0.4 for x in eventos] + [T_CIE + 0.9, t1 - 0.2]
    return cuadro, t0, t1, _claves(spec, A, auto), eventos


# ---------------------------------------------------------------- controles (aprobada: reel 6)
def controles(spec, w, m):
    """Filas de controles de una interfaz que se mueven solos, cada uno en su palabra.
    filas[{nombre, en, tipo}] con tipo: "desplegable" {opciones} · "rango" {desde [lo, hi],
    hasta [lo, hi], escala [a, b], formato "{lo}-{hi}", una_perilla} · "colores". inicio · fin."""
    A = Anclas(w, spec)
    t0, t1 = A(spec["inicio"]), A(spec["fin"])
    filas = [(f, A(f["en"])) for f in spec["filas"]]
    assert len(filas) <= 4, "controles: caben 4 filas en la franja"
    colores = [m.ACENTO, m.GRIS, m.TENUE]

    def cuadro(t):
        a = Ventana(t, t0, t1, spec.get("etiqueta", ""), m)
        if a.fuera:
            return a.cerrar()
        d = a.d
        for k, (fila, tk) in enumerate(filas):
            y = 212 + k * 138
            al = prog(t, tk - 0.35, 0.3)
            if al <= 0:
                continue
            AL = int(255 * al)
            x = 90 + int(-50 * (1 - al))
            a.texto((x, y), fila["nombre"], fs(44), m.TEXTO, al)
            yc = y + 62
            x0, x1 = x, W - 90
            mv = prog(t, tk, 0.8)
            tipo = fila["tipo"]
            if tipo == "desplegable":
                ops = fila["opciones"]
                i = min(len(ops) - 1, int((t - tk) / 0.28)) if t >= tk else 0
                d.rounded_rectangle([x0, yc, x1, yc + 64], 16, fill=m.HUECO + (AL,), outline=(m.ACENTO if 0 < t - tk < 1.2 else m.TENUE) + (AL,), width=3)
                a.texto((x0 + 22, yc + 12), ops[i], fm(38), m.TEXTO, al)
                d.polygon([(x1 - 58, yc + 24), (x1 - 26, yc + 24), (x1 - 42, yc + 44)], fill=m.TENUE + (AL,))
            elif tipo == "rango":
                (lo0, hi0), (lo1, hi1) = fila["desde"], fila["hasta"]
                lo, hi = lo0 + (lo1 - lo0) * mv, hi0 + (hi1 - hi0) * mv
                et = fila.get("formato", "{lo}-{hi}").format(lo=round(lo), hi=round(hi))
                ra, rb = fila["escala"]
                px = lambda v: x0 + (x1 - x0 - 190) * (v - ra) / (rb - ra)
                d.rounded_rectangle([x0, yc + 26, x1 - 190, yc + 36], 5, fill=m.HUECO + (AL,))
                d.rounded_rectangle([px(lo), yc + 26, px(hi), yc + 36], 5, fill=m.ACENTO + (AL,))
                for v in ((hi,) if fila.get("una_perilla") else (lo, hi)):
                    d.ellipse([px(v) - 17, yc + 14, px(v) + 17, yc + 48], fill=m.TEXTO + (AL,))
                a.texto((x1 - 170, yc + 6), et, fs(40), m.TEXTO, al)
            elif tipo == "colores":
                vuelta = int((t - tk) / 0.22) if t >= tk and t - tk < 0.9 else (4 if t >= tk else 0)
                for j in range(3):
                    d.rounded_rectangle([x0 + j * 200, yc, x0 + j * 200 + 170, yc + 64], 14, fill=colores[(j + vuelta) % 3] + (AL,))
            else:
                raise SystemExit("controles: tipo desconocido %r" % tipo)
        return a.cerrar()

    eventos = [tk for _, tk in filas]
    auto = [x + 0.6 for x in eventos] + [t1 - 0.2]
    return cuadro, t0, t1, _claves(spec, A, auto), eventos


# ================================================================ NUEVAS (su estilo, sin verlas el)
def sello(spec, w, m):
    """Un veredicto: contexto en lineas que entran en su palabra y, en el momento clave, una
    pastilla en acento que CAE girada desde el doble de tamano y se asienta con rebote.
    (Del glosario: «stamp».) contexto[{texto, en}] · sello {texto, en, giro (-6)} · inicio · fin."""
    A = Anclas(w, spec)
    t0, t1 = A(spec["inicio"]), A(spec["fin"])
    ctx = [(c["texto"], A(c["en"])) for c in spec.get("contexto", [])]
    se = spec["sello"]
    T_SE = A(se["en"])
    giro = se.get("giro", -6)
    f = fb(84)
    tmp = Ventana(t0 + 1, t0, t1, "", m)
    tw = int(tmp.ancho(se["texto"], f))
    pw, ph = tw + 120, 150
    pastilla = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pastilla)
    pd.rounded_rectangle([0, 0, pw - 1, ph - 1], ph // 2, fill=m.ACENTO + (255,))
    pd.text((60, 16), se["texto"], font=f, fill=m.TEXTO + (255,))
    pastilla = pastilla.rotate(giro, resample=Image.BICUBIC, expand=True)
    ys = 240 + 96 * len(ctx) + 40

    def cuadro(t):
        a = Ventana(t, t0, t1, spec.get("etiqueta", ""), m)
        if a.fuera:
            return a.cerrar()
        for k, (txt, te) in enumerate(ctx):
            al = prog(t, te, 0.3)
            col = m.TENUE if t >= T_SE - 0.05 else m.TEXTO       # el contexto se apaga cuando cae el veredicto
            a.texto((MARGEN, 240 + 96 * k + int(24 * (1 - al))), txt, fb(72), col, al)
        if t >= T_SE - 0.05:
            r = rebote((t - T_SE + 0.05) / 0.35)
            s = 2.2 - 1.2 * min(1.0, r) if r < 1 else 1.0
            g = escalar(pastilla, s)
            cx, cy = W / 2, ys + pastilla.height / 2
            a.pegar(g, (cx - g.width / 2, min(cy - g.height / 2, a.tope + 40 - g.height - 1)))
        return a.cerrar()

    auto = [te + 0.4 for _, te in ctx] + [T_SE + 0.08, T_SE + 0.6, t1 - 0.2]
    return cuadro, t0, t1, _claves(spec, A, auto), [T_SE]


def contador(spec, w, m):
    """Un numero grande que SUBE (o baja) de `desde` a `hasta` entre dos anclas, con su titulo
    arriba y una barra que se llena; al llegar, el numero pasa al acento. (Del glosario:
    «counter».) titulo · desde · hasta · empieza · termina · formato ("{n}", "${n:,}", "{n}%") ·
    pie {texto, en} · inicio · fin."""
    A = Anclas(w, spec)
    t0, t1 = A(spec["inicio"]), A(spec["fin"])
    T_A, T_B = A(spec["empieza"]), A(spec["termina"])
    assert T_B > T_A, "contador: termina antes de empezar"
    a0, b0 = spec["desde"], spec["hasta"]
    fmt = spec.get("formato", "{n}")
    pie = spec.get("pie")
    T_PIE = A(pie["en"]) if pie else None

    def cuadro(t):
        a = Ventana(t, t0, t1, spec.get("etiqueta", ""), m)
        if a.fuera:
            return a.cerrar()
        a.texto((MARGEN, 236), spec.get("titulo", ""), fm(52), m.TENUE, prog(t, t0 + 0.1, 0.3))
        x = ease((t - T_A) / (T_B - T_A))
        n = int(round(a0 + (b0 - a0) * x))
        llego = t >= T_B
        r = rebote((t - T_B) / 0.35) if llego else 0
        txt = fmt.format(n=n)
        f = fb(170)
        if llego and r < 1:
            g = Image.new("RGBA", (W, 230), (0, 0, 0, 0))
            ImageDraw.Draw(g).text((0, 0), txt, font=f, fill=m.ACENTO + (255,))
            g = escalar(g, 1.0 + 0.12 * (1 - r))
            a.pegar(g, (MARGEN, 300 - (g.height - 230) / 2))
        else:
            a.texto((MARGEN, 300), txt, f, m.ACENTO if llego else m.TEXTO)
        by, bw = 560, W - 2 * MARGEN
        a.d.rounded_rectangle([MARGEN, by, MARGEN + bw, by + 18], 9, fill=m.HUECO + (255,))
        if x > 0:
            a.d.rounded_rectangle([MARGEN, by, MARGEN + max(18, int(bw * x)), by + 18], 9, fill=m.ACENTO + (255,))
        if pie and t >= T_PIE - 0.05:
            a.texto((MARGEN, 620), pie["texto"], fs(54), m.TEXTO, prog(t, T_PIE, 0.3))
        return a.cerrar()

    auto = [T_A + 0.1, (T_A + T_B) / 2, T_B + 0.4] + ([T_PIE + 0.5] if pie else []) + [t1 - 0.2]
    return cuadro, t0, t1, _claves(spec, A, auto), [T_B]


def etapas(spec, w, m):
    """Una fila de pastillas de etapa: la actual en acento, las anteriores en tenue con ✓, las que
    faltan con solo el borde; debajo, grande, de que trata la actual. (Del glosario: «stepper».)
    etapas[{corto, detalle, en}] (max 4) · inicio · fin."""
    A = Anclas(w, spec)
    t0, t1 = A(spec["inicio"]), A(spec["fin"])
    et = [(e["corto"], e.get("detalle", ""), A(e["en"])) for e in spec["etapas"]]
    assert 2 <= len(et) <= 4, "etapas: entre 2 y 4"
    _en_orden("etapas", [te for _, _, te in et])
    n = len(et)
    GAP = 22
    pw = (W - 2 * MARGEN - GAP * (n - 1)) // n
    PY, PH = 236, 86

    def cuadro(t):
        a = Ventana(t, t0, t1, spec.get("etiqueta", ""), m)
        if a.fuera:
            return a.cerrar()
        d = a.d
        act = max([k for k, (_, _, te) in enumerate(et) if t >= te - 0.05], default=-1)
        al0 = prog(t, t0 + 0.05, 0.3)
        for k, (corto, _, te) in enumerate(et):
            x = MARGEN + k * (pw + GAP)
            AL = int(255 * al0)
            if k < act:
                d.rounded_rectangle([x, PY, x + pw, PY + PH], PH // 2, fill=m.GRIS + (AL,))
                palomita(d, x + 26, PY + 28, 30, m.TEXTO, 7)
                a.texto((x + 70, PY + 22), corto, fs(32), m.TEXTO, al0)
            elif k == act:
                r = rebote((t - te + 0.05) / 0.35)
                g = Image.new("RGBA", (pw, PH), (0, 0, 0, 0))
                gd = ImageDraw.Draw(g)
                gd.rounded_rectangle([0, 0, pw - 1, PH - 1], PH // 2, fill=m.ACENTO + (255,))
                gd.text(((pw - gd.textlength(corto, font=fs(32))) / 2, 22), corto, font=fs(32), fill=m.TEXTO + (255,))
                g = escalar(g, 0.85 + 0.15 * r)
                a.pegar(g, (x + (pw - g.width) / 2, PY + (PH - g.height) / 2))
            else:
                d.rounded_rectangle([x, PY, x + pw, PY + PH], PH // 2, outline=m.TENUE + (AL,), width=3)
                a.texto((x + (pw - a.ancho(corto, fs(32))) / 2, PY + 22), corto, fs(32), m.TENUE, al0)
        if act >= 0:
            _, det, te = et[act]
            al = prog(t, te, 0.3)
            y = 380
            for l in partir(a, det, fb(72), W - 2 * MARGEN - 40):
                a.texto((MARGEN, y + int(24 * (1 - al))), l, fb(72), m.TEXTO, al)
                y += 88
        return a.cerrar()

    auto = [te + 0.5 for _, _, te in et] + [t1 - 0.2]
    return cuadro, t0, t1, _claves(spec, A, auto), [te for _, _, te in et]


PIEZAS = {"lista": lista, "comparativa": comparativa, "titular": titular, "burbujas": burbujas,
          "controles": controles, "sello": sello, "contador": contador, "etapas": etapas}
