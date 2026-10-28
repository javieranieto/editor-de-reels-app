"""Recorte de la persona: un .mov con alfa donde solo quedas tu.

Es la base de los efectos "por detras de mi" (letras de vidrio, portada de
revista, cosas que pasan atras): en CapCut van tres pistas, de abajo arriba,

    1. el video original
    2. lo que va detras (letras, tarjetas, graficas)
    3. este .mov: tu, sin fondo, tapando lo de la pista 2

Por que aqui y no en CapCut: la regla dura 11. El recorte de CapCut
(`matting.flag = 1`) no se calcula al abrir un draft que no armo el, asi que
la mascara se calcula aqui y entra como material con alfa.

El modelo es Robust Video Matting (github.com/PeterL1n/RobustVideoMatting,
GPL-3.0). Es RECURRENTE: cada cuadro usa la memoria del anterior, por eso no
parpadea como un recorte foto por foto. El archivo no va al repo (pesa 15 MB y
su licencia no es la nuestra): si falta, `MODELO_URL` dice de donde bajarlo.

Formato de salida: ProRes 4444 con alfa, del mismo tamano y cuadros por segundo
que el video, sin audio. NO es el qtrle/argb de los adornos y el motion, y es a
proposito: qtrle comprime bien colores planos y muy mal a una persona. Medido
el 27-oct sobre 3 s de un video hablado: qtrle 589 MB, ProRes 4444 199 MB, y
ProRes con el fondo puesto en negro 124 MB. Por eso:
  - donde el alfa es cero se escribe negro (nadie lo ve, y el ruido del fondo
    era lo que pesaba);
  - se recorta SOLO el tramo del efecto (ini/fin), no el video entero: ~40 MB
    por segundo.
✅ CapCut SI lee el alfa del ProRes 4444 (probado por Javier el 27-oct con 3 pistas).
🔑 El color se guarda PREMULTIPLICADO (color*alfa): CapCut lo lee asi. Guardado puro, el borde
salia con un filito claro en CapCut que en ffmpeg no se veia (27-oct). Para mirar una muestra
con ffmpeg hay que "desmultiplicar" (unpremultiply), como hace prueba().
"""
import os
import subprocess
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
MODELO = os.path.join(AQUI, "..", "recursos", "modelos", "rvm_mobilenetv3_fp32.onnx")
MODELO_URL = ("https://github.com/PeterL1n/RobustVideoMatting/releases/download/"
              "v1.0.0/rvm_mobilenetv3_fp32.onnx")

# El modelo trabaja a esta fraccion del tamano real y luego afina el borde a
# tamano completo. 0.25 es lo que recomiendan sus autores para 1080p con la
# persona ocupando buena parte del cuadro (un video hablado).
RATIO = 0.25


def _medidas(video):
    """(ancho, alto, fps) del video, leidos con ffprobe."""
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "stream=width,height,r_frame_rate",
                        "-of", "csv=p=0", video], capture_output=True, text=True, check=True)
    w, h, fps = r.stdout.strip().split(",")[:3]
    num, den = fps.split("/")
    return int(w), int(h), float(num) / float(den), fps


def _sesion():
    import onnxruntime as ort
    if not os.path.exists(MODELO):
        # se baja la primera vez de su fuente original (no va en el repo: 15 MB, licencia GPL)
        import urllib.request
        print("  recorte: bajando el modelo (15 MB, una sola vez) de %s" % MODELO_URL, flush=True)
        os.makedirs(os.path.dirname(MODELO), exist_ok=True)
        urllib.request.urlretrieve(MODELO_URL, MODELO + ".tmp")
        if os.path.getsize(MODELO + ".tmp") < 10_000_000:
            os.remove(MODELO + ".tmp")
            sys.exit("No se pudo bajar el modelo de recorte. Bajalo a mano de %s a %s" % (MODELO_URL, MODELO))
        os.replace(MODELO + ".tmp", MODELO)
    return ort.InferenceSession(MODELO, providers=["CPUExecutionProvider"])


