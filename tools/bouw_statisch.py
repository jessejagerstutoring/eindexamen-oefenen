"""
Maakt vaste pagina's per vak en per onderwerp, zodat zoekmachines ze kunnen vinden.

De site zelf werkt met adressen achter een # (bijv. #/vak/natuurkunde-havo/onderwerp/elektriciteit). Die leest Google
slecht. Dit script zet voor elk vak en elk onderwerp een gewone html-pagina neer met een eigen adres, een titel en
een korte inhoud (wat het onderwerp is, hoe vaak het op het examen komt, welke vragen er zijn). Elke vraag linkt door
naar de oefenpagina in de site.

Draaien (vanuit de map eindexamen-oefenen, na bouw_site.py):
    python3 tools/bouw_statisch.py

Uitvoer:
    docs/onderwerpen/index.html                 alle vakken en onderwerpen op één pagina
    docs/<vak>/index.html                       per vak de onderwerpen
    docs/<vak>/<onderwerp>/index.html           per onderwerp de examenvragen
    docs/sitemap.xml, docs/robots.txt
"""
import html
import json
import shutil
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent
DOCS = ROOT / 'docs'
BASIS = 'https://jessejagerstutoring.github.io/eindexamen-oefenen/'
TV = {1: 'tijdvak 1', 2: 'tijdvak 2'}
ROM = {1: 'I', 2: 'II'}


def e(s):
    return html.escape(str(s), quote=True)


def pagina(titel, beschrijving, pad, inhoud, diepte):
    """Een complete pagina in de huisstijl van de site; diepte = aantal mappen onder docs/."""
    op = '../' * diepte
    return f'''<!doctype html>
<html lang="nl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>{e(titel)}</title>
  <meta name="description" content="{e(beschrijving)}">
  <link rel="canonical" href="{BASIS}{pad}">
  <meta property="og:type" content="website">
  <meta property="og:locale" content="nl_NL">
  <meta property="og:site_name" content="Eindexamen Oefenen">
  <meta property="og:title" content="{e(titel)}">
  <meta property="og:description" content="{e(beschrijving)}">
  <meta property="og:url" content="{BASIS}{pad}">
  <meta property="og:image" content="{BASIS}og.png">
  <meta name="theme-color" content="#1b365d">
  <link rel="icon" href="{op}icoon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="{op}app.css">
</head>
<body>
  <header class="kop">
    <div class="kop-in">
      <a class="merk" href="{op}" aria-label="Naar het begin">
        <span class="merk-naam">Eindexamen Oefenen</span>
        <span class="merk-sub">Centrale examens per onderwerp</span>
      </a>
      <nav class="sitenav" aria-label="Hoofdmenu">
        <a href="{op}">Vakken</a><a href="{op}#/bundels">Examenbundels</a><a href="{op}#/docenten">Voor docenten</a><a href="{op}#/logboek">Logboek</a><a href="{op}#/over">Over</a>
      </nav>
    </div>
  </header>
  <main class="app statisch">
{inhoud}
  </main>
  <footer class="voet">
    <div class="voet-in">
      <p class="voet-onder"><span>Eindexamen Oefenen is een onafhankelijk project en geen officiële site van het CvTE of examenblad.nl.
      De examenvragen en antwoordmodellen komen van het College voor Toetsen en Examens (examenblad.nl), © Staat der Nederlanden.</span>
      <span><a href="{op}onderwerpen/">Alle onderwerpen</a></span></p>
    </div>
  </footer>
</body>
</html>
'''


def schrijf(pad, tekst):
    p = DOCS / pad / 'index.html'
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(tekst)


