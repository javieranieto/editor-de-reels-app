// Marca de EJEMPLO para animado/ (estilo plano y limpio, de empresa): es la del negocio demo, Servicios Alcaraz.
// Para tu marca, copia este archivo a marcas/<tu-marca>.js y cambia tres cosas:
//   1. MK: los colores, sacados del CSS de su sitio EN VIVO (no de memoria ni de un documento).
//   2. MARCA.nombre / MARCA.logo: si hay logo, va el ARCHIVO REAL (marcas/<tu-marca>_assets/logo.png);
//      nunca se dibuja ni se genera. Sin logo, la firma es el nombre escrito (como aqui).
//   3. Las letras: Montserrat viene incluida (OFL); si la de la marca es de pago, un parecido libre y se dice.
// Se carga con  configurar({ ..., usa: ['marcas/marca_ejemplo.js'] })  y fuentes Mont/MontX/MontB.
// Trae: fondo, cajas, texto (at/aw), un telefono con chat, bustos planos con cara y la firma.
const MK = {
  navy: '#1F3A5F', acento: '#E07A4F', papel: '#f7f5f0', tenue: '#b8c2d0', gris: '#2a3f5c', hondo: '#12233a',
  blanco: '#ffffff', tinta: '#0b1a33', rojo: '#E5484D', verde: '#2FB67C', ambar: '#F2B33D', piel: '#E2A57A',
};
const MARCA = { nombre: 'SERVICIOS ALCARAZ', lema: 'electricistas a domicilio', logo: null };   // logo: 'marcas/<tu-marca>_assets/logo.png'
const MKIMG = {};
VIDEO.preparar2 = async () => { if (MARCA.logo) MKIMG.logo = await imagen(MARCA.logo); };

