"""Sonidos de juego de 8 bits para un episodio del pueblo de negocios (animado/marcas/pueblo.js).

Lee el guion.json del episodio y escribe assets/blips.wav con:
- el "bip" de cada letra que aparece en la cajita (a VEL letras por segundo, igual que el video), con un tono
  por personaje: asi se oye quien habla sin voz;
- un "!" cuando alguien se desespera (si el guion trae "sorpresa"), un clic al mover la flechita del menu,
  la melodia de GAME OVER y un "ding" en el consejo.

    python tools/pueblo_blips.py animado/videos/ejemplo-pueblo

Onda cuadrada, como las consolas de 8 bits. Se corre las veces que sea: sobreescribe el mismo archivo.
"""
import json
import os
import sys
import wave

import numpy as np

SR = 44100
VEL = 26                      # letras por segundo: el mismo VEL de marcas/pueblo.js
TONO = {"": 520, "EMPLEADO": 700, "CLIENTE": 600, "TÚ": 440}


def cuadrada(f, dur, vol=0.18):
    t = np.arange(int(SR * dur)) / SR
    env = np.minimum(1, (dur - t) / 0.01)                      # sin chasquido al final
    return vol * np.sign(np.sin(2 * np.pi * f * t)) * env


def poner(pista, ini, son):
    i = int(ini * SR)
    pista[i:i + len(son)] += son[: max(0, len(pista) - i)]


def main():
    carpeta = sys.argv[1]
    g = json.load(open(os.path.join(carpeta, "guion.json"), encoding="utf-8"))
    pista = np.zeros(int(SR * g["dur"]))
    vel = g.get("vel", VEL)
    for d in g["dialogos"]:
        f = TONO.get(d["quien"], 560)
        for i, ch in enumerate(d["texto"].replace("\n", "")):
            if ch.strip() and i % 2 == 0:                       # uno cada dos letras: cada letra satura
                poner(pista, d["t0"] + i / vel, cuadrada(f, 0.035, 0.12))
    for s in g.get("sonidos", []):                              # efectos de juego con nombre
        t, tipo = s["t"], s["tipo"]
        if tipo == "campana":
            poner(pista, t, cuadrada(1568, 0.07, 0.1)); poner(pista, t + 0.08, cuadrada(1318, 0.18, 0.1))
        elif tipo == "notif":
            poner(pista, t, cuadrada(1046, 0.05, 0.12)); poner(pista, t + 0.06, cuadrada(1396, 0.08, 0.12))
        elif tipo == "tictac":
            for k in range(8):
                poner(pista, t + k * 0.18, cuadrada(1200 if k % 2 else 900, 0.02, 0.1))
        elif tipo == "sorpresa":
            poner(pista, t, cuadrada(880, 0.06)); poner(pista, t + 0.07, cuadrada(1320, 0.09))
        elif tipo == "swirl":                                    # sube rapido, como la entrada a una batalla
            for k in range(12):
                poner(pista, t + k * 0.045, cuadrada(300 + k * 90, 0.04, 0.14))
        elif tipo == "golpe":
            poner(pista, t, cuadrada(160, 0.09, 0.22)); poner(pista, t + 0.05, cuadrada(110, 0.12, 0.18))
        elif tipo == "huye":
            for k in range(6):
                poner(pista, t + k * 0.06, cuadrada(900 - k * 110, 0.05, 0.13))
        elif tipo == "select":
            poner(pista, t, cuadrada(1320, 0.05, 0.13))
    for t in g.get("sorpresa", []):
        poner(pista, t, cuadrada(880, 0.06)); poner(pista, t + 0.07, cuadrada(1320, 0.09))
    if "menu" in g:
        poner(pista, g["menu"]["t0"], cuadrada(990, 0.04))
        poner(pista, g["menu"]["cambia"], cuadrada(990, 0.04))
    if "game_over" in g:
        for k, f in enumerate([523, 440, 349, 262]):
            poner(pista, g["game_over"] + 0.3 + k * 0.22, cuadrada(f, 0.2 if k < 3 else 0.5, 0.2))
    if "consejo" in g:
        poner(pista, g["consejo"], cuadrada(1046, 0.08)); poner(pista, g["consejo"] + 0.09, cuadrada(1568, 0.25))
    pista = np.clip(pista, -1, 1)
    salida = os.path.join(carpeta, "assets", "blips.wav")
    os.makedirs(os.path.dirname(salida), exist_ok=True)
    with wave.open(salida, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((pista * 32767).astype(np.int16).tobytes())
    print("->", salida, f"({g['dur']} s)")


if __name__ == "__main__":
    main()
