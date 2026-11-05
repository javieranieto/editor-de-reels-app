// EJEMPLO: "Noticiero del negocio" (20 s, vertical). Para una marca de empresa con publico de duenos de negocio:
// referencia que todos reconocen, letra grande, cifras de tiempo. Formato de noticias: cortinilla, EN VIVO,
// cintillo de ULTIMA HORA, "en el lugar de los hechos", los datos (CASO ILUSTRATIVO, no una estadistica: si
// fuera un dato real, llevaria su fuente) y la recomendacion. El noticiero es INVENTADO ("ND"), no uno real.
//   python animado/render.py ejemplo-noticiero                 -> MP4 con sonidos, sin voz
//   python tools/narrar.py animado/videos/ejemplo-noticiero    -> la voz de corrido (pon tu voz en guion.json)
//   python animado/render.py ejemplo-noticiero --param narrado=1 --audio audio_narrado.json   -> con voz

configurar({
  lienzo: [1080, 1920], salida: [1080, 1920], dur: 20, fps: 30,
  fuentes: { Mont: ['fuentes/Montserrat-Bold.ttf'], MontX: ['fuentes/Montserrat-ExtraBold.ttf'], MontB: ['fuentes/Montserrat-Black.ttf'] },
  usa: ['marcas/marca_ejemplo.js'],
});
// Tiempos de cada escena. Con ?narrado (render --param narrado=1) salen de la VOZ (assets/tiempos.json, de
// tools/narrar.py): la animacion se acomoda a la narracion de corrido. Sin el, los de la version sin voz.
let TN = { set: 1.8, lugar: 6.0, mensaje: 6.2, visto: 7.0, tres: 8.0, datos: 11.0, venta: 13.4, reco: 15.6 };
VIDEO.preparar = async () => {
  await VIDEO.preparar2();
  if (new URLSearchParams(location.search).has('narrado')) {
    TN = { ...TN, ...(await (await fetch(DIR + '/assets/tiempos.json')).json()) }; VIDEO.dur = TN.dur;
  }
};
const ap = (t, a, d = 0.3) => clamp((t - a) / d);
const CINTILLO = 'ÚLTIMA HORA  ·  Negocio local pierde clientes por contestar tarde  ·  Expertos: contestar en minutos sí vende  ·  ';

function estudio(t) {
  fondoMarca('#0a2a6b', MK.hondo);
  X.strokeStyle = 'rgba(0,188,212,0.12)'; X.lineWidth = 2;                       // rejilla de estudio
  for (let x = -((t * 40) % 90); x < W; x += 90) { X.beginPath(); X.moveTo(x, 0); X.lineTo(x, H); X.stroke(); }
  for (let y = 0; y < H; y += 90) { X.beginPath(); X.moveTo(0, y); X.lineTo(W, y); X.stroke(); }
}
function mosca(t) {                                                             // "ND" y EN VIVO arriba
  caja(40, 60, 150, 90, 14, MK.acento); at('ND', 115, 128, { size: 56, f: 'MontB', c: MK.navy });
  caja(210, 75, 210, 60, 30, MK.rojo); if (Math.floor(t * 2) % 2) { X.fillStyle = MK.blanco; X.beginPath(); X.arc(242, 105, 11, 0, 7); X.fill(); }
  at('EN VIVO', 330, 120, { size: 36, f: 'MontX' });
}
function cintillo(t) {                                                          // la franja que corre abajo
  X.fillStyle = MK.blanco; X.fillRect(0, H - 170, W, 90); X.fillStyle = MK.rojo; X.fillRect(0, H - 170, 200, 90);
  at('NOTICIAS', 100, H - 112, { size: 34, f: 'MontB' });
  X.save(); X.beginPath(); X.rect(200, H - 170, W - 200, 90); X.clip();
  const w = aw(CINTILLO, 40, 'MontX'), x0 = 200 + W - ((t * 220) % w);
  for (let k = -1; k < 2; k++) at(CINTILLO, x0 + k * w - W + 200, H - 110, { size: 40, f: 'MontX', c: MK.navy, al: 'left' });
  X.restore();
}
function rotulo(tag, titulo, t0, t) {                                           // el rotulo de abajo de la nota
  const p = eo(ap(t, t0, 0.35)), x = -W * (1 - p);
  caja(40 + x, 1440, 300, 72, 10, MK.rojo); at(tag, 190 + x, 1490, { size: 36, f: 'MontB' });
  caja(40 + x, 1512, 1000, 170, 10, MK.blanco);
  titulo.split('\n').forEach((l, i) => at(l, 70 + x, 1580 + i * 66, { size: 52, f: 'MontB', c: MK.navy, al: 'left' }));
}

