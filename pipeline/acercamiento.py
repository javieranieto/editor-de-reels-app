"""Acercamiento de golpe en mitad de una toma, centrado en la cara.

Es el zoom seco (escala fija, lo que el usuario aprobo) pero SIN necesitar un
corte: en la palabra, la camara "salta" 15-30% mas cerca en 5 cuadros con un
desenfoque de movimiento que vende el salto, se queda ahi, y en la siguiente
palabra marcada vuelve de golpe (o salta otra vez).

Por que no los keyframes de CapCut: el desenfoque de movimiento no se puede
poner con keyframes, y es lo que hace que se lea como CAMARA y no como efecto
(en agosto rechazo las animaciones de zoom de CapCut: "se siente como efecto,
no como camara"). Y el centro sale de la CARA, no del centro del cuadro.

Sale un .mp4 del tramo, sin audio, que en CapCut va en la pista de encima del
video como un b-roll (con su audio el original sigue sonando abajo).

"""
import os
import subprocess
import sys

import cv2
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
CARAS = os.path.join(AQUI, "..", "recursos", "modelos", "face_detection_yunet_2023mar.onnx")

CUADROS_GOLPE = 5     # lo que dura el salto: 5 cuadros a 30 fps = 0.17 s
MUESTRAS_BLUR = 8     # copias que se promedian en el cuadro del salto
OJOS = 0.40           # en el cuadro acercado, los ojos quedan al 40% de arriba (tercios)


def _suave(t):
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 3


def _medidas(video):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "stream=width,height,r_frame_rate", "-of", "csv=p=0", video],
                       capture_output=True, text=True, check=True)
    w, h, fps = r.stdout.strip().split(",")[:3]
    num, den = fps.split("/")
    return int(w), int(h), float(num) / float(den), fps