def main():
    ov = json.loads((DOCS / 'data' / 'vakken.json').read_text())
    uitleg = json.loads((DOCS / 'data' / 'uitleg.json').read_text())['bronnen']
    niveaus = ov['niveaus']
    paden = ['', 'onderwerpen/']
    overzicht = []
    for vak, v in ov['vakken'].items():
        data = json.loads((DOCS / 'data' / f'{vak}.json').read_text())
        niv = niveaus[v['niveau']]
        naam = f"{v['naam']} {niv.lower()}"
        zin = naam[:1].lower() + naam[1:]          # midden in een zin: 'natuurkunde havo'
        nex = len(v['examens'])
        jaren = sorted({x['jaar'] for x in v['examens']})
        laatste = v['examens'][0]
        # oude vaste pagina's van dit vak opruimen (onderwerpen kunnen hernoemd zijn)
        if (DOCS / vak).exists():
            shutil.rmtree(DOCS / vak)
        rijen_vak = []
        for i, d in enumerate(v['domeinen'], 1):
            rijen_vak.append(f'<section class="hoofdstuk"><h2><span class="hnr">{i}</span>{e(d["naam"])}</h2>')
            for j, o in enumerate(d['onderwerpen'], 1):
                vr = sorted([q for q in data['vragen'] if q['onderwerp'] == o['id']],
                            key=lambda q: (-q['jaar'], -q['tijdvak'], q['vraag']))
                in_ex = len({q['examen'] for q in vr})
                per = f"{o['punten'] / nex:.1f}".replace('.', ',') if nex else '0'
                pad = f'{vak}/{o["id"]}/'
                paden.append(pad)
                rijen_vak.append(f'''<a class="paragraaf" href="{o['id']}/">
          <span class="pnr">{i}.{j}</span>
          <span class="pmid"><span class="ptitel">{e(o['naam'])}</span><span class="syl">{e(o['code'])}</span><span class="stip"></span></span>
          <span class="pcijfers"><b>{o['vragen']}</b> vragen · {o['punten']} p</span>
          <span class="pomschr">{e(o['omschrijving'])}</span></a>''')
                vragenrijen = ''.join(
                    f'<tr><td class="zacht">{q["jaar"]}-{ROM[q["tijdvak"]]}</td><td class="vnr">{q["vraag"]}</td>'
                    f'<td><a href="../../#/vraag/{vak}/{e(q["id"])}/o-{o["id"]}">{e(q.get("opgave") or "Opgave")}</a></td>'
                    f'<td class="r">{q["punten"]}</td></tr>' for q in vr)
                bronnen = ''.join(f'<li><a href="{e(u)}" rel="noopener">{e(n)}</a> <span>{e(w)}</span></li>'
                                  for n, u, w in uitleg.get(vak.split('-')[0], []))
                inhoud = f'''    <nav class="kruimel-statisch"><a href="../../">Start</a> › <a href="../">{e(naam)}</a> › {e(o['naam'])}</nav>
    <header class="lijstkop"><p class="bovenkop">{e(naam)} · syllabus {e(o['code'])}</p>
      <h1>Examenvragen {e(o['naam'].lower())}</h1>
      <p class="inleiding">{e(o['omschrijving'])} Dit onderwerp kwam voor in {in_ex} van de {nex} centrale examens {e(zin)} sinds {jaren[0]}
      en levert gemiddeld {per} punten per examen op.</p>
      <p><a class="knop vol" href="../../#/vak/{vak}/onderwerp/{o['id']}">Oefen deze {len(vr)} vragen</a></p></header>
    <div class="tabelvak"><table class="tabel">
      <thead><tr><th>Examen</th><th>Vraag</th><th>Opgave</th><th class="r">Punten</th></tr></thead>
      <tbody>{vragenrijen}</tbody></table></div>
    <aside class="uitleg"><h2>Uitleg nodig?</h2><p>Hier staan alleen examenvragen, met het officiële correctievoorschrift. Voor uitleg van de stof zijn dit goede gratis bronnen:</p><ul>{bronnen}</ul></aside>
    <p class="bronregel">Alle vragen komen uit de centrale examens {e(zin)} van {jaren[0]} tot en met {laatste['jaar']} ({TV[laatste['tijdvak']]}), gepubliceerd door het College voor Toetsen en Examens op examenblad.nl.</p>'''
                titel = f"Examenvragen {o['naam'].lower()} – {naam} | Eindexamen Oefenen"
                besch = (f"Alle {len(vr)} centrale examenvragen over {o['naam'].lower()} voor {zin} ({jaren[0]}–{jaren[-1]}), "
                         f"per vraag met het officiële correctievoorschrift. Gratis, zonder account.")
                schrijf(pad, pagina(titel, besch, pad, inhoud, 2))
            rijen_vak.append('</section>')
        inhoud = f'''    <nav class="kruimel-statisch"><a href="../">Start</a> › {e(naam)}</nav>
    <header class="vakkop"><div><p class="bovenkop">{e(niv)} · centraal examen</p><h1>{e(v['naam'])}</h1>
      <p>{v['vragen']} examenvragen uit {nex} centrale examens ({jaren[0]}–{jaren[-1]}), per onderwerp uit de syllabus.</p>
      <p class="actueel">Bijgewerkt tot en met het examen van {laatste['jaar']}, {TV[laatste['tijdvak']]}.</p></div>
      <p><a class="knop vol" href="../#/vak/{vak}">Naar de oefenpagina</a></p></header>
    <div class="inhoud">{''.join(rijen_vak)}</div>'''
        titel = f"Examenvragen {naam} per onderwerp | Eindexamen Oefenen"
        besch = (f"Alle {v['vragen']} centrale examenvragen {zin} van {jaren[0]} tot en met {jaren[-1]}, ingedeeld per "
                 f"onderwerp uit de syllabus, met het officiële correctievoorschrift. Gratis, zonder account.")
        schrijf(f'{vak}/', pagina(titel, besch, f'{vak}/', inhoud, 1))
        paden.append(f'{vak}/')
        overzicht.append((niv, vak, v))
    # alle onderwerpen op één pagina
    blokken = []
    for niv in niveaus.values():
        blokken.append(f'<h2 class="sectiekop">{e(niv)}</h2>')
        for n, vak, v in overzicht:
            if n != niv:
                continue
            ond = ''.join(f'<li><a href="../{vak}/{o["id"]}/">{e(o["naam"])}</a> <span class="zacht">({o["vragen"]})</span></li>'
                          for d in v['domeinen'] for o in d['onderwerpen'])
            blokken.append(f'<section class="alle-ond"><h3><a href="../{vak}/">{e(v["naam"])}</a></h3><ul>{ond}</ul></section>')
    inhoud = f'''    <header class="lijstkop"><p class="bovenkop">Overzicht</p><h1>Alle onderwerpen</h1>
      <p class="inleiding">Elk onderwerp uit de syllabus met het aantal centrale examenvragen dat erover ging.</p></header>
    {''.join(blokken)}'''
    schrijf('onderwerpen/', pagina('Alle onderwerpen | Eindexamen Oefenen',
                                   'Alle onderwerpen van wiskunde, natuurkunde, scheikunde, nask en biologie vmbo, havo en vwo, met de centrale examenvragen per onderwerp.',
                                   'onderwerpen/', inhoud, 1))
    vandaag = date.today().isoformat()
    (DOCS / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                      + ''.join(f'  <url><loc>{BASIS}{p}</loc><lastmod>{vandaag}</lastmod></url>\n' for p in paden)
                                      + '</urlset>\n')
    (DOCS / 'robots.txt').write_text(f'User-agent: *\nAllow: /\nSitemap: {BASIS}sitemap.xml\n')
    print(f'{len(paden)} pagina\'s in de sitemap')


if __name__ == '__main__':
    main()
