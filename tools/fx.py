"""El catalogo de efectos de video y cuanto se ha usado cada uno.

    python tools/fx.py              # el catalogo + uso en los ultimos reels (lo que se lee al proponer)
    python tools/fx.py --ultimos 8  # mirar mas reels hacia atras

Es lo UNICO que hay que leer para proponer efectos en un reel: que hay, para que momento
sirve cada uno, sus cuidados, y cuales se han usado mucho ultimamente (para variar). El
formato exacto para escribirlos en el plan esta en el docstring de pipeline/fx.py, y solo
se lee al escribirlos. El codigo de cada efecto no se lee: ya esta probado.

El uso se cuenta de lo que el armado ya guarda (proyectos/<reel>/fx/<efecto> <clave>.*),
asi que no hay que anotar nada a mano. El catalogo vive AQUI y en ningun otro lado: si
se agrega un efecto, se agrega a CATALOGO (y a pipeline/fx.py, que es quien lo arma).
"""
import glob
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# efecto: (familia, momento del reel, que hace, cuidado, estado)
#   familia: detras (pista de en medio + recorte) | encima (tarjeta) | pantalla (b-roll del tramo)
CATALOGO = {
    "vidrio":        ("detras", "gancho / la idea", "palabra de vidrio en la pared, detras de la cabeza", "4-7 letras", "aprobado"),
    "portada":       ("detras", "gancho / la idea", "palabra gigante de revista que la cabeza tapa", "una sola palabra", "aprobado"),
    "telefono":      ("detras", "mensajes / WhatsApp", "celular junto a la cabeza con los mensajes", "2-4 mensajes cortos", "aprobado"),
    "lista":         ("encima", "pasos / requisitos", "tarjeta de pasos que se palomean", "2-5 pasos de ~22 letras", "aprobado"),
    "antes_despues": ("encima", "antes y ahora / un numero que cambia", "tarjetita: antes tachado, ahora", "solo cifras PROPIAS o del demo", "aprobado"),
    "chat":          ("encima", "demo / 'le escribo esto'", "chat de IA sobre el pecho, el prompt escribiendose", "prompt de 3-4 lineas", "aprobado"),
    "acercamiento":  ("pantalla", "enfasis / la palabra que golpea", "golpe de camara centrado en la cara", "dentro de UN corte", "aprobado"),
    "vertigo":       ("pantalla", "revelacion / 'y ahi me di cuenta'", "tu quieto, el cuarto se acerca", "dentro de UN corte; una vez por reel", "aprobado"),
    "revelacion":    ("pantalla", "'esto lo hizo la IA' / proceso", "el video entra a una ventana y se palomean pasos", "dentro de UN corte", "aprobado"),
    "cierre":        ("pantalla", "cierre / llamada a la accion", "tarjeta final con muro de miniaturas propias", "solo videos PROPIOS", "aprobado"),
    # --- los 14 del 27/28-oct, hechos de golpe y aprobados juntos por Javier el 28-oct ---
    "titulares":     ("detras", "'todos hablan de X' / noticia", "notas, citas y publicaciones en la pared", "2-3 textos (mas, se tapan)", "aprobado"),
    "grafica":       ("detras", "crecimiento / 'despego'", "linea que se dibuja sobre la cabeza y sube", "cifra PROPIA o del demo", "aprobado"),
    "muro":          ("detras", "'he hecho cientos' / cuerpo de trabajo", "miniaturas propias tapizando la pared", "solo videos PROPIOS; sin vistas", "aprobado"),
    "orbita":        ("detras", "prueba social / 'todas estas'", "tarjetas de videos girando alrededor del pecho", "solo videos PROPIOS; sin vistas", "aprobado"),
    "grafica_vidrio": ("encima", "un numero que crece", "tarjeta translucida con la cifra subiendo", "cifra PROPIA o del demo", "aprobado"),
    "marco":         ("pantalla", "gancho / 'este video'", "ventana de Reels con la cabeza saliendose", "dentro de UN corte", "aprobado"),
    "verde":         ("pantalla", "hablar de una herramienta", "la persona abajo frente a una captura", "imagen propia; UN corte", "aprobado"),
    "papel":         ("pantalla", "una cifra que golpea ('3X', '$0')", "hoja cuadriculada con garabatos y la cifra", "cifra corta; UN corte", "aprobado"),
    "escritorio":    ("pantalla", "un proceso paso a paso", "escritorio arriba y tarjetas que caen", "hasta 4 tarjetas; UN corte", "aprobado"),
    "contenedor":    ("pantalla", "'cientos de...' / muchas cosas a una", "panel arriba y cosas que caen en una caja", "UN corte", "aprobado"),
    "gis":           ("pantalla", "momento ligero o chistoso", "linea de gis alrededor de la silueta y un dibujito", "UN corte", "aprobado"),
    "articulo":      ("pantalla", "nombrar una herramienta o marca", "pagina desenfocada con una palabra resaltada", "1-2 palabras", "aprobado"),
    "pixeles":       ("pantalla", "una frase que se lee como titulo", "cada palabra se enciende en una pantalla", "frase corta (5 lineas max)", "aprobado"),
    "tunel":         ("pantalla", "entre dos tomas / 'pero espera'", "la toma acelera en tunel y entra la siguiente", "va EN un corte", "aprobado"),
}


def uso(ultimos=5):
    """{efecto: en cuantos reels salio} en los `ultimos` reels armados (por fecha), y esos reels.
    Se cuenta por REEL, no por archivo: rehacer un reel deja varias versiones del mismo efecto."""
    proyectos = [p for p in glob.glob(os.path.join(RAIZ, "proyectos", "*", "fx")) if os.path.isdir(p)]
    proyectos = [p for p in proyectos if not os.path.basename(os.path.dirname(p)).startswith("prueba fx")]
    proyectos.sort(key=os.path.getmtime, reverse=True)
    proyectos = proyectos[:ultimos]
    cuenta = {}
    for p in proyectos:
        for tipo in {f.split(" ")[0] for f in os.listdir(p)} & set(CATALOGO):
            cuenta[tipo] = cuenta.get(tipo, 0) + 1
    return cuenta, [os.path.basename(os.path.dirname(p)) for p in proyectos]


def main():
    ultimos = 5
    if "--ultimos" in sys.argv:
        ultimos = int(sys.argv[sys.argv.index("--ultimos") + 1])
    cuenta, reels = uso(ultimos)
    print("EFECTOS DE VIDEO (se piden en el plan con \"fx\"; formato: docstring de pipeline/fx.py)\n")
    print("%-14s %-9s %-36s %-5s %s" % ("efecto", "va", "momento", "reels", "cuidado"))
    for nombre, (familia, momento, _, cuidado, estado) in CATALOGO.items():
        marca = "" if estado == "aprobado" else "  [%s]" % estado.upper()
        print("%-14s %-9s %-36s %-5s %s%s" % (nombre, familia, momento[:36], cuenta.get(nombre, 0), cuidado, marca))
    print("\nUso contado en los ultimos %d reels: %s" % (len(reels), ", ".join(reels) or "(ninguno todavia)"))
    print("Regla: el mas usado ultimamente NO se propone primero, salvo que sea claramente el mejor (decirlo).")


if __name__ == "__main__":
    main()
