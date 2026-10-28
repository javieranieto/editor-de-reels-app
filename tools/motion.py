"""La biblioteca de motion graphics desde la consola.

    python tools/motion.py                         # el catalogo: que piezas hay y en que estado
    python tools/motion.py --muestras [pieza...]   # hoja de cada pieza, para ofrecerlas (no hace .mov)
    python tools/motion.py <spec.json> --palabras <plan.json|clip.json> [--salida <carpeta>] [--solo-hoja]

El spec dice que pieza, que texto y en que palabras; las palabras salen del plan del clip.
Se revisa SIEMPRE la hoja_<nombre>.png antes de dar el .mov por bueno.
"""
import argparse
import io
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from pipeline import motion  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec", nargs="?")
    ap.add_argument("--palabras")
    ap.add_argument("--salida")
    ap.add_argument("--solo-hoja", action="store_true")
    ap.add_argument("--muestras", nargs="*")
    ap.add_argument("--marca", default=None)
    a = ap.parse_args()

    if a.muestras is not None:
        sal = a.salida or os.path.join(RAIZ, "proyectos", "_motion_muestras")
        for nombre in a.muestras or list(motion.CATALOGO):
            c = motion.CATALOGO[nombre]
            spec = dict(c["spec"], nombre=nombre)
            r = motion.renderizar(spec, motion.palabras_sinteticas(c["frase"]), sal, a.marca, solo_hoja=True)
            print("%-12s %-9s %s" % (nombre, "APROBADA" if c["estado"].startswith("aprobada") else "nueva", r["hoja"]))
        return

    if not a.spec:
        print("Piezas de motion (estilo VENTANA, marca %s):\n" % a.marca)
        for nombre, c in motion.CATALOGO.items():
            print("  %-12s %s\n  %-12s sirve para: %s\n" % (nombre, c["estado"], "", c["sirve"]))
        print("Muestras: python tools/motion.py --muestras  ->  proyectos/_motion_muestras/hoja_<pieza>.png")
        return

    if not a.palabras:
        raise SystemExit("falta --palabras <plan.json del clip>: los tiempos salen de ahi, nunca a mano")
    spec = json.load(open(a.spec, encoding="utf-8"))
    sal = a.salida or os.path.join(os.path.dirname(os.path.abspath(a.palabras)), "motion")
    r = motion.renderizar(spec, motion.Palabras.de_archivo(a.palabras), sal, a.marca, solo_hoja=a.solo_hoja)
    print(json.dumps(r, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
