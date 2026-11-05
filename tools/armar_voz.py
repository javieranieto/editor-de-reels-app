"""Arma la voz limpia de una grabacion con varias tomas: toma los tramos de edl.json, ajusta cada borde
al silencio medido (no a los tiempos de Whisper, que se adelantan) y los une con 0.35 s de ruido del
propio cuarto (no silencio digital, que se nota). Sale voz_editada.wav. Luego se transcribe para revisar.
    python tools/armar_voz.py "<carpeta con voz.mp3 y edl.json>"
edl.json: {"tramos": [[ini, fin], [ini, fin, "fijo"], ...]} en segundos de la grabacion; cada tramo es una toma buena.
Antes de escribirlo: transcribir con Whisper por palabra y medir la energia (los tiempos de Whisper se adelantan
y esconden arranques falsos: "No le preguntes algo a..." + pausa + la frase entera). Despues: transcribir
voz_editada.wav y leerla de corrido contra el guion.
Un tramo [a, b, "fijo"] no mueve su inicio: sirve cuando la toma anterior termina pegada.
[a, b, "fijo"|"", "fin"] tampoco mueve su final: cuando la frase siguiente arranca pegada.
["otra", "ruta.mp3"]: mete la frase de otra persona (cliente) con otra voz, a su mismo nivel; sale otras_voces.json.
"""
import json, os, subprocess, sys
import numpy as np

SR = 48000
carpeta = sys.argv[1]
edl = json.load(open(os.path.join(carpeta, "edl.json"), encoding="utf-8"))
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(carpeta, "voz.mp3"), "-ac", "1", "-ar", str(SR),
                      "-f", "f32le", "-"], capture_output=True, check=True).stdout
x = np.frombuffer(raw, dtype=np.float32).copy()
win = SR // 20
db = np.array([20 * np.log10(np.sqrt(np.mean(x[i:i + win] ** 2)) + 1e-9) for i in range(0, len(x) - win, win)])
piso = float(np.percentile(db, 10))
umbral = piso + 8
fr = lambda t: int(t * 20)

def callado(i):
    return all(0 <= j < len(db) and db[j] < umbral for j in range(i, i + 3))

def ajustar(a, b, fijo=False, fin_fijo=False):
    i = fr(a)
    for _ in range(0 if fijo else 8):           # hasta 0.4 s hacia atras, hasta encontrar silencio
        if callado(i - 3): break
        i -= 1
    j = fr(b)
    for _ in range(0 if fin_fijo else 8):
        if callado(j): break
        j += 1
    return i / 20, j / 20

# ruido del cuarto: la ventana de 0.35 s mas callada
k = int(np.argmin(np.convolve(db, np.ones(7), "valid")))
ruido = x[k * win:(k + 7) * win]
fade = int(0.015 * SR)
partes, log, otras = [], [], []

def nivel_voz(z):                       # mediana de la energia de los tramos con voz (dB)
    d = np.array([20 * np.log10(np.sqrt(np.mean(z[i:i + win] ** 2)) + 1e-9) for i in range(0, len(z) - win, win)])
    return float(np.median(d[d > np.percentile(d, 40)]))

def otra_voz(ruta):
    """["otra", "ruta.mp3"]: la frase de OTRA persona (cliente, duena...) con otra voz de ElevenLabs, en medio de
    la suya. Se recorta su silencio y se iguala su nivel al de la voz principal."""
    z = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(carpeta, ruta), "-ac", "1", "-ar",
                                      str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout, dtype=np.float32).copy()
    d = np.array([20 * np.log10(np.sqrt(np.mean(z[i:i + win] ** 2)) + 1e-9) for i in range(0, len(z) - win, win)])
    hay = np.where(d > d.max() - 35)[0]
    z = z[max(0, hay[0] - 2) * win:(hay[-1] + 3) * win]
    z *= 10 ** ((nivel_voz(x) - nivel_voz(z)) / 20)
    return z

for n, t in enumerate(edl["tramos"]):
    if t[0] == "otra":
        seg = otra_voz(t[1]); seg[:fade] *= np.linspace(0, 1, fade); seg[-fade:] *= np.linspace(1, 0, fade)
        if n: partes.append(ruido[:len(ruido) // 2])
        otras.append((sum(len(p) for p in partes) / SR, len(seg) / SR, t[1]))
        partes.append(seg); partes.append(ruido[:len(ruido) // 2])
        log.append(f"  otra voz: {t[1]}  {len(seg)/SR:.2f} s"); continue
    a, b = t[0], t[1]
    a2, b2 = ajustar(a, b, len(t) > 2 and t[2] == "fijo", len(t) > 3 and t[3] == "fin")  # [a, b, "fijo"]: el inicio ya cae en silencio medido, no se mueve
    seg = x[int(a2 * SR):int(b2 * SR)].copy()
    seg[:fade] *= np.linspace(0, 1, fade); seg[-fade:] *= np.linspace(1, 0, fade)
    if n: partes.append(ruido)
    partes.append(seg)
    log.append(f"{a:6.2f}-{b:6.2f} -> {a2:6.2f}-{b2:6.2f}")
y = np.concatenate(partes)
out = os.path.join(carpeta, "voz_editada.wav")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", out],
               input=y.astype(np.float32).tobytes(), check=True)
json.dump([{"ini": round(i, 2), "fin": round(i + d, 2), "archivo": r} for i, d, r in otras],
          open(os.path.join(carpeta, "otras_voces.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"piso {piso:.0f} dB, umbral {umbral:.0f} dB"); print("\n".join(log)); print(f"-> {out}  {len(y)/SR:.2f} s")
