# Eindexamen Oefenen

Een web-app waarin leerlingen echte centrale examenvragen wiskunde, natuurkunde, scheikunde en biologie oefenen per onderwerp, zoals in een examenbundel.
De leerling kiest niveau en vak, klikt op een onderwerp en krijgt een lijst van alle examenvragen over dat onderwerp
(met jaar, tijdvak, opgave en vraagnummer). Per vraag staan de inleiding, figuren en tabellen precies zoals in het examen,
met daaronder het antwoordmodel uit het correctievoorschrift. De leerling geeft zichzelf punten; de voortgang blijft
in de browser. Bij *Mijn voortgang* ziet de leerling per onderwerp zijn score en een advies wat hij nu het beste
kan oefenen (lage score en veel punten per examen gaan voor). Bij elke vraag kan de leerling een korte hint openen.

Nu: havo wiskunde A en B, vwo wiskunde A, B en C, en natuurkunde, scheikunde en biologie op havo en vwo;
examenjaren 2018 t/m 2026 (2020 had geen centrale examens). Samen ruim 4700 vragen.

## Opbouw

| Map | Inhoud |
|---|---|
| `docs/` | De site (statisch, GitHub Pages): `index.html`, `app.js`, `app.css`, `data/*.json`, `img/<examen>/`, `fonts/` (Literata voor koppen en Source Sans 3 voor tekst, zelf gehost, SIL OFL), `og.png` (deelafbeelding) |
| `tools/haal_op.py` | Haalt opgaven, correctievoorschriften en uitwerkbijlagen op van examenblad.nl |
| `tools/bouw_databank.py` | Leest de teksten in: per vraag opgave, nummer, punten, vraagtekst en antwoordmodel |
| `tools/snij.py` | Snijdt per vraag het stuk van de opgave en het antwoordmodel uit de pdf (WebP-beelden) |
| `tools/bouw_site.py` | Zet de onderwerpen per vak (volgens de syllabus) en de vragen klaar in `docs/data/` |
| `tools/bouw_statisch.py` | Maakt vaste, vindbare pagina's per vak en onderwerp (`docs/<vak>/<onderwerp>/`), `docs/onderwerpen/`, `sitemap.xml` en `robots.txt` |
| `docs/data/logboek.json` | Het logboek op de site: wat er wanneer is veranderd, met de hand bijgehouden |
| `docs/data/uitleg.json` | Gratis uitlegbronnen elders per vakgroep (getoond bij elk onderwerp); af en toe nalopen of de links nog werken |
| `hints/<vak>.json` | Per vraag een korte hint (zonder het antwoord), per vraag geschreven met Claude op basis van vraag en antwoordmodel, met een bijlesdocent die meekijkt |
| `indeling/<vak>.json` | Het onderwerp van elke vraag, per vraag gelezen en ingedeeld volgens de subdomeinen van de syllabus (met Claude, niet op trefwoorden) |
| `bronnen/` | Documentenlijst, databank, teksten en syllabi (de pdf's zelf staan niet in git) |

## Bijwerken met nieuwe examens

```sh
python3 tools/haal_op.py          # nieuwe documenten ophalen (bestaande worden overgeslagen); vakken als argument,
                                  # bv. natuurkunde scheikunde biologie --niveau havo vwo
python3 tools/bouw_databank.py    # vragen inlezen
python3 tools/snij.py             # beelden snijden (Python met Pillow nodig)
# nieuwe vragen een onderwerp geven in indeling/<vak>.json en een hint in hints/<vak>.json
python3 tools/bouw_site.py        # site-gegevens bijwerken
python3 tools/bouw_statisch.py    # vaste pagina's per onderwerp en de sitemap bijwerken
```

`snij.py` en `bouw_site.py` melden vragen die ze niet konden plaatsen.

**Na elke wijziging een regel in het logboek** (`docs/data/logboek.json`, nieuwste bovenaan): datum, korte titel en
één of twee zinnen in gewone taal over wat er voor leerlingen is veranderd. De startpagina toont de laatste drie, en
"Laatst bijgewerkt" onderaan de site volgt het logboek. Zo is zichtbaar dat de site wordt bijgehouden.

De site en de bundels noemen geen bedrijf: ze heten Eindexamen Oefenen en verwijzen naar het webadres
(`WEBADRES` in `tools/bouw_bundel.py`). Fouten melden gaat via `MELDADRES` in `docs/app.js` (leeg = via GitHub).

## Bron

De examens en correctievoorschriften zijn van het College voor Toetsen en Examens (CvTE), gepubliceerd op
[examenblad.nl](https://www.examenblad.nl). © Staat der Nederlanden. Hergebruik is toegestaan met bronvermelding
(examenblad.nl/over-examenblad/copyright). Bij elke vraag staat de bron met een link naar het originele examen.

## Oefenboek als pdf (A5)

`tools/bouw_bundel.py` maakt per vak een oefenboek zoals een examenbundel: deel 1 met de opgaven per onderwerp
(vraagnummers beginnen per onderwerp bij 1), deel 2 met de nieuwste examens compleet, achterin de uitwerkingen uit het
correctievoorschrift (met de aanvullingen van het CvTE). Vragen en antwoorden zijn vectoruitsneden uit de originele
pdf's, met dezelfde snijlijnen als de site (`snij.posities`). Het boek blijft binnen het maximale aantal pagina's door
de oudste examens weg te laten. Natuurkunde havo is het voorbeeldboek. Er zijn bundels voor alle elf bètavakken.
Voorin staat een voorwoord (binnenkant omslag), achterin een pagina "Succes met je examen!" met wat
je de avond ervoor en tijdens het examen doet (teksten in `tools/bundel/boek.tex`).

Alle bundels in één keer (drie rijen tegelijk kan, 32 GB geheugen is ruim genoeg): `bundels/bouw/alles.sh <vak> ...`.

```sh
~/env/bin/python tools/bouw_bundel.py natuurkunde-havo            # bouwen (elk vak uit bouw_site.VAKKEN)
~/env/bin/python tools/bouw_bundel.py natuurkunde-havo --opnieuw  # examenkeuze opnieuw bepalen
~/env/bin/python tools/bouw_bundel.py --proef [vak ...]           # droogtest zonder LaTeX (standaard: alle vakken)
~/env/bin/python tools/bouw_bundel.py --publiceer                  # alle gebouwde bundels op de site zetten
```

Werkwijze voor een nieuw vak:

1. `--proef <vak>`: alle vragen geplaatst, niets ontbreekt? Het verslag staat in `bundels/bouw/proef.txt`.
2. Bouwen. Na de bouw staat in `bundels/bouw/<vak>/controle.txt` wat een mens moet nakijken (ontbrekende vragen,
   verkleinde tekst, LaTeX-waarschuwingen, afbreekpatronen, bijna lege pagina's) en in `controle/vel-NN.png` alle
   pagina's in het klein.
3. Alle contactvellen nalopen.
4. `--publiceer`: kopieert elke `bundels/<vak>.pdf` met een omslagplaatje naar `docs/bundels/` en schrijft
   `docs/data/bundels.json`. De site toont ze dan op `#/bundels`, met een link op de startpagina, in de voet en op
   de pagina van het vak. Daarna committen en pushen.

Instellingen: `STANDAARD` < `FAMILIES[<familie>]` < `BOEKEN[<vak>]` bovenin het script (hulpmiddelen, formulekaart,
paginabudget enz.). De examenduur komt uit de voorpagina's, de formulekaart wordt vanzelf herkend. Per familie
(optioneel) `tools/bundel/tips-<familie>.tex` en `tools/bundel/omslag/<familie>.tex` (een lijntekening, geen foto);
anders de algemene versies (`BOEKEN[<vak>]['tips']` kan een andere kiezen, bijv. `wiskunde-a` of `wiskunde-ac-vwo`).
`bundels/bouw/<vak>/keuze.json` onthoudt welke examens pasten en welke selectie te veel
pagina's gaf.

Opmaakregels die het script afdwingt: tekst ca. 10 pt (12 pt × 0,84); figuren mogen iets krimpen om nog op de pagina
te passen (vragen tot 85 %, uitwerkingen tot 70 %); in de uitwerkingen gaat de witruimte van het origineel half mee;
schrijfregels van de uitwerkbijlagen vallen weg; een opgavetitel blijft bij het begin van de opgave; de bronvermelding
staat rechts rafelig en lange adressen en codes mogen breken; super- en subscripten zonder glyph worden gezet.

Uitsneden: steekt een figuur, tabel, foto of aslabel links over de vaste snijlijn, dan schuift de snijlijn voor dat
blok mee (hooguit 6 mm in de marge, de rest door iets kleiner te schalen) en groeit het blok in de hoogte mee; de
oorspronkelijke vraagnummers daarin worden wit afgedekt. Loopt een figuur naast de tekst door over de grens tussen twee
vragen, dan sluiten die stukken naadloos aan (geen witruimte, geen paginabreuk). Een grens schuift langs een exponent of
teller, en tussen twee antwoorden naar een witte regel. Het controleverslag meldt onder "uitsneden" elke plek waar nog
inkt buiten een uitsnede valt; dat moet leeg zijn.

## Andere vakken (onderzoek)

`onderzoek/andere-vakken/` bevat de examens van de talen, Nederlands en de maatschappijvakken (2018–2026, havo en vwo),
een analyse of de methode daar werkt, en een eerste automatische indeling. Los van de site; zie
`onderzoek/andere-vakken/RAPPORT.md` voor het advies per vak.

Nodig: LuaLaTeX (TinyTeX met o.a. tikz, fancyhdr, sourceserif, sourcesans, xurl, hyphen-dutch), poppler, en Pillow,
numpy en pikepdf. Opmaak en vaste teksten staan in `tools/bundel/`. Uitvoer: `bundels/<vak>.pdf` (niet in git; de gepubliceerde kopie staat in `docs/bundels/`).