escena(0, 999, t => {
  // 1) cortinilla del noticiero
  if (t < TN.set) {
    estudio(t);
    for (let i = 0; i < 4; i++) { const p = eo(ap(t, i * 0.08, 0.5)); X.fillStyle = i % 2 ? MK.acento : MK.blanco; X.fillRect(-W + p * W * 2 - i * 60, 700 + i * 60, W, 40); }
    const a = ap(t, 0.5, 0.3);
    at('NOTICIERO', W / 2, 900, { size: 130, f: 'MontB', a, sombra: MK.hondo });
    at('DEL NEGOCIO', W / 2, 1010, { size: 80, f: 'MontB', c: MK.acento, a });
    return;
  }
  estudio(t);
  // 2) la conductora en el set con la ULTIMA HORA
  if (t < TN.lugar) {
    caja(130, 300, 820, 420, 26, 'rgba(0,188,212,0.18)');                         // pantalla de fondo del set
    at('ÚLTIMA HORA', W / 2, 545, { size: 90, f: 'MontB', c: MK.acento, a: ap(t, TN.set + 0.1) });
    busto(W / 2, 1400, 1.5, { ropa: MK.navy, pelo: '#3b2a20', peinado: 'largo', cara: 'serio' });
    caja(0, 1300, W, 150, 0, '#e8eef7');                                          // el escritorio
    rotulo('ÚLTIMA HORA', 'Cliente se va porque\nnadie le contestó', 2.1, t);
  }
  // 3) en el lugar de los hechos: el mensaje sin contestar
  if (t >= TN.lugar && t < TN.datos) {
    at('EN EL LUGAR DE LOS HECHOS', W / 2, 290, { size: 46, f: 'MontX', c: MK.tenue, a: ap(t, TN.lugar) });
    telefonoMarca(W / 2, 830, 0.8, t, { nombre: 'TALLER', visto: TN.visto, msgs: [{ yo: true, t: TN.mensaje, texto: '¿Cuánto cuesta\nla afinación?' }], pie: 'Visto 10:02', pieT: TN.visto });
    if (t >= TN.tres) { const s = back(ap(t, TN.tres, 0.35)); X.save(); X.translate(W / 2, 1180); X.scale(s, s); caja(-300, -70, 600, 140, 70, MK.rojo); at('3 h sin respuesta', 0, 18, { size: 56, f: 'MontB' }); X.restore(); }
    rotulo('EN VIVO', 'El mensaje llegó a las 10:02.\nNadie contestó.', TN.lugar + 0.4, t);
  }
  // 4) los datos: quien se quedo con la venta
  if (t >= TN.datos && t < TN.reco) {
    at('LOS DATOS', W / 2, 300, { size: 80, f: 'MontB', c: MK.acento, a: ap(t, TN.datos) });
    at('¿Quién se quedó con la venta?', W / 2, 380, { size: 46, f: 'Mont', a: ap(t, TN.datos + 0.2) });
    const D = [['NEGOCIO A', '2 min', 0.18, true], ['NEGOCIO B', '40 min', 0.55, false], ['NEGOCIO C', '3 horas', 1.0, false]];
    D.forEach(([n, tiempo, largo, gana], i) => {
      const y = 520 + i * 260, p = eo(ap(t, gana && TN.dos_min ? TN.dos_min : TN.datos + 0.5 + (i - 1) * 0.4, 0.6));   // el que gano entra cuando la voz dice "dos minutos"
      at(n, 110, y, { size: 44, f: 'MontX', al: 'left' });
      caja(110, y + 30, 600 * largo * p + 20, 90, 14, gana ? MK.verde : MK.rojo);
      at(tiempo, 140, y + 95, { size: 46, f: 'MontB', al: 'left', a: p });
      if (t >= TN.venta) at(gana ? 'VENDIÓ' : 'PERDIÓ', 1000, y + 95, { size: 44, f: 'MontB', al: 'right', c: gana ? MK.verde : MK.rojo, a: ap(t, TN.venta + i * 0.2) });
    });
    at('Caso ilustrativo', W / 2, 1360, { size: 34, f: 'Mont', c: MK.tenue });
  }
  // 5) la recomendacion y la firma
  if (t >= TN.reco) {
    at('LA RECOMENDACIÓN', W / 2, 330, { size: 70, f: 'MontB', c: MK.acento, a: ap(t, TN.reco) });
    caja(90, 440, 900, 560, 36, MK.blanco);
    ['Contesta en', 'minutos,', 'no en horas.'].forEach((l, i) => at(l, W / 2, 610 + i * 120, { size: 96, f: 'MontB', c: MK.navy, a: ap(t, TN.reco + 0.3 + i * 0.3) }));
    at('Una recomendación de', W / 2, 1180, { size: 40, f: 'Mont', c: MK.tenue, a: ap(t, TN.reco + 1.6) });
    firmaMarca(ap(t, TN.reco + 1.8), 1310);
  }
  mosca(t);
  cintillo(t);
});
