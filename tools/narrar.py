"""Narracion DE CORRIDO para un video animado: la voz manda y el video se acomoda a ella.

Antes cada frase se generaba aparte y se pegaba en su escena: cada una empezaba "en frio" y
terminaba con tono de punto final, y sonaba cortada (medido en la primera prueba: «se sienten muy planas, como cortadas»).
Aqui el texto entero va en UNA llamada; ElevenLabs devuelve el segundo de cada palabra, y con las `anclas` del
guion se calcula cuando empieza cada escena. El video lee assets/tiempos.json.

    python tools/narrar.py animado/videos/ejemplo-noticiero

En guion.json:
    "narrado": {"voz": "<id>", "modelo": "eleven_v4", "estabilidad": 0.3, "velocidad": 1.0,
                "texto": "...", "cola": 2.0,
                "anclas": {"lugar": ["cliente", 1, -0.25], ...}}     # nombre: [palabra, ocurrencia, ajuste en s]
Sale assets/narrado.wav, assets/tiempos.json ({ancla: segundo, "fin_voz", "dur"}) y assets/palabras_narrado.json.
"""
import json
import os
import subprocess
import sys
import unicodedata

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from pipeline import voz_off  # noqa: E402


def limpia(p):
    p = unicodedata.normalize("NFD", p.lower())
    return "".join(c for c in p if c.isalnum() and unicodedata.category(c) != "Mn")


def main():
    carpeta = sys.argv[1]
    g = json.load(open(os.path.join(carpeta, "guion.json"), encoding="utf-8"))
    n = g["narrado"]
    destino = os.path.join(carpeta, "assets", "voz", f"narrado_{n['voz'][:6]}_{n.get('modelo', 'v2')}.mp3")
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    r = voz_off.sintetizar(n["texto"], n["voz"], destino, modelo=n.get("modelo", voz_off.MODELO),
                           velocidad=n.get("velocidad", voz_off.VELOCIDAD), estabilidad=n.get("estabilidad", voz_off.ESTABILIDAD))
    palabras = r["palabras"]
    dur_voz = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", r["archivo"]],
                                   capture_output=True, text=True).stdout)
    tiempos = {}
    for nombre, (palabra, ocurrencia, ajuste) in n["anclas"].items():
        hits = [p for p in palabras if limpia(p["word"]) == limpia(palabra)]
        if len(hits) < ocurrencia:
            raise SystemExit(f"Ancla «{nombre}»: la palabra «{palabra}» sale {len(hits)} veces, se pidio la {ocurrencia}")
        tiempos[nombre] = round(hits[ocurrencia - 1]["start"] + ajuste, 3)
    tiempos["fin_voz"] = round(dur_voz, 3)
    tiempos["dur"] = round(dur_voz + n.get("cola", 2.0), 3)
    orden = sorted(tiempos.items(), key=lambda x: x[1])
    print(f"  voz: {dur_voz:.2f} s medidos · video: {tiempos['dur']:.2f} s")
    for k, v in orden:
        print(f"    {v:6.2f}  {k}")
    a = os.path.join(carpeta, "assets")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", r["archivo"], "-ac", "1", "-ar", "44100", os.path.join(a, "narrado.wav")], check=True)
    json.dump(tiempos, open(os.path.join(a, "tiempos.json"), "w", encoding="utf-8"), indent=1)
    json.dump(palabras, open(os.path.join(a, "palabras_narrado.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print("->", os.path.join(a, "tiempos.json"))


if __name__ == "__main__":
    main()