def capas(video, ini=None, fin=None, ratio=RATIO):
    """Cuadro por cuadro: (original RGB, color de la persona RGB, alfa 0-255), todo uint8.

    Es lo que usan recortar() y los efectos que necesitan a la persona Y al fondo
    (pipeline/vertigo.py). El modelo es recurrente: hay que pasarle los cuadros seguidos.
    """
    W, H, fps, _ = _medidas(video)
    sesion = _sesion()
    corte = []
    if ini is not None:
        corte += ["-ss", "%.3f" % ini]
    if fin is not None:
        corte += ["-to", "%.3f" % fin]
    leer = subprocess.Popen(["ffmpeg", "-v", "error"] + corte + ["-i", video, "-an",
                             "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    memoria = [np.zeros((1, 1, 1, 1), np.float32)] * 4
    paso = np.array([ratio], np.float32)
    tam = W * H * 3
    while True:
        crudo = leer.stdout.read(tam)
        if len(crudo) < tam:
            break
        cuadro = np.frombuffer(crudo, np.uint8).reshape(H, W, 3)
        src = cuadro.transpose(2, 0, 1)[None].astype(np.float32) / 255.0
        fgr, pha, *memoria = sesion.run(None, {"src": src, "r1i": memoria[0], "r2i": memoria[1],
                                               "r3i": memoria[2], "r4i": memoria[3],
                                               "downsample_ratio": paso})
        # El color sale del modelo (fgr) y no del cuadro original: ya viene
        # limpio en el borde, sin el halo del fondo pegado al pelo.
        color = (fgr[0].transpose(1, 2, 0) * 255).clip(0, 255).astype(np.uint8)
        alfa = (pha[0, 0] * 255).clip(0, 255).astype(np.uint8)
        yield cuadro, color, alfa
    leer.wait()


def recortar(video, destino, ini=None, fin=None, ratio=RATIO):
    """Escribe en `destino` (.mov) a la persona del video sin fondo.

    ini / fin en segundos del video (None = desde el inicio / hasta el final).
    Devuelve el numero de cuadros escritos. Verifica el alfa al terminar.
    """
    W, H, fps, fps_txt = _medidas(video)
    escribir = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba",
                                 "-s", "%dx%d" % (W, H), "-r", fps_txt, "-i", "-",
                                 "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le",
                                 destino], stdin=subprocess.PIPE)
    n = 0
    for _, color, alfa in capas(video, ini, fin, ratio):
        # CapCut lee el alfa del ProRes como PREMULTIPLICADO: el color ya va mezclado
        # con la transparencia. Guardado "puro", el borde le salia con un filito claro
        # (probado por Javier en CapCut el 27-oct). Esto ademas deja en negro el fondo.
        color = (color.astype(np.uint16) * alfa[..., None] // 255).astype(np.uint8)
        escribir.stdin.write(np.dstack([color, alfa]).tobytes())
        n += 1
        if n % 60 == 0:
            print("  recorte: %d cuadros (%.1f s)" % (n, n / fps), flush=True)
    escribir.stdin.close()
    if escribir.wait() != 0 or n == 0:
        sys.exit("El recorte no se pudo escribir (%d cuadros leidos)" % n)
    _verificar(destino, n)
    return n


def _verificar(destino, n):
    """Un recorte bueno tiene a alguien (alfa alto en el centro) y tiene fondo
    quitado (alfa en cero en buena parte). Un .mov todo opaco o todo vacio es un
    archivo perfectamente valido, por eso se mide."""
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", destino, "-vf",
                        "select='not(mod(n\\,15))',alphaextract,scale=108:192",
                        "-vsync", "0", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                       capture_output=True, check=True)
    a = np.frombuffer(r.stdout, np.uint8).reshape(-1, 192, 108) / 255.0
    persona = a[:, 60:150, 34:74].mean()      # el centro, donde va el pecho
    fondo = (a < 0.05).mean()                 # cuanto quedo transparente
    print("  recorte: %d cuadros | persona %.0f%% | fondo quitado %.0f%%" % (n, persona * 100, fondo * 100))
    if persona < 0.5 or fondo < 0.2:
        sys.exit("El recorte no se ve bien (persona %.0f%%, fondo %.0f%%): revisa el video" % (persona * 100, fondo * 100))


def prueba(video, recorte, palabra, destino, ini=None, fin=None):
    """Vista previa del efecto, solo para mirarla: el video, una palabra grande
    detras y el recorte encima. NO es lo que va a CapCut (alla van las tres
    pistas separadas); sirve para comprobar que la palabra de verdad queda atras."""
    corte = []
    if ini is not None:
        corte += ["-ss", "%.3f" % ini]
    if fin is not None:
        corte += ["-to", "%.3f" % fin]
    fuente = os.path.join(AQUI, "..", "recursos", "fuentes", "Poppins-Bold.ttf")
    fuente = fuente.replace("\\", "/").replace(":", "\\:")
    texto = ("drawtext=fontfile='%s':text='%s':fontsize=330:fontcolor=white@0.92:"
             "x=(w-text_w)/2:y=h*0.20" % (fuente, palabra))
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + corte + ["-i", video, "-i", recorte,
                    "-filter_complex", "[0:v]%s[fondo];[1:v]format=yuva444p,unpremultiply=inplace=1[p];[fondo][p]overlay=0:0:shortest=1[v]" % texto,
                    "-map", "[v]", "-map", "0:a?", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", destino], check=True)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Recorta a la persona del video (.mov con alfa para CapCut)")
    p.add_argument("video")
    p.add_argument("--salida", help="ruta del .mov (por omision, junto al video)")
    p.add_argument("--ini", type=float)
    p.add_argument("--fin", type=float)
    p.add_argument("--prueba", metavar="PALABRA", help="ademas, arma un mp4 de muestra con esa palabra detras")
    a = p.parse_args()
    base = os.path.splitext(a.video)[0]
    salida = a.salida or base + " - recorte.mov"
    recortar(a.video, salida, a.ini, a.fin)
    print("Recorte:", salida)
    if a.prueba:
        muestra = base + " - prueba detras.mp4"
        prueba(a.video, salida, a.prueba, muestra, a.ini, a.fin)
        print("Muestra:", muestra)
