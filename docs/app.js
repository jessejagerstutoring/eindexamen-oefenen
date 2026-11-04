/*
 * Eindexamen Oefenen: echte centrale examenvragen per onderwerp.
 * Routes (in de hash):
 *   #/                                begin: kies niveau en vak
 *   #/vak/<vak>                       inhoudsopgave van een vak (of ?per=examen)
 *   #/vak/<vak>/onderwerp/<id>        alle vragen over één onderwerp
 *   #/vak/<vak>/examen/<code>         alle vragen van één examen
 *   #/vak/<vak>/voortgang             je scores per onderwerp en een advies wat je nu oefent
 *   #/tips                            examentips, algemeen en per vak
 *   #/vraag/<vak>/<id>/<lijst>        één vraag; <lijst> is o-<onderwerp> of e-<examen> voor vorige/volgende
 */
(() => {
  const app = document.getElementById('app');
  const kruimel = document.getElementById('kruimel');
  const hoofdnav = document.getElementById('hoofdnav');
  const cache = {};
  let OVERZICHT = null;

  // ---------- scores (alleen in deze browser) ----------
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
  const tipsData = () => json('data/tips.json').catch(() => null);
  const SITE = 'https://jessejagerstutoring.nl';
  const komma = x => x.toFixed(1).replace('.', ',');
  // gemiddeld aantal punten dat een onderwerp per examen oplevert
  const perExamen = (vak, o) => o.punten / OVERZICHT.vakken[vak].examens.length;
  const lijstje = l => `<ul>${l.map(x => `<li>${esc(x)}</li>`).join('')}</ul>`;
  function aanpakBlok(tip, open, kop = 'Zo pak je dit aan') {
    if (!tip) return '';
    return `<details class="aanpak"${open ? ' open' : ''}><summary>${esc(kop)}</summary><div class="aanpak-in">
      <div><h3>Aanpak</h3>${lijstje(tip.aanpak)}</div>
      <div><h3>Hier gaan vaak punten verloren</h3>${lijstje(tip.valkuilen)}</div></div></details>`;
  }
  const hulpBlok = () => `<aside class="hulp"><div><h2>Persoonlijke hulp nodig?</h2>
    <p>Eindexamen Oefenen is een gratis project van Jesse Jagers Tutoring. Kom je er met oefenen alleen niet uit, of wil je gericht toewerken naar je examen? Kijk dan voor bijles en begeleiding op de website.</p></div>
    <a class="knop vol" href="${SITE}" target="_blank" rel="noopener">jessejagerstutoring.nl</a></aside>`;
  // bij welk vak hoort een examencode (voor scores op de startpagina)
  function vakVanExamen(code) {
    for (const [k, v] of Object.entries(OVERZICHT.vakken)) {
      const e = v.examens.find(x => x.code === code);
      if (e) return [k, e];
    }
    return [];
  }
  const niv = vak => OVERZICHT.niveaus[OVERZICHT.vakken[vak].niveau];
  const vakNaam = vak => `${OVERZICHT.vakken[vak].naam} ${niv(vak).toLowerCase()}`;
  const onderwerp = (vak, id) => OVERZICHT.vakken[vak].domeinen.flatMap(d => d.onderwerpen).find(o => o.id === id);
  // paragraafnummer zoals in een boek: hoofdstuk = domein, paragraaf = onderwerp
  function nummer(vak, id) {
    let uit = '';
    OVERZICHT.vakken[vak].domeinen.forEach((d, i) => d.onderwerpen.forEach((o, j) => { if (o.id === id) uit = `${i + 1}.${j + 1}`; }));
    return uit;
  }

  function status(id) {
    const r = lees()[id];
    if (!r) return '<span class="st">–</span>';
    const k = r.s === r.m ? 'goed' : r.s === 0 ? 'fout' : 'half';
    return `<span class="st ${k}">${r.s} van ${r.m}</span>`;
  }
  const gemaakt = ids => { const v = lees(); return ids.filter(i => v[i]).length; };

  function zetKruimel(delen) {
    kruimel.innerHTML = delen.map(([t, h]) => (h ? `<a href="${h}">${esc(t)}</a>` : `<span>${esc(t)}</span>`)).join('<span class="sep">›</span>');
  }
  function zetNav(actief) {
    const per = {};
    Object.entries(OVERZICHT.vakken).forEach(([k, v]) => (per[v.niveau] = per[v.niveau] || []).push([k, v]));
    hoofdnav.innerHTML = Object.entries(per).map(([n, l]) => `<b>${OVERZICHT.niveaus[n]}</b>${l.map(([k, v]) => `<a href="#/vak/${k}" class="${k === actief ? 'aan' : ''}">${esc(v.naam)}</a>`).join('')}`).join('')
      + `<a href="#/tips" class="los ${actief === 'tips' ? 'aan' : ''}">Examentips</a>`;
  }
  function toon(html, titel, vak) {
    zetNav(vak);
    app.innerHTML = html;
    document.title = titel ? `${titel} – Eindexamen Oefenen` : 'Eindexamen Oefenen';
    window.scrollTo(0, 0);
  }
  // hele tabelrij klikbaar, de link in de rij blijft het echte doel
  function klikbareRijen(tabel) {
    tabel.addEventListener('click', e => {
      const tr = e.target.closest('tr[data-href]');
      if (tr && !e.target.closest('a')) location.hash = tr.dataset.href;
    });
  }

  // ---------- begin ----------
  function begin() {
    zetKruimel([]);
    const sc = lees();
    const telVak = {};
    let laatste = null;
    Object.entries(sc).forEach(([id, r]) => {
      const [k, e] = vakVanExamen(id.split(':')[0]);
      if (!k) return;
      telVak[k] = (telVak[k] || 0) + 1;
      if (!laatste || r.t > laatste.t) laatste = { t: r.t, id, k, e };
    });
    const per = {};
    Object.entries(OVERZICHT.vakken).forEach(([k, v]) => (per[v.niveau] = per[v.niveau] || []).push([k, v]));
    const rijen = Object.entries(per).map(([n, lijst]) => lijst.map(([k, v], i) => {
      const nOw = v.domeinen.reduce((s, d) => s + d.onderwerpen.length, 0);
      const j = v.examens.map(e => e.jaar);
      return `<tr data-href="#/vak/${k}"><td class="niv">${i === 0 ? OVERZICHT.niveaus[n] : ''}</td>
        <td class="vaknaam"><a href="#/vak/${k}">${esc(v.naam)}</a></td>
        <td class="r verberg">${nOw}</td><td class="r">${v.vragen}</td><td class="r verberg">${Math.min(...j)}–${Math.max(...j)}</td>
        <td class="r">${telVak[k] ? `<a class="st" href="#/vak/${k}/voortgang">${telVak[k]} gemaakt</a>` : '<span class="st">–</span>'}</td></tr>`;
    }).join('')).join('');
    toon(`
      <div class="titelblok">
        <div>
          <p class="bovenkop">Centraal examen wiskunde · havo en vwo</p>
          <h1>Examenvragen oefenen per onderwerp</h1>
          <p class="inleiding">Alle vragen uit de centrale examens sinds 2018, geordend volgens de syllabus. Je maakt elke vraag zoals hij op het examen stond, met de inleiding, figuren en tabellen van de opgave, en kijkt hem na met het officiële correctievoorschrift.</p>
        </div>
        <aside class="werkwijze">
          <h2>Zo werk je</h2>
          <ol>
            <li>Kies je vak en een onderwerp uit de inhoudsopgave.</li>
            <li>Maak de vraag op papier.</li>
            <li>Bekijk het antwoordmodel en geef jezelf punten.</li>
            <li>Kijk bij <b>Mijn voortgang</b> waar je het beste verder kunt oefenen.</li>
          </ol>
          <p class="klein">Lees ook de <a href="#/tips">examentips</a>: hoe je je tijd verdeelt en hoe je punten haalt.</p>
        </aside>
      </div>
      ${laatste ? `<p class="verder"><span>Verder waar je gebleven was:</span> <a href="#/vraag/${laatste.k}/${enc(laatste.id)}">${esc(vakNaam(laatste.k))}, examen ${laatste.e.jaar}-${tvKort(laatste.e.tijdvak)}, vraag ${esc(laatste.id.split(':')[1])}</a></p>` : ''}
      <h2 class="sectiekop">Kies je vak</h2>
      <table class="catalogus">
        <thead><tr><th>Niveau</th><th>Vak</th><th class="r verberg">Onderwerpen</th><th class="r">Vragen</th><th class="r verberg">Examens</th><th class="r">Jij</th></tr></thead>
        <tbody>${rijen}</tbody>
      </table>`);
    klikbareRijen(app.querySelector('.catalogus'));
  }

  // ---------- vak: inhoudsopgave ----------
  async function vakPagina(vak, perExamen) {
    const v = OVERZICHT.vakken[vak];
    if (!v) return nietGevonden();
    const data = await vakData(vak);
    zetKruimel([['Start', '#/'], [vakNaam(vak), null]]);
    const ids = data.vragen.map(q => q.id);
    const kop = `<header class="vakkop">
        <div><p class="bovenkop">${niv(vak)} · centraal examen</p><h1>${esc(v.naam)}</h1>
        <p>${v.vragen} vragen uit ${v.examens.length} examens (${v.examens[v.examens.length - 1].jaar}–${v.examens[0].jaar}) · ${gemaakt(ids)} door jou gemaakt</p></div>
        <nav class="weergave" aria-label="Weergave"><a href="#/vak/${vak}" class="${perExamen ? '' : 'aan'}">Per onderwerp</a><a href="#/vak/${vak}?per=examen" class="${perExamen ? 'aan' : ''}">Per examen</a><a href="#/vak/${vak}/voortgang">Mijn voortgang</a></nav>
      </header>`;
    if (perExamen) {
      const rijen = v.examens.map(e => {
        const q = data.vragen.filter(x => x.examen === e.code);
        return `<tr data-href="#/vak/${vak}/examen/${e.code}"><td><a href="#/vak/${vak}/examen/${e.code}">${e.jaar}</a></td><td>${tv(e.tijdvak)}</td>
          <td class="r">${q.length}</td><td class="r">${q.reduce((s, x) => s + x.punten, 0)}</td><td class="r">${gemaakt(q.map(x => x.id))} van ${q.length}</td></tr>`;
      }).join('');
      toon(kop + `<div class="tabelvak"><table class="tabel"><thead><tr><th>Jaar</th><th>Tijdvak</th><th class="r">Vragen</th><th class="r">Punten</th><th class="r">Gemaakt</th></tr></thead><tbody>${rijen}</tbody></table></div>`, vakNaam(vak), vak);
      return klikbareRijen(app.querySelector('.tabel'));
    }
    toon(kop + `<div class="inhoud">${v.domeinen.map((d, i) => `<section class="hoofdstuk"><h2><span class="hnr">${i + 1}</span>${esc(d.naam)}</h2>${d.onderwerpen.map((o, j) => {
      const q = data.vragen.filter(x => x.onderwerp === o.id).map(x => x.id);
      const g = gemaakt(q);
      return `<a class="paragraaf" href="#/vak/${vak}/onderwerp/${o.id}">
          <span class="pnr">${i + 1}.${j + 1}</span>
          <span class="pmid"><span class="ptitel">${esc(o.naam)}</span><span class="syl" title="Syllabus">${esc(o.code)}</span><span class="stip"></span></span>
          <span class="pcijfers"><b>${o.vragen}</b> vragen · ${o.punten} p</span>
          <span class="pomschr">${esc(o.omschrijving)}</span>
          <span class="pvoortgang ${g && g === q.length ? 'af' : ''}">${g ? `${g} van ${q.length} gemaakt` : ''}</span>
        </a>`;
    }).join('')}</section>`).join('')}</div>`, vakNaam(vak), vak);
  }

  // ---------- lijst van vragen ----------
  const FILTERS = { alle: () => true, recent: q => q.jaar >= 2022, ouder: q => q.jaar < 2022, open: q => !lees()[q.id] };
  let filter = 'alle';

  async function lijstPagina(vak, soort, sleutel) {
    const v = OVERZICHT.vakken[vak];
    if (!v) return nietGevonden();
    const data = await vakData(vak);
    let vragen, titel, sub, lijstId, boven, extra = '';
    if (soort === 'onderwerp') {
      const o = onderwerp(vak, sleutel);
      if (!o) return nietGevonden();
      const tips = await tipsData();
      extra = aanpakBlok(tips && tips.vakken[vak] && tips.vakken[vak].onderwerpen[sleutel], true);
      vragen = data.vragen.filter(q => q.onderwerp === sleutel);
      titel = o.naam;
      boven = `${vakNaam(vak)} · paragraaf ${nummer(vak, sleutel)} · syllabus ${o.code}`;
      sub = `${o.omschrijving} Dit onderwerp levert gemiddeld ${komma(perExamen(vak, o))} punten per examen op.`;
      lijstId = `o-${sleutel}`;
    } else {
      vragen = data.vragen.filter(q => q.examen === sleutel).sort((a, b) => a.vraag - b.vraag);
      if (!vragen.length) return nietGevonden();
      titel = `Examen ${vragen[0].jaar}, ${tv(vragen[0].tijdvak)}`;
      boven = vakNaam(vak);
      sub = `${vragen.length} vragen, samen ${vragen.reduce((s, q) => s + q.punten, 0)} punten.`;
      lijstId = `e-${sleutel}`;
    }
    zetKruimel([['Start', '#/'], [vakNaam(vak), `#/vak/${vak}${soort === 'examen' ? '?per=examen' : ''}`], [soort === 'onderwerp' ? titel : `${vragen[0].jaar}-${tvKort(vragen[0].tijdvak)}`, null]]);
    const kolom = soort === 'onderwerp' ? '<th>Examen</th>' : '<th class="verberg">Onderwerp</th>';
    const teken = () => {
      const zicht = vragen.filter(FILTERS[filter]);
      document.getElementById('rijen').innerHTML = zicht.length ? zicht.map(q => {
        const h = `#/vraag/${vak}/${enc(q.id)}/${lijstId}`;
        return `<tr data-href="${h}">
          ${soort === 'onderwerp' ? `<td class="zacht">${q.jaar}-${tvKort(q.tijdvak)}</td>` : ''}
          <td class="vnr">${q.vraag}</td>
          <td><a href="${h}">${esc(q.opgave || 'Opgave')}</a></td>
          ${soort === 'examen' ? `<td class="zacht verberg">${esc(onderwerp(vak, q.onderwerp).naam)}</td>` : ''}
          <td class="r">${q.punten}</td><td class="r">${status(q.id)}</td></tr>`;
      }).join('') : `<tr><td colspan="5" class="leeg">Geen vragen bij dit filter.</td></tr>`;
      document.querySelectorAll('.filters button').forEach(b => b.classList.toggle('aan', b.dataset.f === filter));
    };
    toon(`<header class="lijstkop"><p class="bovenkop">${esc(boven)}</p><h1>${esc(titel)}</h1><p class="inleiding">${esc(sub)}</p></header>
      ${extra}
      <div class="filters" role="group" aria-label="Filter"><span>Toon:</span>
        <button data-f="alle">alle ${vragen.length} vragen</button>
        ${soort === 'onderwerp' ? `<button data-f="recent">2022 en later</button><button data-f="ouder">2018–2021</button>` : ''}
        <button data-f="open">nog niet gemaakt</button>
      </div>
      <div class="tabelvak"><table class="tabel">
        <thead><tr>${soort === 'onderwerp' ? kolom : ''}<th>Vraag</th><th>Opgave</th>${soort === 'examen' ? kolom : ''}<th class="r">Punten</th><th class="r">Jouw score</th></tr></thead>
        <tbody id="rijen"></tbody></table></div>`, titel, vak);
    app.querySelector('.filters').addEventListener('click', e => { const b = e.target.closest('button'); if (b) { filter = b.dataset.f; teken(); } });
    klikbareRijen(app.querySelector('.tabel'));
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
    const tips = await tipsData();
    const tip = tips && tips.vakken[vak] && tips.vakken[vak].onderwerpen[q.onderwerp];
    if (!lijst) lijst = `o-${q.onderwerp}`;
    // de lijst waar de leerling vandaan komt, voor vorige en volgende
    const reeks = lijst.startsWith('e-') ? data.vragen.filter(x => x.examen === lijst.slice(2)).sort((a, b) => a.vraag - b.vraag) : data.vragen.filter(x => x.onderwerp === lijst.slice(2));
    const i = reeks.findIndex(x => x.id === id);
    const vorige = reeks[i - 1], volgende = reeks[i + 1];
    const terug = lijst.startsWith('e-') ? [`Examen ${q.jaar}-${tvKort(q.tijdvak)}`, `#/vak/${vak}/examen/${q.examen}`] : [`${nummer(vak, q.onderwerp)} ${o.naam}`, `#/vak/${vak}/onderwerp/${q.onderwerp}`];
    zetKruimel([['Start', '#/'], [vakNaam(vak), `#/vak/${vak}`], terug, [`Vraag ${q.vraag}`, null]]);

    const img = (s, alt) => `<img src="${s.src}" width="${s.w}" height="${s.h}" alt="${esc(alt)}" loading="lazy" decoding="async">`;
    const eerder = q.stukken.slice(0, -1), deze = q.stukken[q.stukken.length - 1];
    const pdf = q.pdf || {};
    const r = lees()[q.id];
    const link = (u, t) => (u ? `<a href="${u}" target="_blank" rel="noopener">${t}</a>` : '');
    toon(`
      <header class="vraagkop">
        <p class="bovenkop">${esc(vakNaam(vak))} · examen ${q.jaar}, ${tv(q.tijdvak)}</p>
        <h1><span class="vn">Vraag ${q.vraag}</span> · ${esc(q.opgave || 'Opgave')}</h1>
      </header>
      <div class="vraagopzet">
        <aside class="kantlijn">
          <dl>
            <div><dt>Examen</dt><dd>${esc(v.naam)} ${OVERZICHT.niveaus[v.niveau].toLowerCase()}<br>${q.jaar}, ${tv(q.tijdvak)}</dd></div>
            <div><dt>Opgave</dt><dd>${esc(q.opgave || '–')}</dd></div>
            <div><dt>Punten</dt><dd>${q.punten}</dd></div>
            <div><dt>Onderwerp</dt><dd><a href="#/vak/${vak}/onderwerp/${q.onderwerp}">${nummer(vak, q.onderwerp)} ${esc(o.naam)}</a><br><span class="st">syllabus ${esc(o.code)}</span></dd></div>
            ${r ? `<div><dt>Jouw score</dt><dd>${status(q.id)}</dd></div>` : ''}
          </dl>
          <div class="bronnen"><b>Originele stukken</b>
            ${link(pdf.opgaven, 'Opgaven (pdf)')}
            ${link(pdf.uitwerkbijlage, 'Uitwerkbijlage (pdf)')}
            ${link(pdf.correctievoorschrift, 'Correctievoorschrift (pdf)')}
            ${link(pdf['correctievoorschrift-aanvulling'], 'Aanvulling correctievoorschrift')}
            <a href="#/vak/${vak}/examen/${q.examen}">Alle vragen van dit examen</a>
          </div>
        </aside>
        <div>
          ${eerder.length ? `<details class="context" open><summary>Inleiding en eerdere vragen van deze opgave (${eerder.length === 1 ? 'vraag ' + eerder[0].vraag : 'vragen ' + eerder[0].vraag + ' t/m ' + eerder[eerder.length - 1].vraag})</summary>
            <div class="blad">${eerder.map(s => img(s, `Opgave ${q.opgave}, tekst tot en met vraag ${s.vraag}`)).join('')}</div></details>` : ''}
          <div class="blad deze">${img(deze, `Vraag ${q.vraag}: ${q.tekst}`)}</div>
          ${q.uitwerkbijlage ? `<p class="opmerking">Bij deze vraag hoort een uitwerkbijlage. ${pdf.uitwerkbijlage ? `<a href="${pdf.uitwerkbijlage}" target="_blank" rel="noopener">Open de uitwerkbijlage (pdf)</a>.` : `Die staat achterin de <a href="${pdf.opgaven}" target="_blank" rel="noopener">originele opgaven (pdf)</a>.`}</p>` : ''}
          ${vak === 'wiskunde-a-havo' ? `<p class="opmerking">Het formuleblad staat voorin de <a href="${pdf.opgaven}" target="_blank" rel="noopener">originele opgaven (pdf)</a>.</p>` : ''}
          ${aanpakBlok(tip, false, 'Hint: aanpak bij dit onderwerp')}
          <div class="acties"><button class="knop vol" id="toon" aria-expanded="false">Bekijk het antwoordmodel</button></div>
          <section class="antwoordblok" id="antwoord" hidden>
            <h2>Antwoordmodel</h2>
            ${q.antwoord ? `<div class="blad">${img(q.antwoord, `Antwoordmodel vraag ${q.vraag}`)}</div>` : `<p class="opmerking">Het antwoordmodel staat in het <a href="${pdf.correctievoorschrift}" target="_blank" rel="noopener">correctievoorschrift (pdf)</a>.</p>`}
            ${pdf['correctievoorschrift-aanvulling'] ? `<p class="opmerking">Voor dit examen is een <a href="${pdf['correctievoorschrift-aanvulling']}" target="_blank" rel="noopener">aanvulling op het correctievoorschrift</a> verschenen.</p>` : ''}
            <div class="zelfscore"><b>Hoeveel punten heb je gehaald?</b>
              <div class="punten" role="group" aria-label="Punten">${Array.from({ length: q.punten + 1 }, (_, p) => `<button data-p="${p}" class="${r && r.s === p ? 'aan' : ''}">${p}</button>`).join('')}</div>
              <span class="klein" id="bewaard">${r ? `Bewaard: ${r.s} van ${r.m} punten.` : 'Elk bolletje (•) in het antwoordmodel is meestal 1 punt.'}</span></div>
          </section>
          <nav class="bladnav">
            ${vorige ? `<a class="knop stil" href="#/vraag/${vak}/${enc(vorige.id)}/${lijst}">‹ Vorige vraag</a>` : '<span></span>'}
            <span class="teller">${i + 1} van ${reeks.length}</span>
            ${volgende ? `<a class="knop" href="#/vraag/${vak}/${enc(volgende.id)}/${lijst}">Volgende vraag ›</a>` : `<a class="knop stil" href="${terug[1]}">Terug naar het overzicht</a>`}
          </nav>
        </div>
      </div>`, `Vraag ${q.vraag}, ${vakNaam(vak)} ${q.jaar}-${tvKort(q.tijdvak)}`, vak);

    const knop = document.getElementById('toon'), ant = document.getElementById('antwoord');
    knop.addEventListener('click', () => {
      ant.hidden = !ant.hidden;
      knop.setAttribute('aria-expanded', String(!ant.hidden));
      knop.textContent = ant.hidden ? 'Bekijk het antwoordmodel' : 'Verberg het antwoordmodel';
      if (!ant.hidden) ant.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
    ant.querySelector('.punten').addEventListener('click', e => {
      const b = e.target.closest('button');
      if (!b) return;
      const p = +b.dataset.p;
      bewaar(q.id, p, q.punten);
      ant.querySelectorAll('.punten button').forEach(x => x.classList.toggle('aan', x === b));
      document.getElementById('bewaard').textContent = `Bewaard: ${p} van ${q.punten} punten.`;
    });
  }

  // ---------- mijn voortgang en advies ----------
  async function voortgangPagina(vak) {
    const v = OVERZICHT.vakken[vak];
    if (!v) return nietGevonden();
    const data = await vakData(vak);
    const sc = lees();
    zetKruimel([['Start', '#/'], [vakNaam(vak), `#/vak/${vak}`], ['Mijn voortgang', null]]);
    const alle = [];
    const hoofdstukken = v.domeinen.map((d, i) => ({ d, i, ow: d.onderwerpen.map((o, j) => {
      const q = data.vragen.filter(x => x.onderwerp === o.id);
      const af = q.filter(x => sc[x.id]);
      const s = af.reduce((t, x) => t + sc[x.id].s, 0), m = af.reduce((t, x) => t + sc[x.id].m, 0);
      const pct = m ? s / m : null, w = perExamen(vak, o);
      const open = q.find(x => !sc[x.id]);
      // voorrang: veel examenpunten en een lage score; nog niet geoefend telt bijna als een lage score
      let prio = !af.length ? w * 0.8 : w * (1 - pct) + (af.length < 3 && open ? w * 0.25 : 0);
      if (!open) prio *= 0.5;
      const r = { o, nr: `${i + 1}.${j + 1}`, n: q.length, af: af.length, s, m, pct, w, open: open || q[0], prio };
      alle.push(r);
      return r;
    }) }));
    const totS = alle.reduce((t, r) => t + r.s, 0), totM = alle.reduce((t, r) => t + r.m, 0), totAf = alle.reduce((t, r) => t + r.af, 0);
    const oordeel = r => (!r.af ? ['', 'nog niet geoefend'] : r.pct < 0.55 ? ['fout', 'oefen meer'] : r.pct < 0.8 ? ['half', 'bijna'] : r.af < 3 ? ['goed', 'goed begin'] : ['goed', 'beheerst']);
    const reden = r => (!r.af ? `Nog niet geoefend. Levert gemiddeld ${komma(r.w)} punten per examen op.`
      : `Je haalt ${Math.round(r.pct * 100)}% van de punten (${r.af} van ${r.n} vragen gemaakt). Levert gemiddeld ${komma(r.w)} punten per examen op.`);
    const advies = alle.filter(r => r.prio > 0.3).sort((a, b) => b.prio - a.prio).slice(0, 3);
    toon(`<header class="vakkop">
        <div><p class="bovenkop">${niv(vak)} · ${esc(v.naam)}</p><h1>Mijn voortgang</h1>
        <p>${totAf ? `${totAf} van ${v.vragen} vragen gemaakt · ${totS} van ${totM} punten behaald (${Math.round(totS / totM * 100)}%)` : 'Je hebt bij dit vak nog geen vragen nagekeken.'}</p></div>
        <nav class="weergave" aria-label="Weergave"><a href="#/vak/${vak}">Per onderwerp</a><a href="#/vak/${vak}?per=examen">Per examen</a><a href="#/vak/${vak}/voortgang" class="aan">Mijn voortgang</a></nav>
      </header>
      <section class="advies">
        <h2>${totAf ? 'Hier kun je nu het beste aan werken' : 'Begin met deze onderwerpen'}</h2>
        <p class="klein">Het advies kijkt naar je scores en naar hoeveel punten een onderwerp gemiddeld oplevert op het examen.${totAf ? '' : ' Deze onderwerpen leveren de meeste punten op.'}</p>
        <ol>${advies.map(r => `<li>
          <div><a class="advies-titel" href="#/vak/${vak}/onderwerp/${r.o.id}">${r.nr} ${esc(r.o.naam)}</a><p>${esc(reden(r))}</p></div>
          <a class="knop" href="#/vraag/${vak}/${enc(r.open.id)}/o-${r.o.id}">Maak een vraag ›</a></li>`).join('')}</ol>
      </section>
      <h2 class="sectiekop">Per onderwerp</h2>
      <div class="tabelvak"><table class="tabel voortgang">
        <thead><tr><th>Onderwerp</th><th class="r verberg">Punten per examen</th><th class="r">Gemaakt</th><th>Score</th></tr></thead>
        <tbody>${hoofdstukken.map(h => `<tr class="hst"><td colspan="4">${h.i + 1} ${esc(h.d.naam)}</td></tr>` + h.ow.map(r => {
          const [k, t] = oordeel(r);
          return `<tr data-href="#/vak/${vak}/onderwerp/${r.o.id}"><td><span class="zacht">${r.nr}</span> <a href="#/vak/${vak}/onderwerp/${r.o.id}">${esc(r.o.naam)}</a></td>
            <td class="r verberg">${komma(r.w)}</td><td class="r">${r.af} van ${r.n}</td>
            <td><span class="balk"><span class="${k}" style="width:${r.pct === null ? 0 : Math.round(r.pct * 100)}%"></span></span><span class="st ${k}">${r.pct === null ? '' : Math.round(r.pct * 100) + '% · '}${t}</span></td></tr>`;
        }).join('')).join('')}</tbody></table></div>
      ${hulpBlok()}
      ${totAf ? '<p class="wissen"><button class="knop stil" id="wis">Wis mijn scores voor dit vak</button></p>' : ''}`, `Mijn voortgang ${vakNaam(vak)}`, vak);
    klikbareRijen(app.querySelector('.tabel'));
    const wis = document.getElementById('wis');
    if (wis) wis.addEventListener('click', () => {
      if (!wis.dataset.zeker) { wis.dataset.zeker = '1'; wis.textContent = 'Weet je het zeker? Klik nog een keer om te wissen'; return; }
      const nieuw = lees();
      data.vragen.forEach(x => delete nieuw[x.id]);
      try { localStorage.setItem(SLEUTEL, JSON.stringify(nieuw)); } catch (e) { /* niets te wissen */ }
      voortgangPagina(vak);
    });
  }

  // ---------- examentips ----------
  async function tipsPagina() {
    const t = await tipsData();
    if (!t) return nietGevonden();
    zetKruimel([['Start', '#/'], ['Examentips', null]]);
    toon(`<header class="lijstkop"><p class="bovenkop">Voorbereiding</p><h1>Examentips wiskunde</h1>
        <p class="inleiding">Wat je in de laatste weken doet, hoe je je tijd verdeelt en hoe je je antwoorden opschrijft zodat je alle punten krijgt. De tips volgen de regels uit de correctievoorschriften.</p></header>
      <div class="tips">${t.algemeen.map((x, i) => `<section class="tipblok"><h2><span class="hnr">${i + 1}</span>${esc(x.kop)}</h2>${lijstje(x.punten)}</section>`).join('')}</div>
      <h2 class="sectiekop">Let op per vak</h2>
      <div class="tipvakken">${Object.entries(t.vakken).filter(([k]) => OVERZICHT.vakken[k]).map(([k, x]) => `<section class="tipvak"><h3><a href="#/vak/${k}">${esc(vakNaam(k))}</a></h3>${lijstje(x.letop)}</section>`).join('')}</div>
      <p class="klein">Bij elk onderwerp staat bovendien een korte aanpak met de fouten die het vaakst punten kosten.</p>
      ${hulpBlok()}`, 'Examentips', 'tips');
  }

  function nietGevonden() {
    zetKruimel([['Start', '#/']]);
    toon('<p class="leeg">Deze pagina bestaat niet (meer).</p><a class="knop" href="#/">Naar de start</a>', 'Niet gevonden');
  }

  // ---------- router ----------
  async function route() {
    const [pad, zoek] = location.hash.replace(/^#\/?/, '').split('?');
    const d = pad.split('/').map(decodeURIComponent);
    try {
      if (!OVERZICHT) OVERZICHT = await json('data/vakken.json');
      if (!d[0]) return begin();
      if (d[0] === 'tips') return tipsPagina();
      if (d[0] === 'vak' && d[2] === 'voortgang') return voortgangPagina(d[1]);
      if (d[0] === 'vak' && d.length === 2) return vakPagina(d[1], /per=examen/.test(zoek || ''));
      if (d[0] === 'vak' && d[2] === 'onderwerp') return lijstPagina(d[1], 'onderwerp', d[3]);
      if (d[0] === 'vak' && d[2] === 'examen') return lijstPagina(d[1], 'examen', d[3]);
      if (d[0] === 'vraag') return vraagPagina(d[1], d[2], d[3]);
      nietGevonden();
    } catch (e) {
      console.error(e);
      app.innerHTML = '<p class="leeg">Er ging iets mis bij het laden. Probeer het opnieuw.</p>';
    }
  }
  window.addEventListener('hashchange', () => { filter = 'alle'; route(); });
  route();
})();
