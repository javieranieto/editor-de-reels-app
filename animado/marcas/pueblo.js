// El "pueblo de negocios": mundo de juego RPG en look de 16 bits (se eligio entre tres: Game Boy verde,
// Game Boy azul y este, de consola de 16 bits). Pixel art de verdad: se dibuja a 96x171
// (9:16) y se agranda sin suavizar al lienzo del video. Todo es ORIGINAL: del genero (vista desde arriba,
// cajita de dialogo, menu con flechita), nada de Pokemon ni EarthBound.
// Se carga con  configurar({ ..., usa: ['marcas/pueblo.js'] })  y fuentes Pix (SilkscreenBold, trae acentos y ñ).

const LW = 96, LH = 171;
const LO = document.createElement('canvas'); LO.width = LW; LO.height = LH;
let g = LO.getContext('2d');                    // donde dibuja R(); capa() lo cambia
// capa aparte para la interfaz (la cajita): asi la camara puede acercarse al cuarto sin agrandar la cajita
const UI = document.createElement('canvas'); UI.width = LW; UI.height = LH;
const gUI = UI.getContext('2d'), gMUNDO = g;
function capa(ctx, fn) { const antes = g; g = ctx; fn(); g = antes; }
const PCOL = {
  pared: '#D9DEE8', paredO: '#9AA6C0', piso1: '#C9CFDA', piso2: '#B5BCCB', mostr: '#C68B59', mostrF: '#8A5A3C',
  k: '#1B1B26', s: '#E2A57A', hP: '#1B1715', SP: '#324165', p: '#2E3A55', e: '#1B1B26', w: '#FFFFFF', c: '#FF6A3D',
  SE: '#3FBF7F', h1: '#6B4A2B', S1: '#C0392B', h2: '#E3B23C', S2: '#2E8B57', auto: '#FF6A3D', vidrio: '#8FC3F0',
  planta: '#3E8E41', maceta: '#B5651D', caja: '#FFFFFF', borde: '#324165', texto: '#1B1B26', m: '#7A3B2A',
  llanta: '#2B2B33', mancha: '#8E95A6', sudor: '#8FC3F0', rojo: '#E5484D',
};
const R = (x, y, w, h, c) => { g.fillStyle = PCOL[c] ?? c; g.fillRect(Math.round(x), Math.round(y), w, h); };
function psprite(filas, x, y, cambia = {}, espejo = false) {
  const n = filas[0].length;
  filas.forEach((f, j) => { if (f.length !== n) throw new Error('sprite: la fila ' + j + ' mide ' + f.length); });
  filas.forEach((f, j) => [...f].forEach((ch, i) => { if (ch !== '.') R(x + (espejo ? n - 1 - i : i), y + j, 1, 1, cambia[ch] ?? ch); }));
}

// ---- personajes (12x16). h = pelo, S = camisa. El protagonista lleva el color de TU marca: cambia PCOL.SP ----
const CUERPO = [
  '..kSSSSSSk..',
  '.kSSSSSSSSk.',
  '.ksSSSSSSsk.',
  '.ksSSSSSSsk.',
  '..kSSSSSSk..',
  '..kppppppk..',
  '..kppkkppk..',
];
const PIES = [['..kkk..kkk..'], ['..kkk...kk..'], ['...kk..kkk..']];   // quieto, paso A, paso B
const ESPALDA = ['...kkkkkk...', '..khkhhkhk..', '.khhhhhhhhk.', '.khhhhhhhhk.', '.khhhhhhhhk.', '..kshhhhsk..', '...kssssk...', '..kSSSSSSk..'];
const FRENTE = ['...kkkkkk...', '..khkhhkhk..', '.khhhhhhhhk.', '.khsssssshk.', '.ksessssesk.', '.kssssssssk.', '..kssmmssk..', '...kssssk...'];
const LADO = ['...kkkkk....', '..khkhhkhk..', '.khhhhhhhhk.', '.khhhhssssk.', '.khhhssseskk', '.khhsssssk..', '..kssssmk...', '...kssssk...'];
const PERSONAS = { protagonista: { h: 'hP', S: 'SP' }, cliente1: { h: 'h1', S: 'S1' }, cliente2: { h: 'h2', S: 'S2' } };
// mira: 'arriba' | 'abajo' | 'izq' | 'der'; paso: 0 quieto, 1/2 caminando
function persona(quien, x, y, mira = 'arriba', paso = 0) {
  const cabeza = mira === 'arriba' ? ESPALDA.slice(0, 7) : mira === 'abajo' ? FRENTE : LADO;
  const filas = mira === 'arriba' ? [...ESPALDA.slice(0, 8), ...CUERPO.slice(1)] : [...cabeza, ...CUERPO.slice(1)];
  psprite([...filas.slice(0, 15), ...PIES[paso]], x, y - (paso ? 1 : 0), PERSONAS[quien], mira === 'izq');
}
const EMPLEADO = [
  '...kkkkkk...', '..kcccccck..', '.kcccccccck.', '.kkkkkkkkkk.', '.kssssssssk.', '.kskksskksk.',
  '.kssssssssk.', '..kssmmssk..', '...kssssk...', '..kSSSSSSk..', '.kSswwwwsSk.', '.kSswwwwsSk.',
];
const EMPLEADO_VE = EMPLEADO.map((f, j) => j === 5 ? '.ksekssseks.' : j === 10 || j === 11 ? '.kSSSSSSSSk.' : f);
const empleado = (x, y, levanta) => psprite(levanta ? EMPLEADO_VE : EMPLEADO, x, y, { S: 'SE' });

