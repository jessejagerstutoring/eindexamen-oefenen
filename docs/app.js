/*
 * Eindexamen Oefenen: echte centrale examenvragen per onderwerp.
 * Routes (in de hash):
 *   #/                                begin: kies niveau en vak
 *   #/vak/<vak>                       inhoudsopgave van een vak (of ?per=examen)
 *   #/vak/<vak>/onderwerp/<id>        alle vragen over één onderwerp
 *   #/vak/<vak>/examen/<code>         alle vragen van één examen
 *   #/vak/<vak>/voortgang             je scores per onderwerp en een advies wat je nu oefent
 *   #/bundels[/<vak>]                 gratis examenbundels als pdf
 *   #/docenten                        uitleg voor docenten
 *   #/logboek                         wat er wanneer aan de site is veranderd
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
  // gratis examenbundels (pdf); ontbreekt het bestand, dan is er gewoon nog geen bundel
  const bundels = () => json('data/bundels.json').catch(() => []);
  const logboek = () => json('data/logboek.json').catch(() => []);
  // e-mailadres voor foutmeldingen; zolang dit leeg is, gaat een melding via GitHub
  const MELDADRES = '';
  const MELDPAGINA = 'https://github.com/jessejagerstutoring/eindexamen-oefenen/issues/new';
  // goede gratis uitleg elders, per vakgroep (data/uitleg.json; ook gebruikt door tools/bouw_statisch.py)
  const uitleg = () => json('data/uitleg.json').then(d => d.bronnen).catch(() => ({}));
  const familie = vak => vak.split('-')[0];
  const dagNL = d => new Date(d).toLocaleDateString('nl-NL', { day: 'numeric', month: 'long', year: 'numeric' });
  // vakken waarvan het opgavenboekje voorin een formuleblad heeft
  const FORMULEBLAD = ['wiskunde-a-havo', 'wiskunde-a-vwo', 'wiskunde-b-vwo'];
  const komma = x => x.toFixed(1).replace('.', ',');
  // gemiddeld aantal punten dat een onderwerp per examen oplevert
  const perExamen = (vak, o) => o.punten / OVERZICHT.vakken[vak].examens.length;
  const hulpBlok = () => `<aside class="hulp"><div><h2>Klopt er iets niet?</h2>
    <p>Een vraag bij het verkeerde onderwerp, een tip die niet helpt of een figuur die niet goed is uitgesneden: laat het weten, dan wordt het aangepast. Bij elke vraag staat een vraagcode, die helpt om hem terug te vinden.</p></div>
    <a class="knop" href="#/over/fouten">Een fout melden</a></aside>`;
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
    hoofdnav.innerHTML = Object.entries(per).map(([n, l]) => `<b>${OVERZICHT.niveaus[n]}</b>${l.map(([k, v]) => `<a href="#/vak/${k}" class="${k === actief ? 'aan' : ''}">${esc(v.naam)}</a>`).join('')}`).join('');
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
  const NIVEAUSLEUTEL = 'eo-niveau';
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
    const niveaus = Object.keys(OVERZICHT.niveaus);
    let gekozen = (() => { try { return localStorage.getItem(NIVEAUSLEUTEL); } catch (e) { return null; } })();
    if (!niveaus.includes(gekozen)) gekozen = laatste ? OVERZICHT.vakken[laatste.k].niveau : niveaus[0];
    const totaal = Object.values(OVERZICHT.vakken).reduce((t, v) => t + v.vragen, 0);
    const kaart = (k, v) => {
      const nOw = v.domeinen.reduce((t, d) => t + d.onderwerpen.length, 0);
      const j = v.examens.map(e => e.jaar);
      return `<a class="vakkaart" href="#/vak/${k}">
        <span class="vk-naam">${esc(v.naam)}</span>
        <span class="vk-cijfers">${v.vragen} vragen · ${nOw} onderwerpen · ${Math.min(...j)}–${Math.max(...j)}</span>
        <span class="vk-jij">${telVak[k] ? `${telVak[k]} door jou gemaakt` : ''}</span></a>`;
    };
    const tekenVakken = () => {
      const lijst = Object.entries(OVERZICHT.vakken).filter(([, v]) => v.niveau === gekozen);
      document.getElementById('vakken').innerHTML = lijst.map(([k, v]) => kaart(k, v)).join('');
      document.querySelectorAll('.niveaukeuze button').forEach(b => {
        b.classList.toggle('aan', b.dataset.n === gekozen);
        b.setAttribute('aria-pressed', String(b.dataset.n === gekozen));
      });
    };
    toon(`
      <div class="titelblok">
        <div>
          <p class="bovenkop">Centraal examen · havo en vwo</p>
          <h1>Echte examenvragen, per onderwerp</h1>
          <p class="inleiding">Alle ${totaal.toLocaleString('nl-NL')} vragen uit de centrale examens wiskunde, natuurkunde, scheikunde en biologie sinds 2018, met het officiële correctievoorschrift. Gratis, zonder account en zonder reclame.</p>
        </div>
        <aside class="werkwijze">
          <h2>Zo werk je</h2>
          <ol>
            <li>Kies een onderwerp waar je punten wilt halen.</li>
            <li>Maak de vraag op papier, zoals op het examen.</li>
            <li>Kijk na met het antwoordmodel en geef jezelf punten.</li>
            <li>Bij <b>Mijn voortgang</b> zie je wat je daarna het beste kunt doen.</li>
          </ol>
        </aside>
      </div>
      <ul class="beloftes">
        <li><b>Officieel materiaal</b>Elke vraag en elk antwoordmodel komt letterlijk uit de examens van het College voor Toetsen en Examens.</li>
        <li><b>Per vraag ingedeeld</b>Elke vraag is afzonderlijk gelezen en bij een onderwerp uit de syllabus ingedeeld, met hulp van AI (Claude) en met een ervaren bijlesdocent die meekijkt.</li>
        <li><b>Ook op papier</b>Voor elk vak is er een <a href="#/bundels">gratis examenbundel</a> als pdf: opgaven per onderwerp, complete examens en alle uitwerkingen.</li>
      </ul>
      ${laatste ? `<p class="verder"><span>Verder waar je gebleven was:</span> <a href="#/vraag/${laatste.k}/${enc(laatste.id)}">${esc(vakNaam(laatste.k))}, examen ${laatste.e.jaar}-${tvKort(laatste.e.tijdvak)}, vraag ${esc(laatste.id.split(':')[1])}</a></p>` : ''}
      <section class="kies">
        <h2 class="sectiekop">Kies je niveau en je vak</h2>
        <div class="niveaukeuze" role="group" aria-label="Niveau">${niveaus.map(n => `<button data-n="${n}">${OVERZICHT.niveaus[n]}</button>`).join('')}</div>
        <div class="vakkaarten" id="vakken"></div>
      </section>
      <section class="nieuws" id="nieuws"></section>`);
    tekenVakken();
    app.querySelector('.niveaukeuze').addEventListener('click', e => {
      const b = e.target.closest('button');
      if (!b) return;
      gekozen = b.dataset.n;
      try { localStorage.setItem(NIVEAUSLEUTEL, gekozen); } catch (err) { /* privévenster */ }
      tekenVakken();
    });
    logboek().then(l => {
      const plek = document.getElementById('nieuws');
      if (!plek || !l.length) return;
      plek.innerHTML = `<h2 class="sectiekop">Nieuw op de site</h2>
        <ol class="logboek kort">${l.slice(0, 3).map(x => `<li><time datetime="${x.datum}">${dagNL(x.datum)}</time><div><b>${esc(x.titel)}</b><p>${esc(x.tekst)}</p></div></li>`).join('')}</ol>
        <p class="meer"><a href="#/logboek">Alles wat er is veranderd ›</a></p>`;
    });
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
        <p>${v.vragen} vragen uit ${v.examens.length} examens (${v.examens[v.examens.length - 1].jaar}–${v.examens[0].jaar}) · ${gemaakt(ids)} door jou gemaakt</p>
        <p class="actueel">Bijgewerkt tot en met het examen van ${v.examens[0].jaar}, ${tv(v.examens[0].tijdvak)}.</p></div>
        <nav class="weergave" aria-label="Weergave"><a href="#/vak/${vak}" class="${perExamen ? '' : 'aan'}">Per onderwerp</a><a href="#/vak/${vak}?per=examen" class="${perExamen ? 'aan' : ''}">Per examen</a><a href="#/vak/${vak}/voortgang">Mijn voortgang</a></nav>
      </header>`;
    const bundel = (await bundels()).find(b => b.vak === vak);
    const bundelRegel = bundel ? `<aside class="bundel-blok">
        <a href="#/bundels/${vak}" class="bundel-mini" aria-hidden="true" tabindex="-1"><img src="${bundel.omslag}" alt="" width="250" height="354" loading="lazy"></a>
        <div><b>Liever op papier?</b><p>De gratis examenbundel ${esc(vakNaam(vak))}: ${bundel.paginas} pagina's met opgaven per onderwerp, ${bundel.deel2.length} complete examens en alle uitwerkingen.</p>
        <a class="knop" href="${bundel.bestand}" target="_blank" rel="noopener">Bekijk de bundel (pdf)</a></div></aside>` : '';
    if (perExamen) {
      const rijen = v.examens.map(e => {
        const q = data.vragen.filter(x => x.examen === e.code);
        return `<tr data-href="#/vak/${vak}/examen/${e.code}"><td><a href="#/vak/${vak}/examen/${e.code}">${e.jaar}</a></td><td>${tv(e.tijdvak)}</td>
          <td class="r">${q.length}</td><td class="r">${q.reduce((s, x) => s + x.punten, 0)}</td><td class="r">${gemaakt(q.map(x => x.id))} van ${q.length}</td></tr>`;
      }).join('');
      toon(kop + bundelRegel + `<div class="tabelvak"><table class="tabel"><thead><tr><th>Jaar</th><th>Tijdvak</th><th class="r">Vragen</th><th class="r">Punten</th><th class="r">Gemaakt</th></tr></thead><tbody>${rijen}</tbody></table></div>`, vakNaam(vak), vak);
      return klikbareRijen(app.querySelector('.tabel'));
    }
    toon(kop + bundelRegel + `<div class="inhoud">${v.domeinen.map((d, i) => `<section class="hoofdstuk"><h2><span class="hnr">${i + 1}</span>${esc(d.naam)}</h2>${d.onderwerpen.map((o, j) => {
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

  // goede gratis uitleg elders, plus een zoekopdracht voor precies dit onderwerp
  function uitlegBlok(vak, titel, alle) {
    const bronnen = alle[familie(vak)] || [];
    const zoek = `https://www.youtube.com/results?search_query=${enc(`${titel} ${OVERZICHT.vakken[vak].naam} ${niv(vak)} uitleg`)}`;
    return `<aside class="uitleg"><h2>Uitleg nodig?</h2>
      <p>Hier staan alleen examenvragen. Snap je de stof nog niet goed, kijk dan eerst bij een van deze gratis bronnen:</p>
      <ul>${bronnen.map(([n, u, w]) => `<li><a href="${u}" target="_blank" rel="noopener">${esc(n)}</a> <span>${esc(w)}</span></li>`).join('')}
        <li><a href="${zoek}" target="_blank" rel="noopener">Zoek op YouTube naar uitleg over ${esc(titel.toLowerCase())}</a></li></ul>
      <p class="klein">Deze sites hebben niets met Eindexamen Oefenen te maken; ze staan hier omdat ze goed en gratis zijn.</p></aside>`;
  }

  // ---------- lijst van vragen ----------
  const FILTERS = { alle: () => true, recent: q => q.jaar >= 2022, ouder: q => q.jaar < 2022, open: q => !lees()[q.id] };
  let filter = 'alle';

  async function lijstPagina(vak, soort, sleutel) {
    const v = OVERZICHT.vakken[vak];
    if (!v) return nietGevonden();
    const data = await vakData(vak);
    let vragen, titel, sub, lijstId, boven;
    if (soort === 'onderwerp') {
      const o = onderwerp(vak, sleutel);
      if (!o) return nietGevonden();
      vragen = data.vragen.filter(q => q.onderwerp === sleutel)
        .sort((a, b) => b.jaar - a.jaar || b.tijdvak - a.tijdvak || a.vraag - b.vraag);
      titel = o.naam;
      boven = `${vakNaam(vak)} · paragraaf ${nummer(vak, sleutel)} · syllabus ${o.code}`;
      const inExamens = new Set(vragen.map(q => q.examen)).size;
      sub = `${o.omschrijving} Dit onderwerp kwam voor in ${inExamens} van de ${v.examens.length} examens en levert gemiddeld ${komma(perExamen(vak, o))} punten per examen op.`;
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
      <div class="filters" role="group" aria-label="Filter"><span>Toon:</span>
        <button data-f="alle">alle ${vragen.length} vragen</button>
        ${soort === 'onderwerp' ? `<button data-f="recent">2022 en later</button><button data-f="ouder">2018–2021</button>` : ''}
        <button data-f="open">nog niet gemaakt</button>
      </div>
      <div class="tabelvak"><table class="tabel">
        <thead><tr>${soort === 'onderwerp' ? kolom : ''}<th>Vraag</th><th>Opgave</th>${soort === 'examen' ? kolom : ''}<th class="r">Punten</th><th class="r">Jouw score</th></tr></thead>
        <tbody id="rijen"></tbody></table></div>
      ${soort === 'onderwerp' ? uitlegBlok(vak, titel, await uitleg()) : ''}`, titel, vak);
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
    // de lijst waar de leerling vandaan komt, voor vorige en volgende (een onbekende lijst: het onderwerp van de vraag)
    const maakReeks = l => (l.startsWith('e-') ? data.vragen.filter(x => x.examen === l.slice(2)).sort((a, b) => a.vraag - b.vraag) : data.vragen.filter(x => x.onderwerp === l.slice(2)));
    let reeks = lijst ? maakReeks(lijst) : [];
    if (!reeks.some(x => x.id === id)) { lijst = `o-${q.onderwerp}`; reeks = maakReeks(lijst); }
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
            <div><dt>Vraagcode</dt><dd><span class="code">${esc(q.id)}</span><br><a href="${meldLink(vak, q)}">Fout gezien? Meld het</a></dd></div>
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
          <p class="bronregel">Bron: centraal examen ${esc(vakNaam(vak))} ${q.jaar}, ${tv(q.tijdvak)}, vraag ${q.vraag}. College voor Toetsen en Examens, ${link(pdf.opgaven, 'examenblad.nl') || 'examenblad.nl'}.</p>
          ${q.uitwerkbijlage ? `<p class="opmerking">Bij deze vraag hoort een uitwerkbijlage. ${pdf.uitwerkbijlage ? `<a href="${pdf.uitwerkbijlage}" target="_blank" rel="noopener">Open de uitwerkbijlage (pdf)</a>.` : `Die staat achterin de <a href="${pdf.opgaven}" target="_blank" rel="noopener">originele opgaven (pdf)</a>.`}</p>` : ''}
          ${FORMULEBLAD.includes(vak) ? `<p class="opmerking">Het formuleblad staat voorin de <a href="${pdf.opgaven}" target="_blank" rel="noopener">originele opgaven (pdf)</a>.</p>` : ''}
          ${v.opmerking ? `<p class="opmerking">${esc(v.opmerking)}</p>` : ''}
          <div class="acties"><button class="knop vol" id="toon" aria-expanded="false">Bekijk het antwoordmodel</button>${q.hint ? '<button class="knop stil" id="tipknop" aria-expanded="false" aria-controls="tip">Geef een tip</button>' : ''}</div>
          ${q.hint ? `<p class="tip" id="tip" hidden><b>Tip</b>${esc(q.hint)}</p>` : ''}
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

    const tipknop = document.getElementById('tipknop'), tip = document.getElementById('tip');
    if (tipknop) tipknop.addEventListener('click', () => {
      tip.hidden = !tip.hidden;
      tipknop.setAttribute('aria-expanded', String(!tip.hidden));
      tipknop.textContent = tip.hidden ? 'Geef een tip' : 'Verberg de tip';
    });
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

  // een foutmelding: mail met de vraagcode, of de contactpagina zolang er geen meldadres is
  const meldLink = (vak, q) => (MELDADRES
    ? `mailto:${MELDADRES}?subject=${enc(`Fout bij vraag ${q.id}`)}&body=${enc(`${vakNaam(vak)}, examen ${q.jaar} ${tv(q.tijdvak)}, vraag ${q.vraag}\nVraagcode: ${q.id}\n\nWat klopt er niet?\n`)}`
    : '#/over/fouten');

  // ---------- over deze site ----------
  function overPagina(sectie) {
    zetKruimel([['Start', '#/'], ['Over deze site', null]]);
    const vk = Object.values(OVERZICHT.vakken);
    const vragen = vk.reduce((t, v) => t + v.vragen, 0);
    const jaren = vk.flatMap(v => v.examens.map(e => e.jaar));
    const vakken = [...new Set(vk.map(v => v.naam.replace(/ [ABC]$/, '')))];
    const delen = [
      ['wat', 'Wat is Eindexamen Oefenen?', `
        <ul class="cijfers"><li><b>${vragen.toLocaleString('nl-NL')}</b>examenvragen</li><li><b>${vk.length}</b>vakken op havo en vwo</li><li><b>${Math.min(...jaren)}–${Math.max(...jaren)}</b>centrale examens</li></ul>
        <p>Eindexamen Oefenen zet alle vragen uit de centrale examens van ${vakken.slice(0, -1).join(', ').toLowerCase()} en ${vakken[vakken.length - 1].toLowerCase()} op een rij, geordend per onderwerp, zoals in een examenbundel. Zo oefen je gericht met de onderwerpen waar je nog punten kunt halen.</p>
        <p>Je maakt elke vraag zoals hij op het examen stond, kijkt hem na met het officiële antwoordmodel en geeft jezelf punten. Bij <b>Mijn voortgang</b> zie je per onderwerp hoe het gaat en waar je het beste verder kunt oefenen.</p>`],
      ['werkwijze', 'Hoe is het gemaakt?', `
        <ul>
          <li><b>De vragen en antwoordmodellen</b> komen uit de originele examens en correctievoorschriften van het College voor Toetsen en Examens, zoals gepubliceerd op <a href="https://www.examenblad.nl" target="_blank" rel="noopener">examenblad.nl</a>. Ze zijn letterlijk uit de pdf's overgenomen, met de inleiding, figuren en tabellen die bij de vraag horen. In 2020 waren er geen centrale examens.</li>
          <li><b>De indeling per onderwerp</b> volgt de subdomeinen uit de syllabus van elk vak. Elke vraag is afzonderlijk gelezen en ingedeeld, niet automatisch op trefwoorden: met hulp van AI (Claude), en met een ervaren bijlesdocent die meekijkt. Raakt een vraag meerdere onderwerpen, dan staat hij bij het onderwerp waar hij het meest over gaat.</li>
          <li><b>De tips</b> bij de vragen zijn zelf geschreven. Ze geven een richting of een eerste stap, nooit het antwoord.</li>
        </ul>`],
      ['wie', 'Wie maakt dit?', `
        <p>Eindexamen Oefenen is een onafhankelijk project. Het begon met een simpele ergernis: de examens zelf zijn openbaar en van iedereen, maar wie ze per onderwerp wil oefenen, moet daar meestal voor betalen.</p>
        <p>De site wordt actief bijgehouden. Na elk examen komen de nieuwe vragen erbij, worden ze ingedeeld en nagelopen, en worden fouten die leerlingen en docenten melden verbeterd. Wat er wanneer veranderd is, staat in het <a href="#/logboek">logboek</a>.</p>
        <p>De site is en blijft gratis, zonder reclame en zonder account.</p>`],
      ['privacy', 'Privacy', `
        <p>Kort gezegd: deze site verzamelt niets over jou.</p>
        <ul>
          <li>Je hebt geen account nodig en de site gebruikt geen cookies, geen advertenties en geen bezoekersstatistieken.</li>
          <li>De punten die je jezelf geeft, worden alleen in deze browser op je eigen apparaat bewaard (in de <i>local storage</i>). Ze worden nergens naartoe gestuurd. Je wist ze bij <b>Mijn voortgang</b> van een vak, of door de browsergegevens van deze site te verwijderen.</li>
          <li>De site draait op GitHub Pages. Zoals bij elke website ziet de server technische gegevens zoals je IP-adres; GitHub gebruikt die alleen om de site te laten werken en te beveiligen.</li>
          <li>De lettertypes staan op de site zelf, dus er gaat geen verzoek naar Google of andere partijen. Pas als je op een link naar een originele pdf klikt, ga je naar examenblad.nl.</li>
        </ul>`],
      ['fouten', 'Een fout gezien?', `
        <p>Bij ruim ${Math.floor(vragen / 100) * 100} vragen kan er iets misgaan: een vraag bij het verkeerde onderwerp, een onduidelijke tip of een beeld dat niet goed is uitgesneden. Meld het, dan wordt het verbeterd.</p>
        <p>Bij elke vraag staat in de kantlijn een <b>vraagcode</b>, bijvoorbeeld <span class="code">ha-1018-a-25-1:12</span>. Vermeld die code, dan is de vraag direct terug te vinden.</p>
        <p>${MELDADRES ? `Mail je melding naar <a href="mailto:${MELDADRES}">${MELDADRES}</a>.` : `Meld het via <a href="${MELDPAGINA}" target="_blank" rel="noopener">deze pagina op GitHub</a>, waar de site wordt bijgehouden. Je hebt daar een gratis account voor nodig.`}</p>`],
      ['disclaimer', 'Disclaimer', `
        <p>Eindexamen Oefenen is geen officiële site van het College voor Toetsen en Examens of examenblad.nl. De vragen en antwoordmodellen zijn officieel; de indeling per onderwerp, de tips en het advies bij Mijn voortgang zijn eigen werk.</p>
        <p>Bij het nakijken geldt altijd het originele correctievoorschrift, inclusief eventuele aanvullingen. Die vind je via de links bij elke vraag. Aan de site kunnen geen rechten worden ontleend.</p>`],
    ];
    toon(`<header class="lijstkop"><p class="bovenkop">Over deze site</p><h1>Eerlijk oefenen met echte examens</h1></header>
      <div class="over">
        <nav class="over-inhoud" aria-label="Inhoud">${delen.map(([id, t]) => `<a href="#/over/${id}">${t}</a>`).join('')}</nav>
        <div class="over-tekst">${delen.map(([id, t, h]) => `<section id="${id}"><h2>${t}</h2>${h}</section>`).join('')}</div>
      </div>
      ${hulpBlok()}`, 'Over deze site');
    const doel = sectie && document.getElementById(sectie);
    if (doel) doel.scrollIntoView();
  }

  // ---------- logboek ----------
  async function logboekPagina() {
    zetKruimel([['Start', '#/'], ['Logboek', null]]);
    const l = await logboek();
    toon(`<header class="lijstkop"><p class="bovenkop">Logboek</p><h1>Wat er is veranderd</h1>
        <p class="inleiding">Deze site wordt actief bijgehouden. Hier staat wat er wanneer is toegevoegd of verbeterd, het nieuwste bovenaan.</p></header>
      <ol class="logboek">${l.map(x => `<li><time datetime="${x.datum}">${dagNL(x.datum)}</time><div><b>${esc(x.titel)}</b><p>${esc(x.tekst)}</p></div></li>`).join('')}</ol>
      ${hulpBlok()}`, 'Logboek');
  }

  // ---------- voor docenten ----------
  function docentenPagina() {
    zetKruimel([['Start', '#/'], ['Voor docenten', null]]);
    const vk = Object.values(OVERZICHT.vakken);
    const vragen = vk.reduce((t, v) => t + v.vragen, 0);
    toon(`<header class="lijstkop"><p class="bovenkop">Voor docenten</p><h1>In de les of als huiswerk</h1>
        <p class="inleiding">Eindexamen Oefenen is gemaakt voor leerlingen, maar werkt ook goed in de klas. Alles is gratis, er is geen account nodig en er is geen reclame, dus u kunt er leerlingen zonder bezwaar naar verwijzen.</p></header>
      <div class="over"><div class="over-tekst">
        <section><h2>Wat er op staat</h2>
          <p>Alle ${vragen.toLocaleString('nl-NL')} vragen uit de centrale examens wiskunde A, B en C, natuurkunde, scheikunde en biologie voor havo en vwo sinds 2018. Elke vraag staat bij één onderwerp uit de syllabus (met de syllabuscode), samen met de inleiding en figuren van de opgave en het officiële correctievoorschrift.</p></section>
        <section><h2>Zo gebruiken docenten het</h2>
          <ul>
            <li><b>Na een hoofdstuk:</b> geef de link naar het onderwerp mee. Leerlingen zien dan meteen hoe de stof op het examen terugkomt, van het nieuwste examen naar het oudste.</li>
            <li><b>In de examenklas:</b> laat leerlingen bij <b>Mijn voortgang</b> kijken welke onderwerpen de meeste punten opleveren en waar zij nog punten laten liggen.</li>
            <li><b>Op papier:</b> de <a href="#/bundels">examenbundels</a> mogen vrij worden geprint en gedeeld, ook voor een hele klas.</li>
            <li><b>Een complete toets:</b> onder <i>Per examen</i> staat elk examen in zijn geheel, met links naar de originele pdf's.</li>
          </ul></section>
        <section><h2>Hoe betrouwbaar is de indeling?</h2>
          <p>Elke vraag is afzonderlijk gelezen en ingedeeld bij het onderwerp waar hij het meest over gaat, met hulp van AI (Claude) en met een ervaren bijlesdocent die meekijkt. Raakt een vraag meerdere onderwerpen, dan staat hij er één keer. De vragen en antwoordmodellen zelf zijn ongewijzigd overgenomen van examenblad.nl; bij het nakijken geldt altijd het originele correctievoorschrift met eventuele aanvullingen.</p></section>
        <section><h2>Iets gezien dat niet klopt?</h2>
          <p>Docenten vinden fouten het snelst. Een vraag bij een verkeerd onderwerp, een te ruime tip of een slecht uitgesneden figuur: <a href="#/over/fouten">meld het</a>, dan wordt het aangepast en komt het in het <a href="#/logboek">logboek</a>.</p></section>
      </div></div>`, 'Voor docenten');
  }

  // ---------- examenbundels (pdf) ----------
  async function bundelPagina(doel) {
    zetKruimel([['Start', '#/'], ['Examenbundels', null]]);
    // havo eerst, dan vwo; binnen een niveau in de volgorde van het vakkenmenu
    const volg = Object.keys(OVERZICHT.vakken);
    const b = [...await bundels()].sort((x, y) => volg.indexOf(x.vak) - volg.indexOf(y.vak));
    const reeks = l => l.length > 1 ? `${l[0]} t/m ${l[l.length - 1]}` : l[0];
    const kaarten = b.map(x => `<article class="bundel" id="bundel-${x.vak}">
        <a class="bundel-omslag" href="${x.bestand}" target="_blank" rel="noopener" aria-label="Open de examenbundel ${esc(vakNaam(x.vak))}"><img src="${x.omslag}" alt="" width="250" height="354" loading="lazy"></a>
        <div class="bundel-tekst">
          <p class="bovenkop">${niv(x.vak)}</p>
          <h2>${esc(OVERZICHT.vakken[x.vak].naam)}</h2>
          <dl>
            <div><dt>Deel 1, per onderwerp</dt><dd>${x.deel1.length} examens (${reeks(x.deel1)})</dd></div>
            <div><dt>Deel 2, complete examens</dt><dd>${x.deel2.join(', ')}</dd></div>
            <div><dt>Omvang</dt><dd>${x.paginas} pagina's A5 · pdf, ${komma(x.mb)} MB</dd></div>
          </dl>
          <div class="bundel-knoppen">
            <a class="knop vol" href="${x.bestand}" target="_blank" rel="noopener">Bekijk online</a>
            <a class="knop" href="${x.bestand}" download>Download</a>
          </div>
        </div>
      </article>`).join('');
    toon(`<header class="lijstkop"><p class="bovenkop">Gratis · pdf om te printen</p><h1>Examenbundels</h1>
        <p class="inleiding">Een complete examenbundel op A5, gratis. In deel 1 staan de opgaven uit eerdere examens per onderwerp, net als op deze site. In deel 2 staan de drie nieuwste examens compleet, zodat je een echt examen op tijd kunt oefenen. Achterin vind je de uitwerkingen: het officiële correctievoorschrift bij elke vraag.</p>
      </header>
      ${b.length ? `<div class="bundels">${kaarten}</div>` : '<p class="leeg">Er staan nog geen examenbundels online.</p>'}
      <p class="bundel-noot">Print op A5, of op A4 met twee pagina's per vel. De vragen en antwoorden komen van het CvTE (examenblad.nl); bij het nakijken geldt altijd het originele correctievoorschrift. </p>
      ${hulpBlok()}`, 'Examenbundels');
    const el = doel && document.getElementById(`bundel-${doel}`);
    if (el) { el.scrollIntoView(); el.classList.add('licht'); }
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
      const hash = location.hash;
      if (!OVERZICHT) {
        OVERZICHT = await json('data/vakken.json');
        // laatst bijgewerkt: de nieuwste van de gegevens en het logboek
        logboek().then(l => {
          const data = [OVERZICHT.bijgewerkt, ...l.map(x => x.datum)].filter(Boolean).sort();
          if (data.length) document.getElementById('bijgewerkt').textContent = `Laatst bijgewerkt: ${dagNL(data[data.length - 1])}`;
        });
      }
      // eerst de vakgegevens laden; is de leerling intussen al verder geklikt, dan deze pagina niet meer tonen
      if (d[1] && OVERZICHT.vakken[d[1]]) await vakData(d[1]);
      if (hash !== location.hash) return;
      if (!d[0]) return begin();
      if (d[0] === 'vak' && d[2] === 'voortgang') return voortgangPagina(d[1]);
      if (d[0] === 'vak' && d.length === 2) return vakPagina(d[1], /per=examen/.test(zoek || ''));
      if (d[0] === 'vak' && d[2] === 'onderwerp') return lijstPagina(d[1], 'onderwerp', d[3]);
      if (d[0] === 'vak' && d[2] === 'examen') return lijstPagina(d[1], 'examen', d[3]);
      if (d[0] === 'vraag') return vraagPagina(d[1], d[2], d[3]);
      if (d[0] === 'over') return overPagina(d[1]);
      if (d[0] === 'bundels') return bundelPagina(d[1]);
      if (d[0] === 'logboek') return logboekPagina();
      if (d[0] === 'docenten') return docentenPagina();
      nietGevonden();
    } catch (e) {
      console.error(e);
      app.innerHTML = '<p class="leeg">Er ging iets mis bij het laden. Probeer het opnieuw.</p>';
    }
  }
  window.addEventListener('hashchange', () => { filter = 'alle'; route(); });
  route();
})();
