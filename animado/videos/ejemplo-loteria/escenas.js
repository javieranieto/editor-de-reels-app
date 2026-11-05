// EJEMPLO: "La lotería de los negocios" (20 s, vertical). Se "canta" una carta: el error del negocio (contestar
// tarde), su verso, el caso y "¡LOTERÍA!" de la competencia. Se usa el FORMATO de la lotería (carta numerada,
// dibujo, nombre, verso); el dibujo es propio, no de las cartas tradicionales, que tienen dueño.
//   python animado/render.py ejemplo-loteria

configurar({
  lienzo: [1080, 1920], salida: [1080, 1920], dur: 20, fps: 30,
  fuentes: { Mont: ['fuentes/Montserrat-Bold.ttf'], MontX: ['fuentes/Montserrat-ExtraBold.ttf'], MontB: ['fuentes/Montserrat-Black.ttf'] },
  usa: ['marcas/marca_ejemplo.js'],
});
// Con ?narrado los tiempos salen de la voz (assets/tiempos.json, tools/narrar.py); sin el, los de la version sin voz.
let TN = { carta: 1.5, verso1: 3.0, verso2: 4.0, verso3: 5.0, caso: 7.0, n1: 7.8, n2: 8.3, n3: 8.8, sellos: 10.4, tabla: 12.6, grito: 14.2, consejo: 16.2 };
VIDEO.preparar = async () => {
  await VIDEO.preparar2();
  if (new URLSearchParams(location.search).has('narrado')) { TN = { ...TN, ...(await (await fetch(DIR + '/assets/tiempos.json')).json()) }; VIDEO.dur = TN.dur; }
};

const ap = (t, a, d = 0.3) => clamp((t - a) / d);               // aparece
function papelPicado(t) {                                         // banderitas de fiesta arriba
  const cols = [MK.acento, MK.blanco, MK.ambar, MK.acento, MK.blanco];
  for (let i = 0; i < 9; i++) {
    const x = i * 125 - 20, sway = Math.sin(t * 3 + i) * 6;
    X.fillStyle = cols[i % 5]; X.beginPath(); X.moveTo(x, 40); X.lineTo(x + 115, 40); X.lineTo(x + 115, 150 + sway);
    for (let k = 4; k >= 0; k--) X.lineTo(x + k * 23 + 11, 150 + sway - (k % 2 ? 0 : 24));
    X.lineTo(x, 150 + sway); X.closePath(); X.fill();
  }
  X.strokeStyle = MK.tenue; X.lineWidth = 3; X.beginPath(); X.moveTo(0, 40); X.lineTo(W, 40); X.stroke();
}
function caracol(cx, cy, s, t) {                                  // el dibujo de la carta: un caracol con su telefono
  X.save(); X.translate(cx, cy); X.scale(s, s);
  X.fillStyle = '#9DB0C9'; X.beginPath(); X.roundRect(-170, 40, 330, 70, 35); X.fill();             // cuerpo
  X.beginPath(); X.ellipse(150, 20, 55, 70, -0.3, 0, 7); X.fill();                                  // cabeza
  X.strokeStyle = '#9DB0C9'; X.lineWidth = 14; X.lineCap = 'round';
  [[130, -40, 110, -110], [175, -35, 190, -105]].forEach(([a, b, c, d]) => { X.beginPath(); X.moveTo(a, b); X.lineTo(c, d); X.stroke(); });
  X.fillStyle = MK.tinta; [[110, -115], [190, -110]].forEach(([x, y]) => { X.beginPath(); X.arc(x, y, 13, 0, 7); X.fill(); });
  // concha en espiral
  X.fillStyle = MK.ambar; X.beginPath(); X.arc(-40, -10, 120, 0, 7); X.fill();
  X.strokeStyle = '#B9791F'; X.lineWidth = 12; X.beginPath();
  for (let a = 0; a < 5.5 * Math.PI; a += 0.1) { const r = 105 - a * 5.8; X.lineTo(-40 + Math.cos(a) * r, -10 + Math.sin(a) * r); }
  X.stroke();
  // telefono en la "mano" y "zzz"
  X.save(); X.translate(205, 55); X.rotate(-0.3); caja(-22, -45, 44, 80, 8, MK.tinta); caja(-16, -38, 32, 60, 4, '#8FC3F0'); X.restore();
  const k = (t * 0.8) % 1; at('z', 250, -60 - k * 80, { size: 40 + k * 30, c: MK.navy, a: 1 - k, f: 'MontB' });
  X.restore();
}
function carta(cx, cy, s, t, frente) {
  X.save(); X.translate(cx, cy); X.scale(s, 1);
  if (!frente) {
    caja(-310, -450, 620, 900, 30, MK.navy, MK.blanco, 14);
    for (let y = -400; y < 420; y += 70) for (let x = -260; x < 280; x += 70) { X.fillStyle = MK.acento; X.globalAlpha = 0.35; X.fillRect(x, y, 30, 30); }
    X.globalAlpha = 1; logo(0, 0, 160, true);
  } else {
    caja(-310, -450, 620, 900, 30, MK.blanco, MK.navy, 16);
    caja(-270, -410, 540, 640, 16, '#E8F7FA');
    at('23', -250, -340, { size: 70, al: 'left', f: 'MontB', c: MK.navy });
    caracol(0, -60, 1.05, t);
    at('EL QUE', 0, 300, { size: 58, f: 'MontB', c: MK.navy });
    at('CONTESTA TARDE', 0, 375, { size: 52, f: 'MontB', c: MK.navy });
  }
  X.restore();
}

