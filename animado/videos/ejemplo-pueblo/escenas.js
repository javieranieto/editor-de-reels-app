// EJEMPLO: el pueblo de negocios, episodio "El taller" (25 s, vertical, sin voz). Es la version aprobada que
// sirve de base para una serie: arranca en la accion (la marca va en una banda arriba, no en una pantalla de
// inicio: ahi deciden si se quedan), la camara se acerca a lo que importa (la fila, el telefono, el reloj, su
// cara), la pantalla tiembla, y el cliente desesperado es una BATALLA contra su barra de PACIENCIA. Al final,
// GAME OVER -> ¿CONTINUAR? -> el consejo. Lo que cambia de episodio a episodio va en guion.json.
// La marca que lo presenta es la del negocio demo (Servicios Alcaraz): cambia "marca" y "lema" en guion.json.
//   python tools/pueblo_blips.py animado/videos/ejemplo-pueblo      (sonidos de letra, golpes, game over)
//   python tools/pueblo_musica.py animado/videos/ejemplo-pueblo     (musica de 8 bits propia, 0 creditos)
//   python animado/render.py ejemplo-pueblo --fotos 1 5 9 12 18 20 23   ->  hoja.png para revisar
//   python animado/render.py ejemplo-pueblo                              ->  MP4

configurar({
  lienzo: [1080, 1920], salida: [1080, 1920], dur: 25, fps: 30,
  fuentes: { Pix: ['fuentes/SilkscreenBold.ttf'] },
  usa: ['marcas/pueblo.js'],
});

let G = null;
VIDEO.preparar = async () => { G = await (await fetch(DIR + '/guion.json')).json(); VEL = G.vel || VEL; MARCA_CAJA = G.marca_caja || G.marca; };

const paso = t => 1 + (Math.floor(t * 8) % 2);
const mover = (t, a, b, desde, hasta) => lerp(desde, hasta, eio(clamp((t - a) / (b - a))));

// ---- camara: [segundo, centro x, centro y, zoom] en pixeles del juego; entre llaves se mueve suave ----
const CAM = [
  [0, 56, 100, 1.7], [1.9, 56, 100, 1.7], [2.4, 57, 52, 2.4], [4.5, 57, 52, 2.9],     // la fila -> el telefono
  [4.75, 80, 28, 3.0], [5.7, 80, 28, 3.0], [6.2, 48, 85, 1.0],                          // el reloj -> todo el cuarto
  [6.4, 56, 82, 1.5], [6.99, 56, 80, 1.7],                                              // el "!" del cliente
  [7.0, 48, 85.5, 1], [13.0, 48, 85.5, 1], [13.4, 56, 80, 1.3], [15.3, 56, 80, 1.4],     // batalla y regreso
  [15.45, 56, 97, 2.6], [17.0, 56, 97, 2.8], [17.05, 48, 85.5, 1], [25, 48, 85.5, 1],   // su cara, y game over
];
function camara(t) {
  let i = 0; while (i < CAM.length - 2 && t >= CAM[i + 1][0]) i++;
  const [ta, xa, ya, za] = CAM[i], [tb, xb, yb, zb] = CAM[i + 1], p = eio(clamp((t - ta) / ((tb - ta) || 1)));
  return { cx: lerp(xa, xb, p), cy: lerp(ya, yb, p), z: lerp(za, zb, p) };
}
const TIEMBLA = [[6.4, 0.35, 2.5], [10.0, 0.25, 2], [10.5, 0.25, 2], [11.1, 0.25, 2], [11.6, 0.25, 2], [17.1, 0.5, 3]];
function temblor(t) {
  for (const [a, d, amp] of TIEMBLA) if (t >= a && t < a + d) { const k = amp * (1 - (t - a) / d); return [r(k), r(k)]; }
  return [0, 0];
}
let V = null;                                   // la vista de este cuadro: recorte del mundo y escala
function vista(t) {
  const { cx, cy, z } = camara(t), [dx, dy] = temblor(t), sw = LW / z, sh = LH / z;
  const sx = clamp(cx - sw / 2, 0, LW - sw) + dx, sy = clamp(cy - sh / 2, 0, LH - sh) + dy;
  V = { sx, sy, sw, sh, k: W / sw };
}
const wx = x => (x - V.sx) * V.k, wy = y => (y - V.sy) * V.k;
function wtxt(s, x, y, o = {}) {                // texto pegado al mundo: se mueve y crece con la camara
  X.font = `700 ${(o.size ?? 40) * V.k / PESC}px Pix`; X.textAlign = o.al ?? 'center';
  X.fillStyle = o.c ?? PCOL.texto; X.fillText(s, wx(x), wy(y));
}