// ---- el taller (sin la gente) ----
function taller() {
  R(0, 0, LW, LH, 'k');
  R(0, 0, LW, 34, 'pared'); R(0, 0, LW, 2, 'paredO'); R(0, 32, LW, 2, 'paredO');
  R(4, 6, 22, 18, 'k'); R(5, 7, 20, 16, 'vidrio'); R(15, 7, 1, 16, 'k'); R(5, 15, 20, 1, 'k');
  R(33, 3, 30, 10, 'k'); R(34, 4, 28, 8, 'c');
  R(68, 6, 24, 18, 'k'); R(69, 7, 22, 16, 'mostrF');
  [[71, 9, 2, 8], [75, 9, 2, 11], [79, 9, 2, 7], [83, 9, 2, 10], [87, 9, 2, 6]].forEach(([x, y, w, h]) => R(x, y, w, h, 'paredO'));
  for (let y = 34; y < 126; y += 8) for (let x = 0; x < LW; x += 8) { R(x, y, 8, 8, ((x + y) / 8) % 2 ? 'piso1' : 'piso2'); R(x, y, 8, 1, 'piso2'); }
  R(6, 54, 18, 5, 'mancha'); R(9, 59, 10, 2, 'mancha');
  R(2, 38, 28, 13, 'k'); R(3, 39, 26, 11, 'auto'); R(6, 41, 8, 4, 'vidrio'); R(17, 41, 8, 4, 'vidrio');
  R(4, 49, 6, 4, 'k'); R(21, 49, 6, 4, 'k');
  for (let i = 0; i < 3; i++) { R(2, 100 + i * 5, 12, 5, 'k'); R(3, 101 + i * 5, 10, 3, 'llanta'); R(6, 102 + i * 5, 4, 1, 'mancha'); }
  R(84, 110, 8, 8, 'maceta'); R(82, 100, 12, 10, 'planta'); R(85, 96, 6, 6, 'planta');
}
function mostrador() {
  R(34, 54, 60, 3, 'k'); R(34, 55, 60, 3, 'mostr'); R(34, 58, 60, 8, 'mostrF'); R(34, 66, 60, 1, 'k');
  R(78, 48, 12, 7, 'k'); R(79, 49, 10, 5, 'paredO');
}
function globo(x, y, w = 13, h = 7) { R(x, y, w, h, 'k'); R(x + 1, y + 1, w - 2, h - 2, 'caja'); }

// ---- pasar el cuadro de baja resolucion al lienzo, y escribir a resolucion final ----
let PESC = 1;
function pantalla() {
  PESC = W / LW;
  X.imageSmoothingEnabled = false; X.drawImage(LO, 0, 0, LW * PESC, LH * PESC); X.imageSmoothingEnabled = true;
}
function ptxt(s, x, y, o = {}) {           // x, y en pixeles del juego
  X.font = `700 ${o.size ?? 44}px Pix`; X.textAlign = o.al ?? 'left'; X.fillStyle = o.c ?? PCOL.texto;
  X.globalAlpha = o.a ?? 1; X.fillText(s, x * PESC, y * PESC); X.globalAlpha = 1;
}
// cajita de dialogo con el texto escribiendose a VEL letras por segundo
let VEL = 26;                                  // letras por segundo; un episodio puede cambiarlo (guion.vel)
let MARCA_CAJA = 'TU MARCA';                 // la pestaña de la cajita: de quien es el juego (el episodio lo cambia)
function caja(quien, texto, t0, t) {
  if (t < t0) return;
  R(2, 127, LW - 4, 42, 'k'); R(3, 128, LW - 6, 40, 'borde'); R(5, 130, LW - 10, 36, 'caja');
  R(5, 121, 46, 8, 'k'); R(6, 122, 44, 7, 'borde');               // pestaña con la marca (el texto en cajaTexto)
}
function cajaTexto(quien, texto, t0, t) {
  if (t < t0) return;
  const n = Math.floor((t - t0) * VEL);
  ptxt(MARCA_CAJA, 28, 127.6, { al: 'center', size: 30, c: '#FFFFFF' });
  let y = 139;
  if (quien) { ptxt(quien + ':', 8, y, { c: PCOL.borde }); y += 10; }
  let resta = n;
  for (const linea of texto.split('\n')) { ptxt(linea.slice(0, Math.max(0, resta)), 8, y); resta -= linea.length; y += 10; }
  if (n >= texto.length && Math.floor(t * 2.5) % 2) ptxt('▼', 85, 165);
}