function caja(x, y, w, h, r, fill, borde, grosor = 6) {
  X.beginPath(); X.roundRect(x, y, w, h, r);
  if (fill) { X.fillStyle = fill; X.fill(); }
  if (borde) { X.lineWidth = grosor; X.strokeStyle = borde; X.stroke(); }
}
// texto en Montserrat: f = 'Mont' (bold), 'MontX' (extrabold) o 'MontB' (black)
function at(s, x, y, o = {}) {
  X.save(); X.globalAlpha = o.a ?? 1;
  X.font = `${o.it ? 'italic ' : ''}${o.size ?? 60}px ${o.f ?? 'MontX'}`; X.textAlign = o.al ?? 'center'; X.textBaseline = 'alphabetic';
  if (o.ls) X.letterSpacing = o.ls + 'px';
  if (o.sombra) { X.fillStyle = o.sombra; X.fillText(s, x + 5, y + 6); }
  if (o.borde) { X.lineWidth = o.borde; X.strokeStyle = o.bc ?? MK.navy; X.lineJoin = 'round'; X.strokeText(s, x, y); }
  X.fillStyle = o.c ?? MK.blanco; X.fillText(s, x, y); X.restore();
}
function aw(s, size, f = 'MontX') { X.save(); X.font = `${size}px ${f}`; const w = X.measureText(s).width; X.restore(); return w; }
// el logo real (si la marca tiene archivo) o el nombre escrito; centrado en x
function logo(cx, cy, alto, blanco = true, a = 1) {
  const im = MKIMG.logo;
  if (im) { const w = alto * im.width / im.height; X.save(); X.globalAlpha = a; X.drawImage(im, cx - w / 2, cy - alto / 2, w, alto); X.restore(); return; }
  at(MARCA.nombre, cx, cy + alto * 0.15, { size: alto * 0.42, f: 'MontB', c: blanco ? MK.blanco : MK.navy, a });
  at(MARCA.lema, cx, cy + alto * 0.5, { size: alto * 0.2, f: 'Mont', c: MK.acento, a });
}
function fondoMarca(c1 = MK.navy, c2 = MK.hondo) {
  const gr = X.createLinearGradient(0, 0, 0, H); gr.addColorStop(0, c1); gr.addColorStop(1, c2);
  X.fillStyle = gr; X.fillRect(0, 0, W, H);
}
// telefono con chat: msgs = [{yo, texto, t}] (aparecen en su t); visto = segundo en que se pone azul
function telefonoMarca(cx, cy, s, t, o = {}) {
  X.save(); X.translate(cx, cy); X.scale(s, s);
  caja(-260, -470, 520, 940, 60, MK.tinta); caja(-236, -440, 472, 880, 40, MK.papel);
  caja(-236, -440, 472, 120, [40, 40, 0, 0], o.color ?? MK.navy);
  X.beginPath(); X.arc(-170, -380, 34, 0, 7); X.fillStyle = MK.blanco; X.fill();
  at(o.nombre ?? 'NEGOCIO', -120, -364, { size: 38, al: 'left', f: 'Mont' });
  let y = -260;
  for (const m of o.msgs ?? []) {
    if (t < m.t) continue;
    const lineas = m.texto.split('\n'), w = Math.max(...lineas.map(l => aw(l, 36, 'Mont'))) + (m.yo && o.visto !== undefined ? 130 : 60), h = 30 + lineas.length * 48;   // lugar para las ✓✓
    const x = m.yo ? 210 - w : -210;
    caja(x, y, w, h, 26, m.yo ? '#CFE8D8' : MK.blanco, m.yo ? null : MK.tenue, 3);
    lineas.forEach((l, i) => at(l, x + 30, y + 62 + i * 48, { size: 36, al: 'left', f: 'Mont', c: MK.tinta }));
    if (m.yo && o.visto !== undefined) { const c = t >= o.visto ? '#2D9CDB' : MK.tenue; palomita(x + w - 80, y + h - 24, c); palomita(x + w - 54, y + h - 24, c); }
    y += h + 30;
  }
  if (o.pie && t >= (o.pieT ?? 0)) at(o.pie, 200, y + 10, { size: 30, al: 'right', f: 'Mont', c: '#2D9CDB' });
  X.restore();
}
// persona plana (busto): pelo, piel, ropa; cara: 'feliz' | 'triste' | 'sorpresa' | 'serio'; lagrima, guino
function busto(cx, by, s, o = {}) {
  X.save(); X.translate(cx, by); X.scale(s, s);
  X.fillStyle = o.ropa ?? MK.acento; X.beginPath(); X.roundRect(-150, -170, 300, 200, [110, 110, 20, 20]); X.fill();
  X.fillStyle = o.piel ?? MK.piel; X.fillRect(-30, -200, 60, 50);
  X.beginPath(); X.ellipse(0, -300, 105, 120, 0, 0, 7); X.fill();
  X.fillStyle = o.pelo ?? '#2a1d17'; X.beginPath();
  if (o.peinado === 'largo') { X.ellipse(0, -330, 120, 110, 0, Math.PI, 0); X.fill(); X.fillRect(-120, -330, 40, 190); X.fillRect(80, -330, 40, 190); }
  else { X.ellipse(0, -360, 110, 70, 0, Math.PI * 0.95, Math.PI * 2.05); X.fill(); }
  const cara = o.cara ?? 'serio';
  X.fillStyle = MK.tinta;
  if (cara === 'sorpresa') { [-40, 40].forEach(x => { X.beginPath(); X.arc(x, -300, 14, 0, 7); X.fill(); }); X.beginPath(); X.ellipse(0, -235, 18, 24, 0, 0, 7); X.fill(); }
  else {
    [-40, 40].forEach(x => { X.beginPath(); X.ellipse(x, -300, 10, cara === 'triste' ? 7 : 12, 0, 0, 7); X.fill(); });
    X.lineWidth = 9; X.strokeStyle = MK.tinta; X.lineCap = 'round'; X.beginPath();
    if (cara === 'feliz') X.arc(0, -258, 34, 0.15 * Math.PI, 0.85 * Math.PI);
    else if (cara === 'triste') X.arc(0, -215, 34, 1.15 * Math.PI, 1.85 * Math.PI);
    else { X.moveTo(-28, -240); X.lineTo(28, -240); }
    X.stroke();
    if (cara === 'triste') { X.lineWidth = 7; X.beginPath(); X.moveTo(-62, -330); X.lineTo(-22, -346); X.moveTo(62, -330); X.lineTo(22, -346); X.stroke(); }
  }
  if (o.lagrima !== undefined) { const k = o.lagrima % 1; X.fillStyle = '#8FC3F0'; X.beginPath(); X.ellipse(-45, -280 + k * 70, 11, 16, 0, 0, 7); X.fill(); }
  X.restore();
}
function palomita(x, y, c, s = 1) {              // ✓ dibujada (no se confia en que la letra traiga el simbolo)
  X.save(); X.strokeStyle = c; X.lineWidth = 6 * s; X.lineCap = 'round'; X.lineJoin = 'round';
  X.beginPath(); X.moveTo(x, y - 8 * s); X.lineTo(x + 8 * s, y); X.lineTo(x + 22 * s, y - 18 * s); X.stroke(); X.restore();
}
function firmaMarca(a = 1, y = H - 150) {
  logo(W / 2, y, 170, true, a);
}