function big(filas, x, y, e, cambia = {}) {     // sprite grande para la batalla
  filas.forEach((f, j) => [...f].forEach((ch, i) => { if (ch !== '.') R(x + i * e, y + j * e, e, e, cambia[ch] ?? ch); }));
}
// en funcion: escenas.js se carga ANTES que marcas/pueblo.js, asi que FRENTE y compania aun no existen aqui
const CLIENTE_FRENTE = () => [...FRENTE, ...CUERPO.slice(1), PIES[0][0]];
const EMPLEADO_ESPALDA = () => [...ESPALDA, ...CUERPO.slice(1), PIES[0][0]];
function paciencia(t) {                          // 1 -> 0 en escalones, uno por golpe
  const B = G.batalla; let v = 1;
  B.golpes.forEach(gp => { v -= 0.25 * clamp((t - gp) / 0.3); });
  return clamp(v);
}

// ---- cuadro ----
escena(0, 25, t => {
  const B = G.batalla, enBatalla = t >= B.t0 && t < B.t1, go = G.game_over, fin = t >= go;
  vista(t);
  // MUNDO
  capa(gMUNDO, () => {
    g.clearRect(0, 0, LW, LH);
    if (enBatalla) {
      R(0, 0, LW, LH, 'pared'); for (let y = 0; y < 120; y += 6) R(0, y, LW, 3, 'piso1');
      R(52, 56, 40, 8, 'piso2'); R(4, 108, 44, 9, 'piso2');                              // plataformas
      const sale = clamp((t - B.huye) / 0.6), golpeado = B.golpes.some(gp => t >= gp && t < gp + 0.25);
      if (!(golpeado && Math.floor(t * 20) % 2)) big(CLIENTE_FRENTE(), 60 + sale * 60, 17 + Math.sin(t * 6) * 0.8, 2, { h: 'h1', S: 'S1' });
      big(EMPLEADO_ESPALDA(), 14, 77, 2, { h: 'c', S: 'SE' });
      // paneles: el del cliente con su barra de PACIENCIA, y el del taller
      R(3, 8, 50, 20, 'k'); R(4, 9, 48, 18, 'caja');
      const p = paciencia(t), colBarra = p > 0.5 ? '#3FBF7F' : p > 0.2 ? '#E3B23C' : PCOL.rojo;
      R(8, 21, 40, 4, 'k'); R(9, 22, 38, 2, 'piso2'); if (p > 0) R(9, 22, Math.round(38 * p), 2, colBarra);
      R(46, 92, 46, 16, 'k'); R(47, 93, 44, 14, 'caja');
      if (t >= 9.5 && t < 10.9) { R(36, 70, 9, 14, 'k'); R(37, 71, 7, 11, 'vidrio'); }  // el telefono del IGNORAR
    } else {
      taller();
      const yC2 = mover(t, 13.0, 13.4, 89, 72), yJ = mover(t, 13.0, 13.4, 107, 89);
      empleado(50, 42, t >= 13.4 && t < go);
      mostrador();
      if (t < B.swirl) persona('cliente1', 50, 72, t >= 6.4 ? 'abajo' : 'arriba');
      persona('cliente2', 50, yC2, 'arriba', t > 13.0 && t < 13.4 ? paso(t) : 0);
      persona('protagonista', 50, yJ, t >= 15.4 ? 'abajo' : 'arriba', t > 13.0 && t < 13.4 ? paso(t) : 0);
      if (t >= 2.5 && t < 4.7) { globo(63, 34); for (let i = 0; i <= Math.floor(t * 3) % 3; i++) R(66 + i * 3, 37, 2, 1, 'k'); }
      if (t >= 6.4 && t < 7.0) globo(55, 62, 7, 9);
      if (t >= 15.4 && t < go) { const k = (t * 1.6) % 1; R(62, yJ + 1 + k * 4, 2, 3, 'sudor'); }
      if (t >= 2.55 && t < 3.2) { R(61, 50, 3, 3, 'c'); }                                  // la notificacion del telefono
    }
    if (fin) { g.globalAlpha = clamp((t - go) / 0.4) * 0.85; R(0, 0, LW, LH, 'k'); g.globalAlpha = 1; }
  });
  // INTERFAZ (no se mueve con la camara)
  capa(gUI, () => {
    g.clearRect(0, 0, LW, LH);
    const d = G.dialogos.find(x => t >= x.t0 && t < x.t1);
    if (d) caja(d.quien, d.texto, d.t0, t);
    const M = G.menu;
    if (t >= M.t0 && t < M.t1) { R(52, 100, 42, 25, 'k'); R(53, 101, 40, 23, 'borde'); R(54, 102, 38, 21, 'caja'); }
    if (t < 2.4) { const a = clamp(t / 0.25) * (1 - clamp((t - 2.1) / 0.3)); g.globalAlpha = a; R(0, 0, LW, 15, 'borde'); R(0, 15, LW, 1, 'c'); g.globalAlpha = 1; }
    // remolino de entrada a la batalla, y cortina de regreso
    const remolino = (p, entra) => {
      for (let y = 0; y < LH; y += 6) for (let x = 0; x < LW; x += 6) {
        const a = (Math.atan2(y - LH / 2, x - LW / 2) / (2 * Math.PI) + 0.5 + Math.hypot(x - LW / 2, y - LH / 2) / 220) % 1;
        if (entra ? a < p : a > p) R(x, y, 6, 6, 'k');
      }
    };
    if (t >= B.swirl && t < B.t0) remolino(clamp((t - B.swirl) / 0.55), true);
    if (t >= B.t1 && t < B.t1 + 0.4) remolino(clamp((t - B.t1) / 0.4), false);
    if (t >= G.consejo) { R(0, 0, LW, LH, 'borde'); R(6, 20, LW - 12, 104, 'k'); R(7, 21, LW - 14, 102, 'caja'); }
  });

  // al lienzo, en orden: el mundo con la camara, sus textos, y la interfaz encima (la cortina tapa el letrero)
  PESC = W / LW;
  X.imageSmoothingEnabled = false; X.drawImage(LO, V.sx, V.sy, V.sw, V.sh, 0, 0, W, H); X.imageSmoothingEnabled = true;
  // textos del mundo
  if (!enBatalla && t < G.consejo && !fin) {
    wtxt('TALLER', 48, 10.6, { size: 52, c: '#FFFFFF' });
    wtxt(`9:${String(Math.round(mover(t, 4.8, 5.7, 0, 40))).padStart(2, '0')}`, 80, 30.6, { size: 36 });
    if (t >= 6.4 && t < 7.0) wtxt('!', 58.5, 69.5, { size: 70, c: PCOL.rojo });
    const yJ = mover(t, 13.0, 13.4, 107, 89);
    if (V.k / PESC < 1.45) {                                   // la etiqueta, solo en planos abiertos (cerca se cortaba)
      const s = V.k / PESC; X.font = `700 ${34 * s}px Pix`; const w = X.measureText('TÚ ▶').width + 22 * s;
      const cx = wx(34), by = wy(yJ + 10); X.fillStyle = PCOL.borde; X.fillRect(cx - w / 2, by - 40 * s, w, 40 * s);
      X.fillStyle = PCOL.c; X.fillRect(cx - w / 2, by - 5 * s, w, 5 * s); X.fillStyle = '#FFFFFF'; X.textAlign = 'center'; X.fillText('TÚ ▶', cx, by - 11 * s);
    }
  }
  X.imageSmoothingEnabled = false; X.drawImage(UI, 0, 0, W, LH * PESC); X.imageSmoothingEnabled = true;
  if (enBatalla) {
    ptxt('CLIENTE', 6, 15, { size: 34 }); ptxt('DESESPERADO', 6, 20, { size: 30 });
    ptxt('PACIENCIA', 30, 15, { size: 22, c: PCOL.paredO });
    ptxt('EL TALLER', 50, 99.5, { size: 34 }); ptxt('Nv. 1', 50, 105, { size: 28, c: PCOL.paredO });
  }
  // interfaz: banda de marca, cajita, menu
  if (t < 2.4) {
    const a = clamp(t / 0.25) * (1 - clamp((t - 2.1) / 0.3));
    ptxt(G.marca + ' presenta', 48, 7, { al: 'center', size: 34, c: PCOL.c, a });
    ptxt(G.serie, 48, 12.4, { al: 'center', size: 26, c: '#FFFFFF', a });
  }
  const d = G.dialogos.find(x => t >= x.t0 && t < x.t1);
  if (d) cajaTexto(d.quien, d.texto, d.t0, t);
  const M = G.menu;
  if (t >= M.t0 && t < M.t1) {
    M.opciones.forEach((o, i) => ptxt(o, 62, 110 + i * 9, { size: 40 }));
    ptxt('▶', 56, t >= M.cambia ? 119 : 110, { size: 40, c: PCOL.c });
  }
  // GAME OVER, CONTINUAR y el consejo
  const C = G.continuar;
  if (fin && t < C.t0) {
    const a = clamp((t - go - 0.2) / 0.3);
    ptxt('GAME OVER', 48, 66, { al: 'center', size: 120, c: PCOL.c, a });
    ptxt('CLIENTE PERDIDO', 48, 80, { al: 'center', size: 58, c: '#FFFFFF', a: clamp((t - go - 0.8) / 0.3) });
    ptxt('se fue con la', 48, 96, { al: 'center', size: 46, c: PCOL.pared, a: clamp((t - go - 1.4) / 0.3) });
    ptxt('competencia', 48, 105, { al: 'center', size: 46, c: PCOL.pared, a: clamp((t - go - 1.4) / 0.3) });
  }
  if (t >= C.t0 && t < G.consejo) {
    ptxt('¿CONTINUAR?', 48, 70, { al: 'center', size: 96, c: '#FFFFFF' });
    const enSi = t >= C.cambia, parpadea = t >= C.elige && Math.floor(t * 10) % 2;
    ptxt('SÍ', 38, 92, { al: 'center', size: 70, c: enSi ? PCOL.c : PCOL.paredO, a: parpadea ? 0.3 : 1 });
    ptxt('NO', 62, 92, { al: 'center', size: 70, c: enSi ? PCOL.paredO : PCOL.c });
    ptxt('▶', enSi ? 28 : 52, 92, { al: 'center', size: 60, c: PCOL.c });
  }
  if (t >= G.consejo) {
    const a = clamp((t - G.consejo) / 0.3);
    ptxt('CONSEJO', 48, 36, { al: 'center', size: 80, c: PCOL.c, a });
    ['Si hay fila,', 'dile cuánto', 'falta en', '1 minuto.'].forEach((l, i) =>
      ptxt(l, 48, 56 + i * 13, { al: 'center', size: 62, a: clamp((t - G.consejo - 0.4 - i * 0.3) / 0.3) }));
    ptxt(G.marca, 48, 142, { al: 'center', size: 52, c: '#FFFFFF', a: clamp((t - G.consejo - 1.8) / 0.4) });
    ptxt(G.lema, 48, 152, { al: 'center', size: 36, c: PCOL.paredO, a: clamp((t - G.consejo - 2.0) / 0.4) });
  }
});
