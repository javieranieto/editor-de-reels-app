"""Musica de un episodio del pueblo de negocios, armada con los temas de tools/chiptune.py segun su guion.json:

  exploracion -> (remolino) batalla -> exploracion -> silencio en el GAME OVER (ahi suena su melodia, que esta en
  blips.wav) -> exploracion bajita en el consejo.

    python tools/pueblo_musica.py animado/videos/ejemplo-pueblo   ->  assets/musica.wav

Si el guion no trae batalla, es exploracion de punta a punta (con el mismo silencio en el game over).
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chiptune import SR, guardar, tema  # noqa: E402


def rampa(n, sube):
    return np.linspace(0, 1, n) if sube else np.linspace(1, 0, n)


def main():
    carpeta = sys.argv[1]
    g = json.load(open(os.path.join(carpeta, "guion.json"), encoding="utf-8"))
    dur = g["dur"]
    pista = np.zeros(int(dur * SR))

    def poner(nombre, a, b, vol=1.0, sube=0.05, baja=0.2):
        if b <= a:
            return
        m = tema(nombre, b - a) * vol
        s, n = int(sube * SR), int(baja * SR)
        if s:
            m[:s] *= rampa(s, True)
        if n:
            m[-n:] *= rampa(n, False)
        i = int(a * SR)
        pista[i:i + len(m)] += m[: len(pista) - i]

    go = g.get("game_over", dur)
    B = g.get("batalla")
    if B:
        poner("exploracion", 0, B["swirl"], baja=0.15)
        poner("batalla", B["swirl"], B["t1"] + 0.4, sube=0.02, baja=0.3)
        poner("exploracion", B["t1"] + 0.4, go, sube=0.3, baja=0.3)
    else:
        poner("exploracion", 0, go, baja=0.3)
    if "consejo" in g:
        poner("exploracion", g["consejo"], dur, vol=0.55, sube=0.6, baja=1.2)
    salida = os.path.join(carpeta, "assets", "musica.wav")
    os.makedirs(os.path.dirname(salida), exist_ok=True)
    guardar(pista, salida)
    print("->", salida)


if __name__ == "__main__":
    main()
