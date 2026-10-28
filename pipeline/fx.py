"""Los efectos de video (detras, tarjetas, acercamiento) pedidos desde el plan.

En el plan.json:

    "fx": [
      {"efecto": "vidrio",   "palabra": "VISTO", "en": "puerta", "dur": 4},
      {"efecto": "portada",  "palabra": "FOCO", "encabezado": "el tema de hoy", "en": "foco"},
      {"efecto": "telefono", "en": "mensaje", "dur": 5, "contacto": "Cliente nuevo",
       "mensajes": [{"en": "pregunta", "quien": "ellos", "texto": "...", "hora": "10:42"}],
       "visto_en": "visto"},
      {"efecto": "lista", "en": "tres", "titulo": "Lo que sí funciona",
       "pasos": [{"en": "contesta", "texto": "Contesta en 5 minutos"}]},
      {"efecto": "antes_despues", "en": "antes", "etiqueta": "Tiempo de respuesta",
       "antes": "3 horas", "despues": "5 minutos", "despues_en": "ahora"},
      {"efecto": "acercamiento", "golpes": [{"en": "pregunta", "escala": 1.15},
                                            {"en": "puerta", "escala": 1.28}], "fin": "cerrada"},
      {"efecto": "revelacion", "en": "editado", "fin": "listo", "titulo": "Editor de reels",
       "archivo": "mi-video.mp4", "pasos": [{"en": "transcribe", "texto": "Transcribir"},
                                            {"en": "corta", "texto": "Quitar silencios"}]},
      {"efecto": "chat", "en": "escribo", "dur": 7, "app": "Tu asistente",
       "prompt": "Edita este video: quita los silencios", "escribe_en": "escribo",
       "respuesta": "Listo. Te dejé el proyecto en CapCut."},
      {"efecto": "vertigo", "en": "cuenta", "fin": "cerrada", "modo": "acerca", "escala": 1.22},
      {"efecto": "cierre", "en": "comenta", "dur": 4, "titular": "Te lo regalo",
       "linea": "Comenta REPO y te lo mando", "fuentes": "C:/mis videos/terminados/*.mp4"}
    ]

"fuentes" del cierre: una lista de videos/imagenes o un patron (glob). Solo material PROPIO.

Cada "en" es un ancla de pipeline/motion: una palabra de la linea de tiempo FINAL,
{"en": "palabra", "despues_de": "otra", "mas": 0.2}, o segundos. 🔴 Si la palabra
se repite, va "despues_de": si no, agarra la primera.

Como queda en CapCut (de abajo arriba):
    video  ·  b-roll (aqui entra el acercamiento)  ·  adornos del plan
    ·  "fx detras" (vidrio, portada, telefono)  ·  "fx recorte" (la persona)
    ·  "fx tarjetas" (lista, antes y despues)  ·  textos (siempre encima)

El recorte se saca de la GRABACION ORIGINAL, pieza por pieza si el efecto cruza
un corte, y lleva el mismo zoom seco que su corte: si no, queda desfasado del
cuerpo. Un zoom ANIMADO no se puede copiar a un recorte ya hecho: se avisa.

Lo armado se guarda en <trabajo>/fx/ con un nombre que sale de lo que se pidio:
volver a generar el reel no lo recalcula.
"""
import hashlib
import json
import os
import subprocess

from pipeline import (acercamiento, cartas, chat, cierre, detras, escenas, pared, recorte, revelacion,
                      tarjetas, telefono, vertigo)
from pipeline.motion.base import Palabras

DETRAS = {"vidrio", "portada", "telefono", "titulares", "grafica", "muro", "orbita"}
TARJETAS = {"lista", "antes_despues", "chat", "grafica_vidrio"}
ESCENAS = {"marco", "verde", "papel", "escritorio", "contenedor", "gis"}   # pantalla completa, de UN corte
CARTAS = {"articulo", "pixeles"}                                          # pantalla completa, sin video
EFECTOS = DETRAS | TARJETAS | ESCENAS | CARTAS | {"acercamiento", "cierre", "revelacion", "vertigo", "tunel"}


def _fuentes(valor, n, nombre):
    """Una lista de videos/imagenes o un patron (glob). Aborta si no hay ninguno."""
    import glob
    fuentes = sorted(glob.glob(valor)) if isinstance(valor, str) else list(valor or [])
    if not fuentes:
        raise SystemExit("fx #%d: %s no encontro videos en %r" % (n, nombre, valor))
    return fuentes


