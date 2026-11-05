"""Musica de 8 bits ORIGINAL, compuesta y sintetizada por codigo (0 creditos, sin derechos de nadie).

Cada tema son 8 compases en notas de octavo: melodia (pulso 25%), acompanamiento en arpegio (pulso 12.5%),
bajo (triangular) y bateria (ruido): las mismas ondas de las consolas de 8 bits. Las melodias y los acordes son
propios; no copian ningun tema de ningun juego.

    python tools/chiptune.py exploracion 30 salida.wav
    python tools/chiptune.py batalla 20 salida.wav

Desde otro script: `tema(nombre, segundos)` devuelve el arreglo de muestras a 44.1 kHz.
"""
import sys
import wave

import numpy as np

SR = 44100
NOTAS = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}


def hz(n):
    nombre, octava = n[:-1], int(n[-1])
    return 440.0 * 2 ** ((NOTAS[nombre] + 12 * (octava + 1) - 69) / 12)


# '-' sostiene la nota anterior, '.' es silencio. 8 octavos por compas.
TEMAS = {
    # Do mayor, alegre: para caminar por el pueblo
    "exploracion": {
        "bpm": 120,
        "acordes": ["C", "Am", "F", "G", "C", "Am", "F", "G"],
        "melodia": [
            "E5 - G5 - C6 - B5 A5", "G5 - E5 - C5 - D5 E5", "F5 - A5 - C6 - A5 G5", "G5 - - - D5 - . .",
            "E5 G5 C6 G5 E5 G5 C6 E6", "D6 - C6 - A5 - G5 -", "F5 A5 C6 A5 F5 A5 D6 C6", "B5 - - - G5 - - .",
        ],
        "bateria": "bombo . hat caja . hat bombo hat caja hat",
    },
    # La menor, rapido y tenso: para la batalla
    "batalla": {
        "bpm": 158,
        "acordes": ["Am", "Am", "F", "G", "Am", "Am", "F", "E"],
        "melodia": [
            "A5 . A5 C6 E6 - D6 C6", "B5 - C6 - A5 - - .", "F5 . F5 A5 C6 - B5 A5", "G5 - A5 - B5 - D6 -",
            "E6 . E6 D6 C6 - B5 C6", "A5 - E5 - A5 - C6 -", "D6 . C6 A5 F5 - A5 C6", "B5 - G#5 - E5 - B5 -",
        ],
        "bateria": "bombo hat caja hat bombo bombo caja hat",
        "bajo_corrido": True,
    },
}
ACORDES = {"C": ["C", "E", "G"], "Am": ["A", "C", "E"], "F": ["F", "A", "C"], "G": ["G", "B", "D"], "E": ["E", "G#", "B"]}


def pulso(f, n, duty):
    t = np.arange(n) / SR
    return np.where((t * f) % 1 < duty, 1.0, -1.0)


def triangular(f, n):
    t = np.arange(n) / SR
    return 2 * np.abs(2 * ((t * f) % 1) - 1) - 1


def envolvente(n, ataque=0.005, salida=0.03, sosten=0.75):
    e = np.full(n, sosten)
    a, r = int(ataque * SR), int(salida * SR)
    e[:a] = np.linspace(0, 1, a) if a else e[:a]
    if r < n:
        e[-r:] *= np.linspace(1, 0, r)
    return e


def _voz(pasos, paso, gen, vol):
    """pasos: lista de notas/'-'/'.' (una por octavo) -> muestras."""
    total = int(len(pasos) * paso * SR)
    out = np.zeros(total)
    i = 0
    while i < len(pasos):
        n = pasos[i]
        largo = 1
        while i + largo < len(pasos) and pasos[i + largo] == "-":
            largo += 1
        if n not in (".", "-"):
            m = int(largo * paso * SR)
            ini = int(i * paso * SR)
            out[ini:ini + m] += vol * gen(hz(n), m) * envolvente(m)
        i += largo
    return out


def _bateria(patron, compases, paso, rng):
    golpes = patron.split()
    n = int(compases * 8 * paso * SR)
    out = np.zeros(n)
    for c in range(compases):
        for j, g in enumerate(golpes[:8]):
            ini = int((c * 8 + j) * paso * SR)
            if g == "bombo":
                m = int(0.12 * SR); t = np.arange(m) / SR
                s = np.sin(2 * np.pi * np.cumsum(np.linspace(150, 45, m)) / SR) * np.exp(-t * 28) * 0.9
            elif g == "caja":
                m = int(0.13 * SR); t = np.arange(m) / SR
                s = rng.uniform(-1, 1, m) * np.exp(-t * 30) * 0.55
            elif g == "hat":
                m = int(0.03 * SR); t = np.arange(m) / SR
                s = rng.uniform(-1, 1, m) * np.exp(-t * 120) * 0.3
            else:
                continue
            out[ini:ini + m] += s[: max(0, n - ini)]
    return out


def tema(nombre, segundos):
    T = TEMAS[nombre]
    paso = 60 / T["bpm"] / 2
    compases_tema = len(T["melodia"])
    rng = np.random.default_rng(7)
    melodia = " ".join(T["melodia"]).split()
    arpegio, bajo = [], []
    for ac in T["acordes"]:
        r, t3, q = ACORDES[ac]
        arpegio += [f"{r}4", f"{t3}4", f"{q}4", f"{t3}4"] * 2
        if T.get("bajo_corrido"):
            bajo += [f"{r}2", f"{r}3"] * 4
        else:
            bajo += [f"{r}2", "-", f"{q}2", "-", f"{r}2", "-", f"{q}2", "-"]
    una = (_voz(melodia, paso, lambda f, n: pulso(f, n, 0.25), 0.17)
           + _voz(arpegio, paso, lambda f, n: pulso(f, n, 0.125), 0.06)
           + _voz(bajo, paso, triangular, 0.22)
           + _bateria(T["bateria"], compases_tema, paso, rng) * 0.35)
    veces = int(np.ceil(segundos * SR / len(una)))
    out = np.tile(una, veces)[: int(segundos * SR)]
    return np.clip(out, -1, 1)


def guardar(muestras, ruta):
    with wave.open(ruta, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(muestras, -1, 1) * 32767).astype(np.int16).tobytes())


if __name__ == "__main__":
    nombre, seg, ruta = sys.argv[1], float(sys.argv[2]), sys.argv[3]
    guardar(tema(nombre, seg), ruta)
    print("->", ruta)
