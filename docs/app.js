/*
 * Eindexamen Oefenen: echte centrale examenvragen per onderwerp.
 * Routes (in de hash):
 *   #/                                begin: kies niveau en vak
 *   #/vak/<vak>                       onderwerpen van een vak (of ?per=examen)
 *   #/vak/<vak>/onderwerp/<id>        alle vragen over één onderwerp
 *   #/vak/<vak>/examen/<code>         alle vragen van één examen
 *   #/vraag/<vak>/<id>/<lijst>        één vraag; <lijst> is o-<onderwerp> of e-<examen> voor vorige/volgende
 */
(() => {
  const app = document.getElementById('app');
  const kruimel = document.getElementById('kruimel');
  const cache = {};
  let OVERZICHT = null;

  // ---------- voortgang (alleen in deze browser) ----------
  const SLEUTEL = 'eo-voortgang-v1';
  const lees = () => { try { return JSON.parse(localStorage.getItem(SLEUTEL)) || {}; } catch (e) { return {}; } };
  const bewaar = (id, score, max) => {
    const v = lees();
    v[id] = { s: score, m: max, t: Date.now() };
    try { localStorage.setItem(SLEUTEL, JSON.stringify(v)); } catch (e) { /* privévenster: dan niet bewaren */ }
  };

  const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const tv = t => (t === 1 ? 'tijdvak 1' : 'tijdvak 2');
  const tvKort = t => (t === 1 ? 'I' : 'II');
  const enc = encodeURIComponent;

  async function json(pad) {
    if (!cache[pad]) cache[pad] = fetch(pad).then(r => { if (!r.ok) throw new Error(pad); return r.json(); });
    return cache[pad];
  }
  const vakData = vak => json(`data/${vak}.json`);
  const vakNaam = vak => { const v = OVERZICHT.vakken[vak]; return `${v.naam} ${OVERZICHT.niveaus[v.niveau].toLowerCase()}`; };
  const onderwerp = (vak, id) => OVERZICHT.vakken[vak].domeinen.flatMap(d => d.onderwerpen).find(o => o.id === id);

  function status(id) {
    const r = lees()[id];
    if (!r) return '';
    const k = r.s === r.m ? 'goed' : r.s === 0 ? 'fout' : 'half';
    return `<span class="st ${k}">${r.s}/${r.m} p</span>`;
  }
  const gemaakt = ids => { const v = lees(); return ids.filter(i => v[i]).length; };

  function zetKruimel(delen) {
    kruimel.innerHTML = delen.map(([t, h]) => (h ? `<a href="${h}">${esc(t)}</a>` : `<span>${esc(t)}</span>`)).join('<span class="sep">/</span>');
  }
  function toon(html, titel) {
    app.innerHTML = html;
    document.title = titel ? `${titel} · Eindexamen Oefenen` : 'Eindexamen Oefenen';
    window.scrollTo(0, 0);
  }

  // ---------- begin ----------
  function begin() {
    zetKruimel([]);
    const per = { havo: [], vwo: [] };
    Object.entries(OVERZICHT.vakken).forEach(([k, v]) => per[v.niveau].push([k, v]));
    const vakKaart = ([k, v]) => {
      const n = v.domeinen.reduce((s, d) => s + d.onderwerpen.length, 0);
      const j = v.examens.map(e => e.jaar);
      return `<a class="vak kaart" href="#/vak/${k}">
        <span class="label">${OVERZICHT.niveaus[v.niveau]}</span>
        <h3>${esc(v.naam)}</h3>
        <span class="meta">${v.vragen} vragen · ${n} onderwerpen · ${v.examens.length} examens (${Math.min(...j)}–${Math.max(...j)})</span>
      </a>`;
    };
    toon(`
      <section class="held">
        <h1>Oefen eindexamenvragen per onderwerp</h1>
        <p>Alle vragen uit de centrale examens wiskunde sinds 2018, ingedeeld volgens de syllabus. Kies je vak, klik op een onderwerp en maak de vragen precies zoals ze op het examen stonden. Daarna kijk je ze na met het officiële antwoordmodel.</p>
      </section>
      <div class="niveaus">
        ${Object.entries(per).map(([niv, lijst]) => `<section class="niveau"><h2>${OVERZICHT.niveaus[niv]}</h2><div class="vakken">${lijst.map(vakKaart).join('')}</div></section>`).join('')}
      </div>
      <section class="uitleg">
        <div class="kaart"><b>1. Kies een onderwerp</b><p>Elk vak is opgedeeld in de onderwerpen uit de syllabus van het centraal examen.</p></div>
        <div class="kaart"><b>2. Maak de vraag</b><p>Je ziet de inleiding, figuren en tabellen van de opgave, precies zoals in het examen.</p></div>
        <div class="kaart"><b>3. Kijk na</b><p>Klap het antwoordmodel uit het correctievoorschrift open en geef jezelf punten.</p></div>
      </section>`);
  }

  // ---------- vak ----------
  async function vakPagina(vak, perExamen) {
    const v = OVERZICHT.vakken[vak];
    if (!v) return nietGevonden();
    const data = await vakData(vak);
    const naam = vakNaam(vak);
    zetKruimel([[OVERZICHT.niveaus[v.niveau], '#/'], [v.naam, null]]);
    const ids = data.vragen.map(q => q.id);
    const kop = `<div class="vak-kop">
        <div><span class="label">${OVERZICHT.niveaus[v.niveau]} · centraal examen</span><h1>${esc(v.naam)}</h1>
        <p>${v.vragen} vragen uit ${v.examens.length} examens · ${gemaakt(ids)} gemaakt</p></div>
        <nav class="tabs" aria-label="Weergave"><a href="#/vak/${vak}" class="${perExamen ? '' : 'aan'}">Per onderwerp</a><a href="#/vak/${vak}?per=examen" class="${perExamen ? 'aan' : ''}">Per examen</a></nav>
      </div>`;
    if (perExamen) {
      return toon(kop + `<div class="examens">${v.examens.map(e => {
        const q = data.vragen.filter(x => x.examen === e.code);
        return `<a class="examen kaart" href="#/vak/${vak}/examen/${e.code}"><b>${e.jaar} · ${tv(e.tijdvak)}</b><span>${q.length} vragen · ${gemaakt(q.map(x => x.id))} gemaakt</span></a>`;
      }).join('')}</div>`, naam);
    }
    toon(kop + v.domeinen.map(d => `<section class="domein"><h2 class="label">${esc(d.naam)}</h2><div class="onderwerpen">${d.onderwerpen.map(o => {
      const q = data.vragen.filter(x => x.onderwerp === o.id).map(x => x.id);
      const g = gemaakt(q);
      return `<a class="ow kaart" href="#/vak/${vak}/onderwerp/${o.id}">
          <h3>${esc(o.naam)} <span class="code">${esc(o.code)}</span></h3>
          <p>${esc(o.omschrijving)}</p>
          <span class="rechts"><span class="tal">${o.vragen} <small>vragen · ${o.punten} p</small></span><span class="balk" title="${g} van ${q.length} gemaakt"><i style="width:${q.length ? Math.round(100 * g / q.length) : 0}%"></i></span></span>
        </a>`;
    }).join('')}</div></section>`).join(''), naam);
  }

  // ---------- lijst van vragen ----------
  const FILTERS = { alle: () => true, recent: q => q.jaar >= 2022, ouder: q => q.jaar < 2022, open: q => !lees()[q.id] };
  let filter = 'alle';

  async function lijstPagina(vak, soort, sleutel) {
    const v = OVERZICHT.vakken[vak];
    if (!v) return nietGevonden();
    const data = await vakData(vak);
    let vragen, titel, sub, lijstId;
    if (soort === 'onderwerp') {
      const o = onderwerp(vak, sleutel);
      if (!o) return nietGevonden();
      vragen = data.vragen.filter(q => q.onderwerp === sleutel);
      titel = o.naam;
      sub = `${o.omschrijving} Syllabus ${o.code}.`;
      lijstId = `o-${sleutel}`;
    } else {
      vragen = data.vragen.filter(q => q.examen === sleutel).sort((a, b) => a.vraag - b.vraag);
      if (!vragen.length) return nietGevonden();
      titel = `Examen ${vragen[0].jaar}, ${tv(vragen[0].tijdvak)}`;
      sub = `${vragen.length} vragen · ${vragen.reduce((s, q) => s + q.punten, 0)} punten.`;
      lijstId = `e-${sleutel}`;
    }
    zetKruimel([[OVERZICHT.niveaus[v.niveau], '#/'], [v.naam, `#/vak/${vak}${soort === 'examen' ? '?per=examen' : ''}`], [soort === 'onderwerp' ? titel : `${vragen[0].jaar}-${tvKort(vragen[0].tijdvak)}`, null]]);
    const teken = () => {
      const zicht = vragen.filter(FILTERS[filter]);
      document.getElementById('vragen').innerHTML = zicht.length ? zicht.map(q => `
        <a class="vr kaart" href="#/vraag/${vak}/${enc(q.id)}/${lijstId}">
          <span class="nr">${q.vraag}</span>
          <span class="wat"><b>${esc(q.opgave || 'Opgave')}</b><span>${soort === 'onderwerp' ? `${q.jaar} ${tv(q.tijdvak)} · ` : `${esc(onderwerp(vak, q.onderwerp).naam)} · `}${q.punten} punten</span></span>
          ${status(q.id) || '<span class="st">nog niet gemaakt</span>'}
        </a>`).join('') : '<p class="leeg kaart">Geen vragen met dit filter.</p>';
      document.querySelectorAll('.filters button').forEach(b => b.classList.toggle('aan', b.dataset.f === filter));
    };
    toon(`<header class="lijst-kop"><span class="label">${esc(vakNaam(vak))}</span><h1>${esc(titel)}</h1><p>${esc(sub)}</p></header>
      <div class="filters" role="group" aria-label="Filter">
        <button data-f="alle">Alle (${vragen.length})</button>
        ${soort === 'onderwerp' ? `<button data-f="recent">2022 en later</button><button data-f="ouder">2018–2021</button>` : ''}
        <button data-f="open">Nog niet gemaakt</button>
      </div>
      <div class="vragen" id="vragen"></div>`, titel);
    app.querySelector('.filters').addEventListener('click', e => { const b = e.target.closest('button'); if (b) { filter = b.dataset.f; teken(); } });
    teken();
  }

  // ---------- één vraag ----------
  async function vraagPagina(vak, id, lijst) {
    const v = OVERZICHT.vakken[vak];
    if (!v) return nietGevonden();
    const data = await vakData(vak);
    const q = data.vragen.find(x => x.id === id);
    if (!q) return nietGevonden();
    const o = onderwerp(vak, q.onderwerp);
    // de lijst waar de leerling vandaan komt, voor vorige en volgende
    let reeks = lijst && lijst.startsWith('e-') ? data.vragen.filter(x => x.examen === lijst.slice(2)).sort((a, b) => a.vraag - b.vraag) : data.vragen.filter(x => x.onderwerp === (lijst ? lijst.slice(2) : q.onderwerp));
    if (!lijst) lijst = `o-${q.onderwerp}`;
    const i = reeks.findIndex(x => x.id === id);
    const vorige = reeks[i - 1], volgende = reeks[i + 1];
    const terug = lijst.startsWith('e-') ? [`${q.jaar}-${tvKort(q.tijdvak)}`, `#/vak/${vak}/examen/${q.examen}`] : [o.naam, `#/vak/${vak}/onderwerp/${q.onderwerp}`];
    zetKruimel([[OVERZICHT.niveaus[v.niveau], '#/'], [v.naam, `#/vak/${vak}`], terug, [`Vraag ${q.vraag}`, null]]);

    const img = (s, alt) => `<img src="${s.src}" width="${s.w}" height="${s.h}" alt="${esc(alt)}" loading="lazy" decoding="async">`;
    const eerder = q.stukken.slice(0, -1), deze = q.stukken[q.stukken.length - 1];
    const examenNaam = `Centraal examen ${OVERZICHT.niveaus[v.niveau].toLowerCase()} ${v.naam.toLowerCase()} ${q.jaar}, ${tv(q.tijdvak)}`;
    const pdf = q.pdf || {};
    const r = lees()[q.id];
    toon(`
      <header class="vraag-kop">
        <span class="label">${esc(examenNaam)}</span>
        <h1>Vraag ${q.vraag} · ${esc(q.opgave || 'Opgave')}</h1>
        <div class="chips"><span class="chip">${esc(o.naam)}</span><span class="chip grijs">${q.punten} punten</span><span class="chip grijs">Syllabus ${esc(o.code)}</span></div>
      </header>
      ${eerder.length ? `<details class="context" open><summary>Inleiding en eerdere vragen van deze opgave (${eerder.length === 1 ? 'vraag ' + eerder[0].vraag : 'vragen ' + eerder[0].vraag + '–' + eerder[eerder.length - 1].vraag})</summary>
        <div class="papier">${eerder.map(s => img(s, `Opgave ${q.opgave}, tekst tot en met vraag ${s.vraag}`)).join('')}</div></details>` : ''}
      <div class="papier deze"><span class="deze-l">VRAAG ${q.vraag}</span>${img(deze, `Vraag ${q.vraag}: ${q.tekst}`)}</div>
      ${q.uitwerkbijlage && pdf.uitwerkbijlage ? `<p class="melding">Bij deze vraag hoort een uitwerkbijlage. <a href="${pdf.uitwerkbijlage}" target="_blank" rel="noopener">Open de uitwerkbijlage (pdf)</a> om erin te tekenen of af te lezen.</p>` : ''}
      ${q.uitwerkbijlage && !pdf.uitwerkbijlage ? `<p class="melding">Bij deze vraag hoort een uitwerkbijlage; die staat achterin de <a href="${pdf.opgaven}" target="_blank" rel="noopener">originele opgaven (pdf)</a>.</p>` : ''}
      <div class="acties">
        <button class="knop hoofd" id="toon" aria-expanded="false">Toon het antwoordmodel</button>
        ${volgende ? `<a class="knop" href="#/vraag/${vak}/${enc(volgende.id)}/${lijst}">Sla over</a>` : ''}
      </div>
      <section id="antwoord" hidden>
        <h2 class="label antwoord-l">Antwoordmodel uit het correctievoorschrift</h2>
        ${q.antwoord ? `<div class="papier">${img(q.antwoord, `Antwoordmodel vraag ${q.vraag}`)}</div>` : `<p class="melding">Het antwoordmodel staat in het <a href="${pdf.correctievoorschrift}" target="_blank" rel="noopener">correctievoorschrift (pdf)</a>.</p>`}
        ${pdf['correctievoorschrift-aanvulling'] ? `<p class="melding">Bij dit examen is een <a href="${pdf['correctievoorschrift-aanvulling']}" target="_blank" rel="noopener">aanvulling op het correctievoorschrift</a> verschenen. Kijk daar ook even.</p>` : ''}
        <div class="score kaart"><b>Hoeveel punten had jij?</b><div class="punten">${Array.from({ length: q.punten + 1 }, (_, p) => `<button data-p="${p}" class="${r && r.s === p ? 'aan' : ''}">${p}</button>`).join('')}</div>
        <span class="label" id="bewaard">${r ? `Bewaard: ${r.s} van ${r.m} punten` : 'Je score wordt in deze browser bewaard'}</span></div>
      </section>
      <nav class="nav-vraag">
        ${vorige ? `<a class="knop" href="#/vraag/${vak}/${enc(vorige.id)}/${lijst}">← Vorige vraag</a>` : '<span></span>'}
        <span class="chip grijs">${i + 1} van ${reeks.length}</span>
        ${volgende ? `<a class="knop hoofd" href="#/vraag/${vak}/${enc(volgende.id)}/${lijst}">Volgende vraag →</a>` : `<a class="knop" href="${terug[1]}">Terug naar de lijst</a>`}
      </nav>
      <section class="bron kaart">
        <b>Bron</b>
        <span>${esc(examenNaam)}, vraag ${q.vraag}. College voor Toetsen en Examens, examenblad.nl. © Staat der Nederlanden.</span>
        <span class="links">
          ${pdf.opgaven ? `<a href="${pdf.opgaven}" target="_blank" rel="noopener">Opgaven (pdf)</a>` : ''}
          ${pdf.correctievoorschrift ? `<a href="${pdf.correctievoorschrift}" target="_blank" rel="noopener">Correctievoorschrift (pdf)</a>` : ''}
          ${pdf.uitwerkbijlage ? `<a href="${pdf.uitwerkbijlage}" target="_blank" rel="noopener">Uitwerkbijlage (pdf)</a>` : ''}
          ${pdf['correctievoorschrift-aanvulling'] ? `<a href="${pdf['correctievoorschrift-aanvulling']}" target="_blank" rel="noopener">Aanvulling correctievoorschrift</a>` : ''}
          <a href="#/vak/${vak}/examen/${q.examen}">Alle vragen van dit examen</a>
        </span>
        ${vak === 'wiskunde-a-havo' || vak.endsWith('-vwo') ? `<span>Het formuleblad staat voorin de originele opgaven.</span>` : ''}
      </section>`, `Vraag ${q.vraag} ${q.jaar}-${tvKort(q.tijdvak)}`);

    const knop = document.getElementById('toon'), ant = document.getElementById('antwoord');
    knop.addEventListener('click', () => {
      ant.hidden = !ant.hidden;
      knop.setAttribute('aria-expanded', String(!ant.hidden));
      knop.textContent = ant.hidden ? 'Toon het antwoordmodel' : 'Verberg het antwoordmodel';
      if (!ant.hidden) ant.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
    ant.querySelector('.punten').addEventListener('click', e => {
      const b = e.target.closest('button');
      if (!b) return;
      const p = +b.dataset.p;
      bewaar(q.id, p, q.punten);
      ant.querySelectorAll('.punten button').forEach(x => x.classList.toggle('aan', x === b));
      document.getElementById('bewaard').textContent = `Bewaard: ${p} van ${q.punten} punten`;
    });
  }

  function nietGevonden() {
    zetKruimel([]);
    toon('<div class="kaart leeg"><p>Deze pagina bestaat niet (meer).</p><a class="knop" href="#/">Naar het begin</a></div>', 'Niet gevonden');
  }

  // ---------- router ----------
  async function route() {
    const [pad, zoek] = location.hash.replace(/^#\/?/, '').split('?');
    const d = pad.split('/').map(decodeURIComponent);
    try {
      if (!OVERZICHT) OVERZICHT = await json('data/vakken.json');
      if (!d[0]) return begin();
      if (d[0] === 'vak' && d.length === 2) return vakPagina(d[1], /per=examen/.test(zoek || ''));
      if (d[0] === 'vak' && d[2] === 'onderwerp') return lijstPagina(d[1], 'onderwerp', d[3]);
      if (d[0] === 'vak' && d[2] === 'examen') return lijstPagina(d[1], 'examen', d[3]);
      if (d[0] === 'vraag') return vraagPagina(d[1], d[2], d[3]);
      nietGevonden();
    } catch (e) {
      console.error(e);
      toon('<div class="kaart leeg"><p>Er ging iets mis bij het laden. Probeer het opnieuw.</p></div>');
    }
  }
  window.addEventListener('hashchange', () => { filter = 'alle'; route(); });
  route();
})();