escena(0, 999, t => {
  fondoMarca();
  papelPicado(t);
  // 1) titulo y la carta que voltea
  if (t < TN.caso) {
    const sube = eo(ap(t, 0.1, 0.4));
    at('LA LOTERÍA', W / 2, 270 + (1 - sube) * 60, { size: 118, f: 'MontB', c: MK.acento, a: sube, sombra: MK.hondo });
    at('DE LOS NEGOCIOS', W / 2, 350 + (1 - sube) * 60, { size: 62, a: sube });
    const p = clamp((t - TN.carta) / 0.5), escala = Math.cos(Math.PI * p);              // voltea: de reves a frente
    const ent0 = Math.min(0.5, TN.carta - 0.6), entra = back(ap(t, ent0, 0.5));
    if (t > ent0) carta(W / 2, 980, Math.max(0.02, Math.abs(escala)) * entra, t, p > 0.5);
    // el verso "cantado"
    ['¡Contesta tarde...', 'y el cliente se va', 'con el que no se tarda!'].forEach((l, i) =>
      at(l, W / 2, 1570 + i * 88, { size: 66, a: ap(t, [TN.verso1, TN.verso2, TN.verso3][i]), c: i === 2 ? MK.acento : MK.blanco }));
  }
  // 2) el caso: tres negocios, uno contesta en 2 min
  if (t >= TN.caso && t < TN.tabla) {
    at('El cliente le escribe', W / 2, 330, { size: 64, a: ap(t, TN.caso) });
    at('a 3 negocios.', W / 2, 410, { size: 64, a: ap(t, TN.caso) });
    at('¿Cuánto tardaron en contestar?', W / 2, 500, { size: 44, f: 'Mont', c: MK.acento, a: ap(t, TN.caso + 0.4) });
    const N = [['2 min', true], ['40 min', false], ['3 horas', false]];
    N.forEach(([tiempo, gana], i) => {
      const y = 600 + i * 330, a = ap(t, [TN.n1, TN.n2, TN.n3][i]);
      caja(110, y, 860, 270, 30, MK.blanco, null); X.globalAlpha = 1;
      X.save(); X.globalAlpha = a;
      at(`NEGOCIO ${'ABC'[i]}`, 170, y + 95, { size: 56, al: 'left', f: 'MontB', c: MK.navy });
      at(`en ${tiempo}`, 170, y + 180, { size: 52, al: 'left', f: 'Mont', c: MK.tinta });
      if (t >= TN.sellos) {
        const s = back(ap(t, TN.sellos + i * 0.25, 0.3));
        X.translate(790, y + 135); X.rotate(-0.12); X.scale(s * 0.95, s * 0.95);
        caja(-130, -55, 260, 110, 16, null, gana ? MK.verde : MK.rojo, 10);
        at(gana ? 'VENDIÓ' : 'PERDIÓ', 0, 20, { size: 56, f: 'MontB', c: gana ? MK.verde : MK.rojo });
      }
      X.restore();
    });
    at('Caso ilustrativo', W / 2, 1640, { size: 34, f: 'Mont', c: MK.tenue, a: ap(t, TN.caso + 0.6) });
  }
  // 3) la tabla de la competencia: ¡LOTERÍA!
  if (t >= TN.tabla && t < TN.consejo) {
    at('Mientras tanto,', W / 2, 330, { size: 64, a: ap(t, TN.tabla) });
    at('tu competencia...', W / 2, 410, { size: 64, a: ap(t, TN.tabla) });
    const sac = t > TN.grito ? r(10 * (1 - clamp((t - TN.grito) / 0.4))) : 0;
    X.save(); X.translate(sac, 0);
    caja(190, 520, 700, 820, 30, MK.blanco, MK.acento, 14);
    for (let i = 0; i < 16; i++) {
      const cx = 290 + (i % 4) * 167, cy = 640 + Math.floor(i / 4) * 190;
      caja(cx - 70, cy - 80, 140, 165, 12, '#E8F7FA', MK.tenue, 3);
      if (t > TN.tabla + 0.2 + i * (TN.grito - TN.tabla - 0.4) / 16) { X.fillStyle = '#7A4A2A'; X.beginPath(); X.ellipse(cx, cy, 30, 22, 0.4, 0, 7); X.fill(); }  // frijolito
    }
    X.restore();
    if (t > TN.grito) { const s = back(ap(t, TN.grito, 0.35)); X.save(); X.translate(W / 2, 1520); X.scale(s, s); at('¡LOTERÍA!', 0, 0, { size: 150, f: 'MontB', c: MK.ambar, borde: 18, bc: MK.hondo }); X.restore(); }
  }
  // 4) consejo y firma
  if (t >= TN.consejo) {
    caja(90, 420, 900, 820, 40, MK.blanco);
    at('CONSEJO', W / 2, 560, { size: 70, f: 'MontB', c: MK.acento, a: ap(t, TN.consejo + 0.1) });
    ['Contesta en', 'minutos,', 'no en horas.'].forEach((l, i) => at(l, W / 2, 720 + i * 110, { size: 92, f: 'MontB', c: MK.navy, a: ap(t, TN.consejo + 0.4 + i * 0.3) }));
    at('Si se te juntan los mensajes,', W / 2, 1100, { size: 44, f: 'Mont', c: MK.tinta, a: ap(t, TN.consejo + 1.5) });
    at('un sistema lo resuelve.', W / 2, 1160, { size: 44, f: 'Mont', c: MK.tinta, a: ap(t, TN.consejo + 1.5) });
    firmaMarca(ap(t, TN.consejo + 2.0), 1500);
  }
});