def _leer(video, ini, fin, W, H):
    corte = (["-ss", "%.3f" % ini] if ini is not None else []) + (["-to", "%.3f" % fin] if fin is not None else [])
    p = subprocess.Popen(["ffmpeg", "-v", "error"] + corte + ["-i", video, "-an", "-f", "rawvideo",
                          "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    tam = W * H * 3
    while True:
        b = p.stdout.read(tam)
        if len(b) < tam:
            break
        yield np.frombuffer(b, np.uint8).reshape(H, W, 3)
    p.wait()


def _seguir_cara(cuadros, W, H):
    """Centro de la cara (x, y de los ojos) en cada cuadro, suavizado para que el
    encuadre no tiemble. Si en un cuadro no hay cara, se queda la anterior."""
    det = cv2.FaceDetectorYN.create(CARAS, "", (W // 4, H // 4), 0.6, 0.3, 50)
    centros, ultimo = [], (W / 2, H * 0.35)
    for i, c in enumerate(cuadros):
        if i % 3 == 0:
            _, caras = det.detect(cv2.resize(c, (W // 4, H // 4)))
            if caras is not None and len(caras):
                f = max(caras, key=lambda r: r[2] * r[3])      # la cara mas grande
                ojos_x = (f[4] + f[6]) / 2 * 4
                ojos_y = (f[5] + f[7]) / 2 * 4
                ultimo = (ojos_x, ojos_y)
        centros.append(ultimo)
    # suavizado de ida y vuelta (sin retraso)
    c = np.array(centros, np.float32)
    for _ in range(2):
        for i in range(1, len(c)):
            c[i] = c[i - 1] * 0.85 + c[i] * 0.15
        for i in range(len(c) - 2, -1, -1):
            c[i] = c[i + 1] * 0.85 + c[i] * 0.15
    return c


def _encuadrar(cuadro, escala, cx, cy, W, H):
    """El cuadro acercado `escala` veces, con los ojos en (cx, cy) llevados a la
    vertical OJOS, sin salirse de la imagen."""
    if escala <= 1.0001:
        return cuadro
    w, h = W / escala, H / escala
    x0 = min(max(cx - w / 2, 0), W - w)
    y0 = min(max(cy - h * OJOS, 0), H - h)
    M = np.float32([[escala, 0, -x0 * escala], [0, escala, -y0 * escala]])
    return cv2.warpAffine(cuadro, M, (W, H), flags=cv2.INTER_LINEAR)


def acercar(video, destino, golpes, ini=None, fin=None):
    """Escribe en `destino` (.mp4, sin audio) el tramo con los golpes de acercamiento.

    golpes : [(segundo, escala)] en segundos DEL TRAMO. En cada segundo la camara salta a
             esa escala (1.0 = vuelve a abierto). Ej.: [(2.46, 1.15), (3.16, 1.0), (3.46, 1.28)]
             Las escalas siguen la jerarquia del zoom seco: leve 1.12-1.18, fuerte 1.22-1.30.
    """
    W, H, fps, fps_txt = _medidas(video)
    golpes = sorted(golpes)
    for t, s in golpes:
        if not 1.0 <= s <= 1.36:
            sys.exit("Escala %.2f fuera de rango (1.00-1.36): mas alla corta la cabeza" % s)
    cuadros = list(_leer(video, ini, fin, W, H))
    if not cuadros:
        sys.exit("No se pudo leer el tramo")
    centros = _seguir_cara(cuadros, W, H)

    # escala de cada cuadro: salto con ease-out de CUADROS_GOLPE cuadros
    escala = np.ones(len(cuadros), np.float32)
    actual = 1.0
    for t, s in golpes:
        k0 = int(round(t * fps))
        for k in range(k0, len(cuadros)):
            avance = _suave((k - k0 + 1) / CUADROS_GOLPE)
            escala[k] = actual + (s - actual) * avance
        actual = s

    esc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24",
                            "-s", "%dx%d" % (W, H), "-r", fps_txt, "-i", "-", "-c:v", "libx264",
                            "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p", destino],
                           stdin=subprocess.PIPE)
    for k, c in enumerate(cuadros):
        cx, cy = centros[k]
        antes = escala[k - 1] if k else escala[k]
        if abs(escala[k] - antes) > 0.004:
            # cuadro de salto: se promedian copias entre la escala de antes y la de ahora,
            # que es el rastro que deja una camara que se mueve rapido
            acum = np.zeros((H, W, 3), np.float32)
            for s in np.linspace(antes, escala[k], MUESTRAS_BLUR):
                acum += _encuadrar(c, float(s), cx, cy, W, H)
            out = (acum / MUESTRAS_BLUR).astype(np.uint8)
        else:
            out = _encuadrar(c, float(escala[k]), cx, cy, W, H)
        esc.stdin.write(out.tobytes())
    esc.stdin.close()
    if esc.wait() != 0:
        sys.exit("No se pudo escribir %s" % destino)
    return len(cuadros)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Acercamiento de golpe centrado en la cara (.mp4 para CapCut)")
    p.add_argument("video")
    p.add_argument("--salida", required=True)
    p.add_argument("--ini", type=float)
    p.add_argument("--fin", type=float)
    p.add_argument("--golpe", action="append", required=True, metavar="SEG:ESCALA",
                   help="segundo del tramo y escala, ej. 2.46:1.15 (1.0 = vuelve). Se repite.")
    a = p.parse_args()
    golpes = [tuple(float(x) for x in g.split(":")) for g in a.golpe]
    n = acercar(a.video, a.salida, golpes, a.ini, a.fin)
    print("%s: %d cuadros" % (a.salida, n))


# --- corte con zoom (transicion entre dos tomas) -----------------------------------

def _girar_escalar(cuadro, s, ang, W, H, cy):
    M = cv2.getRotationMatrix2D((W / 2, cy), ang, s)
    return cv2.warpAffine(cuadro, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def tunel(video_a, a_fin, video_b, b_ini, destino, antes=0.30, despues=0.40):
    """La transicion entre dos tomas, como un tunel: los ultimos `antes` s de la toma A
    aceleran hacia el pecho con desenfoque y un giro corto; corte; la toma B entra muy
    acercada y desenfocada y frena hasta su encuadre en `despues` s.

    Sale un .mp4 de antes+despues s que en CapCut va como b-roll EN el corte:
    de (corte - antes) a (corte + despues).
    Estado: aprobado 28-oct ("me gustaron todos").
    """
    W, H, fps, fps_txt = _medidas(video_a)
    a = list(_leer(video_a, a_fin - antes, a_fin, W, H))
    b = list(_leer(video_b, b_ini, b_ini + despues, W, H))
    if not a or not b:
        sys.exit("No se pudieron leer las dos tomas del corte")
    cy = H * 0.45
    esc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24",
                            "-s", "%dx%d" % (W, H), "-r", fps_txt, "-i", "-", "-c:v", "libx264",
                            "-crf", "16", "-pix_fmt", "yuv420p", destino], stdin=subprocess.PIPE)

    def con_rastro(cuadro, s0, s1, g0, g1):
        acum = np.zeros((H, W, 3), np.float32)
        for s, g in zip(np.linspace(s0, s1, MUESTRAS_BLUR), np.linspace(g0, g1, MUESTRAS_BLUR)):
            acum += _girar_escalar(cuadro, float(s), float(g), W, H, cy)
        return (acum / MUESTRAS_BLUR).astype(np.uint8)

    na, nb = len(a), len(b)
    prev = (1.0, 0.0)
    for k, c in enumerate(a):
        u = (k + 1) / na
        s, g = 1 + 1.4 * u ** 2.5, -6 * u ** 2.5            # acelera: casi nada al principio
        esc.stdin.write(con_rastro(c, prev[0], s, prev[1], g).tobytes())
        prev = (s, g)
    prev = (3.4, 5.0)
    for k, c in enumerate(b):
        u = 1 - (1 - (k + 1) / nb) ** 3                     # frena: llega suave
        s, g = 3.4 - 2.4 * u, 5.0 * (1 - u)
        esc.stdin.write((con_rastro(c, prev[0], s, prev[1], g) if k < nb - 2 else
                         _girar_escalar(c, s, g, W, H, cy)).tobytes())
        prev = (s, g)
    esc.stdin.close()
    if esc.wait() != 0:
        sys.exit("No se pudo escribir %s" % destino)
    return na + nb
