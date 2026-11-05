// EJEMPLO: "Corazón de mostrador", la telenovela del negocio (20 s, vertical). Parodia del género: el cliente
// escribe con ilusión, lo dejan en visto, se va con la competencia, "¡NOOO!" y "En el próximo capítulo...".
// Personajes planos de marcas/marca_ejemplo.js; nada de una telenovela real.
//   python animado/render.py ejemplo-telenovela

configurar({
  lienzo: [1080, 1920], salida: [1080, 1920], dur: 20, fps: 30,
  fuentes: { Mont: ['fuentes/Montserrat-Bold.ttf'], MontX: ['fuentes/Montserrat-ExtraBold.ttf'], MontB: ['fuentes/Montserrat-Black.ttf'],
             Serif: ['fuentes/SourceSerif4.ttf', { weight: '200 900', style: 'normal' }] },
  usa: ['marcas/marca_ejemplo.js'],
});
// Con ?narrado los tiempos salen de la voz (assets/tiempos.json, tools/narrar.py); sin el, los de la version sin voz.
let TN = { escribe: 2.2, telefono: 5.4, ella: 7.3, visto: 7.8, llora: 9.2, seva: 11.2, competencia: 11.6, nooo_escena: 13.2, nooo: 13.3, proximo: 15.9, consejo: 17.0 };
VIDEO.preparar = async () => {
  await VIDEO.preparar2();
  if (new URLSearchParams(location.search).has('narrado')) { TN = { ...TN, ...(await (await fetch(DIR + '/assets/tiempos.json')).json()) }; VIDEO.dur = TN.dur; }
};
const ap = (t, a, d = 0.3) => clamp((t - a) / d);

function drama(t, rojo = 0) {                                     // fondo de telenovela: foco de luz y vineta
  fondoMarca('#0d1f4a', MK.hondo);
  const gr = X.createRadialGradient(W / 2, 760, 80, W / 2, 760, 900);
  gr.addColorStop(0, 'rgba(0,188,212,0.22)'); gr.addColorStop(1, 'rgba(0,0,0,0.55)'); X.fillStyle = gr; X.fillRect(0, 0, W, H);
  if (rojo) { X.fillStyle = `rgba(229,72,77,${0.28 * rojo})`; X.fillRect(0, 0, W, H); }
}
function brillos(t) {
  for (let i = 0; i < 14; i++) {
    const x = (i * 197) % W, y = 200 + (i * 331) % 1300, s = 6 + 8 * Math.abs(Math.sin(t * 2 + i));
    X.fillStyle = 'rgba(255,255,255,0.8)'; X.beginPath(); X.moveTo(x, y - s * 2); X.lineTo(x + s / 2, y); X.lineTo(x, y + s * 2); X.lineTo(x - s / 2, y); X.closePath(); X.fill();
  }
}
function narra(s, y, t0, t, c = MK.blanco) {                    // la frase dramatica de abajo, en italica
  at(s, W / 2, y, { size: 62, f: 'Serif', it: true, c, a: ap(t, t0, 0.4), sombra: 'rgba(0,0,0,0.5)' });
}