def _clave(*partes):
    return hashlib.sha1(json.dumps(partes, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:10]


def _cronologia(segmentos):
    """[(inicio en la linea de tiempo, segmento)] en orden."""
    salida, cursor = [], 0.0
    for s in segmentos:
        salida.append((cursor, s))
        cursor += s["fin"] - s["ini"]
    return salida, cursor


def _piezas(crono, t0, t1):
    """De un tramo de la linea de tiempo, los pedazos de grabacion que lo forman:
    [(segmento, indice, origen_ini, origen_fin, linea_ini, linea_fin)]."""
    piezas = []
    for i, (c, s) in enumerate(crono):
        d = s["fin"] - s["ini"]
        a, b = max(t0, c), min(t1, c + d)
        if b - a > 0.05:
            piezas.append((s, i, s["ini"] + (a - c), s["ini"] + (b - c), a, b))
    return piezas


def _dur(ruta):
    """Lo que dura DE VERDAD un clip ya armado (cuadros enteros): el fin del b-roll se toma
    de aqui y no del tramo pedido, o capcut_lib lo rechaza por pedirle 0.01 s de mas."""
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", ruta],
                       capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


def _encuadre(s, modo_zoom, log):
    """(escala, x, y) del zoom SECO del corte, para copiarlo al recorte. None si es animado."""
    z = s.get("zoom")
    if not z:
        return (1.0, 0.0, 0.0) if modo_zoom not in ("punch", "progresivo") else None
    if isinstance(z, dict):
        if z.get("anim"):
            return None
        pico = float(z.get("punch", z.get("pico", 1.14)))
        y = float(z["y"]) if "y" in z else -float(z.get("ancla", 0.0)) * (pico - 1.0)
        return (pico, float(z.get("x", 0.0)), y)
    if isinstance(z, (int, float)):
        return (float(z), 0.0, 0.0)
    return None


def _recorte_pieza(pieza, carpeta, modo_zoom, log):
    s, i, oi, of, li, lf = pieza
    destino = os.path.join(carpeta, "recorte %s.mov" % _clave(s["path"], round(oi, 3), round(of, 3)))
    if not os.path.exists(destino):
        recorte.recortar(s["path"], destino, oi, of)
    enc = _encuadre(s, modo_zoom, log)
    if enc is None:
        log("  aviso fx: el corte #%d tiene zoom ANIMADO; el recorte va sin zoom y puede "
            "verse desfasado del cuerpo. Usa zoom seco en ese corte." % (i + 1))
        enc = (1.0, 0.0, 0.0)
    escala, x, y = enc
    return {"archivo": destino, "ini": li, "fin": lf, "pista": "fx recorte",
            "escala": escala, "x": x, "y": y}


def resolver(lista, segmentos, palabras, trabajo, modo_zoom=None, log=print, marca=None):
    """Arma cada efecto pedido y devuelve (overlays, broll) listos para capcut_lib.

    palabras : las de la linea de tiempo FINAL (start/end/word).
    """
    if not lista:
        return [], []
    from pipeline.motion.base import usar
    usar(marca)           # la marca del plan ("marca": "mi_marca"); sin ella, la de ejemplo
    carpeta = os.path.join(trabajo, "fx")
    os.makedirs(carpeta, exist_ok=True)
    crono, total = _cronologia(segmentos)
    pw = Palabras(palabras or [])

    def t(a, despues_de=-1.0):
        if not palabras and not isinstance(a, (int, float)):
            raise SystemExit("fx: este reel no tiene palabras en la linea de tiempo; usa segundos en 'en'")
        return pw.ancla(a, despues_de)

    detras_ov, recortes, tarjetas_ov, broll = [], [], [], []
    ocupado_acerc = []
    for n, e in enumerate(lista, 1):
        tipo = e.get("efecto")
        if tipo not in EFECTOS:
            raise SystemExit("fx #%d: efecto %r no existe (hay: %s)" % (n, tipo, ", ".join(sorted(EFECTOS))))

        if tipo == "acercamiento":
            golpes_abs = [(t(g["en"]), float(g["escala"])) for g in e["golpes"]]
            t0 = min(g[0] for g in golpes_abs) - float(e.get("antes", 0.3))
            t1 = t(e["fin"]) if "fin" in e else max(g[0] for g in golpes_abs) + float(e.get("dur", 2.0))
            piezas = _piezas(crono, max(0.0, t0), min(total, t1))
            if len(piezas) != 1:
                raise SystemExit("fx #%d: el acercamiento cruza %d cortes; tiene que caer dentro de UNO "
                                 "(un corte ya es un cambio de camara)" % (n, len(piezas)))
            s, i, oi, of, li, lf = piezas[0]
            if s.get("zoom"):
                log("  aviso fx: el corte #%d ya tiene zoom seco; el acercamiento lo reemplaza en ese tramo" % (i + 1))
            golpes = [(g - li, esc) for g, esc in golpes_abs]
            destino = os.path.join(carpeta, "acercamiento %s.mp4" % _clave(s["path"], round(oi, 3), round(of, 3), golpes))
            if not os.path.exists(destino):
                acercamiento.acercar(s["path"], destino, golpes, oi, of)
            broll.append({"archivo": destino, "ini": li, "fin": min(lf, li + _dur(destino)), "desde": 0, "fx": True})
            ocupado_acerc.append((li, lf))
            log("  fx #%d acercamiento %.2f-%.2f s (%d golpes)" % (n, li, lf, len(golpes)))
            continue

        if tipo == "vertigo":
            t0 = t(e["en"])
            t1 = t(e["fin"]) if "fin" in e else t0 + float(e.get("dur", 2.5))
            piezas = _piezas(crono, t0, min(total, t1))
            if len(piezas) != 1:
                raise SystemExit("fx #%d: el vertigo cruza %d cortes; tiene que caer dentro de UNO" % (n, len(piezas)))
            s, i, oi, of, li, lf = piezas[0]
            if s.get("zoom"):
                log("  aviso fx: el corte #%d ya tiene zoom seco; el vertigo lo reemplaza en ese tramo" % (i + 1))
            modo, escala = e.get("modo", "acerca"), float(e.get("escala", 1.22))
            destino = os.path.join(carpeta, "vertigo %s.mp4" % _clave(s["path"], round(oi, 3), round(of, 3), modo, escala))
            if not os.path.exists(destino):
                vertigo.vertigo(s["path"], destino, oi, of, modo, escala)
            broll.append({"archivo": destino, "ini": li, "fin": min(lf, li + _dur(destino)), "desde": 0, "fx": True})
            ocupado_acerc.append((li, lf))
            log("  fx #%d vertigo %.2f-%.2f s (%s, %.2f)" % (n, li, lf, modo, escala))
            continue

        if tipo == "revelacion":
            t0 = t(e["en"])
            t1 = t(e["fin"]) if "fin" in e else t0 + float(e.get("dur", 5.0))
            piezas = _piezas(crono, t0, min(total, t1))
            if len(piezas) != 1:
                raise SystemExit("fx #%d: la revelacion cruza %d cortes; tiene que caer dentro de UNO" % (n, len(piezas)))
            s, i, oi, of, li, lf = piezas[0]
            if s.get("zoom"):
                log("  aviso fx: el corte #%d ya tiene zoom seco; la revelacion lo reemplaza en ese tramo" % (i + 1))
            pasos = [(t(p["en"], t0 - 0.01) - li, p["texto"]) for p in e["pasos"]]
            destino = os.path.join(carpeta, "revelacion %s.mp4" % _clave(s["path"], round(oi, 3), round(of, 3), pasos,
                                                                          e.get("titulo"), e.get("archivo")))
            if not os.path.exists(destino):
                revelacion.revelar(s["path"], destino, pasos, t0 - li, oi, of,
                                   titulo=e.get("titulo", "Editor de reels"), archivo=e.get("archivo", "mi-video.mp4"))
            broll.append({"archivo": destino, "ini": li, "fin": min(lf, li + _dur(destino)), "desde": 0, "fx": True})
            ocupado_acerc.append((li, lf))
            log("  fx #%d revelacion %.2f-%.2f s (%d pasos)" % (n, li, lf, len(pasos)))
            continue

        if tipo in ESCENAS:
            t0 = t(e["en"])
            t1 = t(e["fin"]) if "fin" in e else t0 + float(e.get("dur", 3.0))
            piezas = _piezas(crono, t0, min(total, t1))
            if len(piezas) != 1:
                raise SystemExit("fx #%d: %s cruza %d cortes; tiene que caer dentro de UNO" % (n, tipo, len(piezas)))
            s, i, oi, of, li, lf = piezas[0]
            if s.get("zoom"):
                log("  aviso fx: el corte #%d ya tiene zoom seco; %s lo reemplaza en ese tramo" % (i + 1, tipo))
            enlinea = lambda lista: [(t(x["en"], t0 - 0.01) - li, x["texto"]) for x in lista]
            destino = os.path.join(carpeta, "%s %s.mp4" % (tipo, _clave(s["path"], round(oi, 3), round(of, 3), dict(e, en=None))))
            if not os.path.exists(destino):
                if tipo == "marco":
                    escenas.marco(s["path"], destino, oi, of, usuario=e.get("usuario"))
                elif tipo == "verde":
                    escenas.verde(s["path"], destino, oi, of, imagen=e.get("imagen"))
                elif tipo == "papel":
                    escenas.papel(s["path"], destino, e["texto"], oi, of)
                elif tipo == "escritorio":
                    escenas.escritorio(s["path"], destino, enlinea(e["tarjetas"]), oi, of)
                elif tipo == "contenedor":
                    escenas.contenedor(s["path"], destino, enlinea(e["cosas"]), oi, of)
                elif tipo == "gis":
                    escenas.gis(s["path"], destino, e.get("dibujo", "estrella"), oi, of)
            broll.append({"archivo": destino, "ini": li, "fin": min(lf, li + _dur(destino)), "desde": 0, "fx": True})
            ocupado_acerc.append((li, lf))
            log("  fx #%d %s %.2f-%.2f s" % (n, tipo, li, lf))
            continue

        if tipo == "tunel":
            # el corte mas cercano a la palabra: de ahi sale la transicion entre las dos tomas
            ta = t(e["en"])
            cortes = [(abs(c - ta), j) for j, (c, _) in enumerate(crono) if j > 0]
            if not cortes:
                raise SystemExit("fx #%d: el tunel necesita un corte y este reel tiene uno solo" % n)
            _, j = min(cortes)
            c_ini, sb = crono[j]
            _, sa = crono[j - 1]
            antes, despues = float(e.get("antes", 0.30)), float(e.get("despues", 0.40))
            destino = os.path.join(carpeta, "tunel %s.mp4" % _clave(sa["path"], sa["fin"], sb["path"], sb["ini"], antes, despues))
            if not os.path.exists(destino):
                acercamiento.tunel(sa["path"], sa["fin"], sb["path"], sb["ini"], destino, antes, despues)
            broll.append({"archivo": destino, "ini": c_ini - antes,
                          "fin": c_ini - antes + _dur(destino), "desde": 0, "fx": True})
            ocupado_acerc.append((c_ini - antes, c_ini + despues))
            log("  fx #%d tunel en el corte #%d (%.2f s)" % (n, j + 1, c_ini))
            continue

        if tipo in CARTAS:
            t0 = t(e["en"])
            t1 = t(e["fin"]) if "fin" in e else min(total, t0 + float(e.get("dur", 2.5)))
            destino = os.path.join(carpeta, "%s %s.mp4" % (tipo, _clave(dict(e, en=None), round(t0, 3), round(t1, 3))))
            if not os.path.exists(destino):
                if tipo == "articulo":
                    cartas.articulo(destino, e["palabra"], dur=t1 - t0)
                else:
                    dichas = [(w["start"] - t0, w["word"].strip()) for w in (palabras or [])
                              if t0 - 0.01 <= w["start"] < t1]
                    cartas.pixeles(destino, dichas, dur=t1 - t0)
            broll.append({"archivo": destino, "ini": t0, "fin": min(t1, t0 + _dur(destino)), "desde": 0, "fx": True})
            ocupado_acerc.append((t0, t1))
            log("  fx #%d %s en %.2f s (%.1f s)" % (n, tipo, t0, t1 - t0))
            continue

        if tipo == "cierre":
            fuentes = _fuentes(e["fuentes"], n, "el cierre")
            t0 = t(e["en"])
            t1 = min(total, t0 + float(e.get("dur", 4.0)))
            destino = os.path.join(carpeta, "cierre %s.mp4" % _clave(e["titular"], e.get("linea"), fuentes, round(t1 - t0, 3)))
            if not os.path.exists(destino):
                cierre.cierre_muro(destino, e["titular"], fuentes, e.get("linea"), dur=t1 - t0)
            broll.append({"archivo": destino, "ini": t0, "fin": min(t1, t0 + _dur(destino)), "desde": 0, "fx": True})
            ocupado_acerc.append((t0, t1))     # tapa la pantalla: nada "detras" puede caer ahi
            log("  fx #%d cierre en %.2f s (%.1f s, %d miniaturas de %d archivos)" % (n, t0, t1 - t0, 20, len(fuentes)))
            continue

        t0 = t(e["en"])
        dur = float(e.get("dur", 4.0))
        t1 = min(total, t0 + dur)
        dur = t1 - t0
        rel = lambda a: t(a, t0 - 0.01) - t0      # anclas internas, contadas desde el efecto
        datos = dict(e, en=None)
        destino = os.path.join(carpeta, "%s %s.mov" % (tipo, _clave(datos, round(t0, 3), round(dur, 3))))

        if not os.path.exists(destino):
            if tipo == "vidrio":
                detras.letras_vidrio(e["palabra"], destino, dur=dur, **({"y": e["y"]} if "y" in e else {}))
            elif tipo == "portada":
                detras.portada(e["palabra"], destino, dur=dur, encabezado=e.get("encabezado"),
                               **({"y": e["y"]} if "y" in e else {}))
            elif tipo == "telefono":
                msgs = [(rel(m["en"]), m.get("quien", "ellos"), m["texto"], m.get("hora", "")) for m in e["mensajes"]]
                telefono.telefono(destino, msgs, contacto=e.get("contacto", "Cliente"),
                                  visto_en=rel(e["visto_en"]) if e.get("visto_en") else None,
                                  dur=dur, lado=e.get("lado", "derecha"))
            elif tipo == "lista":
                tarjetas.lista_pasos(destino, [(rel(p["en"]), p["texto"]) for p in e["pasos"]],
                                     titulo=e.get("titulo", "Te toca"), dur=dur)
            elif tipo == "chat":
                fuentes = e.get("miniaturas") or [_piezas(crono, t0, t0 + 0.2)[0][0]["path"]]
                chat.chat_pantalla(destino, e["prompt"], dur=dur, app=e.get("app", "Tu asistente"),
                                   miniaturas_de=fuentes if e.get("adjuntos", True) else None,
                                   archivos_en=rel(e["archivos_en"]) if e.get("archivos_en") else 0.4,
                                   escribe_en=rel(e["escribe_en"]) if e.get("escribe_en") else 1.3,
                                   enviar_en=rel(e["enviar_en"]) if e.get("enviar_en") else None,
                                   respuesta=e.get("respuesta"))
            elif tipo == "titulares":
                pared.titulares(destino, e["textos"], dur=dur)
            elif tipo == "grafica":
                pared.grafica(destino, e.get("etiqueta", ""), dur=dur, despegue=float(e.get("despegue", 0.6)))
            elif tipo == "muro":
                pared.muro(destino, _fuentes(e["fuentes"], n, "el muro"), dur=dur)
            elif tipo == "orbita":
                pared.orbita(destino, destino.replace(".mov", " frente.mov"), _fuentes(e["fuentes"], n, "la orbita"),
                             titulos=e.get("titulos"), dur=dur)
            elif tipo == "grafica_vidrio":
                tarjetas.grafica_vidrio(destino, e["etiqueta"], float(e["desde"]), float(e["hasta"]),
                                        sufijo=e.get("sufijo", ""), dur=dur)
            elif tipo == "antes_despues":
                tarjetas.antes_despues(destino, e["etiqueta"], e["antes"], e["despues"],
                                       despues_en=rel(e["despues_en"]), dur=dur, lado=e.get("lado", "derecha"))

        entrada = {"archivo": destino, "ini": t0, "fin": t1, "escala": 1.0, "y": 0.0}
        if tipo == "orbita":   # lo de adelante del cuerpo va arriba del recorte
            tarjetas_ov.append(dict(entrada, archivo=destino.replace(".mov", " frente.mov"), pista="fx tarjetas"))
        if tipo in DETRAS:
            detras_ov.append(dict(entrada, pista="fx detras"))
            if e.get("recorte", True):
                for p in _piezas(crono, t0, t1):
                    recortes.append(_recorte_pieza(p, carpeta, modo_zoom, log))
        else:
            tarjetas_ov.append(dict(entrada, pista="fx tarjetas"))
        log("  fx #%d %s en %.2f s (%.1f s)" % (n, tipo, t0, dur))

    for a, b in ocupado_acerc:
        for o in detras_ov:
            if o["ini"] < b and a < o["fin"]:
                raise SystemExit("fx: un efecto detras (%.2f s) cae sobre un acercamiento o un cierre (%.2f-%.2f s); "
                                 "el recorte saldria sin el zoom. Sepáralos." % (o["ini"], a, b))
    # el orden de la lista decide el orden de las pistas: detras, recorte, tarjetas
    return detras_ov + recortes + tarjetas_ov, broll