escena(0, 999, t => {
  // 1) cortinilla de la telenovela
  if (t < TN.escribe) {
    drama(t); brillos(t);
    const a = eo(ap(t, 0.15, 0.6));
    at('Corazón de', W / 2, 760, { size: 110, f: 'Serif', it: true, a, sombra: 'rgba(0,0,0,0.6)' });
    at('MOSTRADOR', W / 2, 900, { size: 132, f: 'MontB', c: MK.acento, a, ls: 4, sombra: MK.hondo });
    at('una telenovela de', W / 2, 1180, { size: 40, f: 'Mont', c: MK.tenue, a: ap(t, 0.8) });
    logo(W / 2, 1290, 130, true, ap(t, 0.9));
    return;
  }
  drama(t, t >= TN.competencia && t < TN.nooo_escena ? 1 : 0);
  at('CAPÍTULO 1: EL VISTO', W / 2, 170, { size: 40, f: 'MontX', c: MK.tenue, ls: 3 });
  // 2) el cliente escribe con ilusion
  if (t < TN.telefono) {
    const z = 1 + 0.06 * (t - TN.escribe);
    X.save(); X.translate(W / 2, 1000); X.scale(z, z); X.translate(-W / 2, -1000);
    busto(W / 2, 1300, 1.6, { ropa: MK.acento, cara: 'feliz' });
    X.save(); X.translate(700, 1080); X.rotate(-0.2); caja(-60, -110, 120, 210, 18, MK.tinta); caja(-48, -96, 96, 170, 10, '#8FC3F0'); X.restore();
    X.restore();
    narra('Él le escribió', 1570, TN.escribe + 0.4, t); narra('con ilusión...', 1650, TN.escribe + 0.8, t);
  }
  // 3) el telefono: lo deja en visto (con relampago)
  if (t >= TN.telefono && t < TN.llora) {
    const z = 1 + 0.08 * (t - TN.telefono);
    telefonoMarca(W / 2, 880, 0.95 * z, t, { nombre: 'EL NEGOCIO', visto: TN.ella + 0.3, msgs: [{ yo: true, t: TN.telefono + 0.1, texto: '¿Me puede\natender hoy?' }], pie: 'Visto 10:02', pieT: TN.ella + 0.3 });
    if (t >= TN.visto && t < TN.visto + 0.3) { X.fillStyle = `rgba(255,255,255,${1 - (t - TN.visto) / 0.3})`; X.fillRect(0, 0, W, H); }
    narra('Y ella...', 1580, TN.ella, t); narra('lo dejó en VISTO.', 1665, TN.visto, t, MK.acento);
  }
  // 4) el llora... y se va con la competencia
  if (t >= TN.llora && t < TN.nooo_escena) {
    const z = 1 + 0.05 * (t - TN.llora), seVa = t >= TN.seva;
    X.save(); X.translate(W / 2, 1000); X.scale(z, z); X.translate(-W / 2, -1000);
    busto(seVa ? 360 : W / 2, 1300, 1.5, { ropa: MK.acento, cara: seVa ? 'feliz' : 'triste', lagrima: seVa ? undefined : t * 1.3 });
    X.restore();
    if (!seVa) { narra('¿Por qué', 1570, TN.llora + 0.2, t); narra('no me contestas?', 1655, TN.llora + 0.6, t); }
    else {
      telefonoMarca(790, 820, 0.55, t, { nombre: 'LA COMPETENCIA', color: MK.verde, msgs: [{ yo: true, t: TN.seva, texto: '¿Me puede\natender hoy?' }, { yo: false, t: TN.seva + 0.5, texto: '¡Claro! Lo\nesperamos.' }] });
      narra('Y se fue... con', 1570, TN.competencia - 0.6, t); narra('LA COMPETENCIA.', 1655, TN.competencia, t, MK.rojo);
    }
  }
  // 5) ella se entera: ¡NOOO!
  if (t >= TN.nooo_escena && t < TN.proximo) {
    const sac = t < TN.nooo ? 0 : r(14 * (1 - clamp((t - TN.nooo) / 0.6))), z = 1 + 0.12 * eo(ap(t, TN.nooo_escena, 1.5));
    X.save(); X.translate(W / 2 + sac, 1000 + sac); X.scale(z, z); X.translate(-W / 2, -1000);
    busto(W / 2, 1320, 1.6, { ropa: MK.ambar, pelo: '#4a2a18', peinado: 'largo', cara: 'sorpresa' });
    X.restore();
    at('¡NOOOOO!', W / 2, 520, { size: 150, f: 'MontB', c: MK.blanco, borde: 16, bc: MK.rojo, a: ap(t, TN.nooo, 0.15) });
    narra('La dueña del negocio', 1610, TN.nooo_escena + 0.2, t);
  }
  // 6) en el proximo capitulo + consejo + firma
  if (t >= TN.proximo) {
    at('EN EL PRÓXIMO CAPÍTULO:', W / 2, 420, { size: 52, f: 'MontX', c: MK.tenue, a: ap(t, TN.proximo) });
    at('¿Aprenderá a', W / 2, 560, { size: 84, f: 'Serif', it: true, a: ap(t, TN.proximo + 0.3) });
    at('contestar a tiempo?', W / 2, 660, { size: 84, f: 'Serif', it: true, a: ap(t, TN.proximo + 0.6) });
    if (t >= TN.consejo - 0.15) caja(110, 820, 860, 420, 36, MK.blanco, null);   // sin el texto, la caja sola estorbaba
    at('CONSEJO', W / 2, 920, { size: 58, f: 'MontB', c: MK.acento, a: ap(t, TN.consejo) });
    at('Contesta en minutos,', W / 2, 1040, { size: 62, f: 'MontB', c: MK.navy, a: ap(t, TN.consejo + 0.2) });
    at('no en horas.', W / 2, 1120, { size: 62, f: 'MontB', c: MK.navy, a: ap(t, TN.consejo + 0.4) });
    firmaMarca(ap(t, TN.consejo + 1.0), 1480);
  }
});
