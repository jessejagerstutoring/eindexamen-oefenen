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
| `docs/` | De site (statisch, GitHub Pages): `index.html`, `app.js`, `app.css`, `data/*.json`, `img/<examen>/`, `fonts/` (lettertypes zelf gehost, SIL OFL), `og.png` (deelafbeelding) |
| `tools/haal_op.py` | Haalt opgaven, correctievoorschriften en uitwerkbijlagen op van examenblad.nl |
| `tools/bouw_databank.py` | Leest de teksten in: per vraag opgave, nummer, punten, vraagtekst en antwoordmodel |
| `tools/snij.py` | Snijdt per vraag het stuk van de opgave en het antwoordmodel uit de pdf (WebP-beelden) |
| `tools/bouw_site.py` | Zet de onderwerpen per vak (volgens de syllabus) en de vragen klaar in `docs/data/` |
| `hints/<vak>.json` | Per vraag een korte hint (zonder het antwoord), met de hand geschreven op basis van vraag en antwoordmodel |
| `indeling/<vak>.json` | Het onderwerp van elke vraag, met de hand ingedeeld volgens de subdomeinen van de syllabus |
| `bronnen/` | Documentenlijst, databank, teksten en syllabi (de pdf's zelf staan niet in git) |

## Bijwerken met nieuwe examens

```sh
python3 tools/haal_op.py          # nieuwe documenten ophalen (bestaande worden overgeslagen); vakken als argument,
                                  # bv. natuurkunde scheikunde biologie --niveau havo vwo
python3 tools/bouw_databank.py    # vragen inlezen
python3 tools/snij.py             # beelden snijden (Python met Pillow nodig)
# nieuwe vragen een onderwerp geven in indeling/<vak>.json en een hint in hints/<vak>.json
python3 tools/bouw_site.py        # site-gegevens bijwerken
```

`snij.py` en `bouw_site.py` melden vragen die ze niet konden plaatsen.

## Bron

De examens en correctievoorschriften zijn van het College voor Toetsen en Examens (CvTE), gepubliceerd op
[examenblad.nl](https://www.examenblad.nl). © Staat der Nederlanden. Hergebruik is toegestaan met bronvermelding
(examenblad.nl/over-examenblad/copyright). Bij elke vraag staat de bron met een link naar het originele examen.

## Oefenboek als pdf (A5)

`tools/bouw_bundel.py` maakt per vak een oefenboek zoals een examenbundel: deel 1 met de opgaven per onderwerp
(vraagnummers lopen door), deel 2 met de nieuwste examens compleet, achterin de uitwerkingen uit het
correctievoorschrift (met de aanvullingen van het CvTE). Vragen en antwoorden zijn vectoruitsneden uit de originele
pdf's, met dezelfde snijlijnen als de site (`snij.posities`). Het boek blijft binnen het maximale aantal pagina's door
de oudste examens weg te laten. Natuurkunde havo is het voorbeeldboek.

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
anders de algemene versies. `bundels/bouw/<vak>/keuze.json` onthoudt welke examens pasten en welke selectie te veel
pagina's gaf.

Opmaakregels die het script afdwingt: tekst ca. 10 pt (12 pt × 0,84); figuren mogen iets krimpen om nog op de pagina
te passen (vragen tot 85 %, uitwerkingen tot 70 %); in de uitwerkingen gaat de witruimte van het origineel half mee;
schrijfregels van de uitwerkbijlagen vallen weg; een opgavetitel blijft bij het begin van de opgave.

Nodig: LuaLaTeX (TinyTeX met o.a. tikz, fancyhdr, sourceserif, sourcesans, xurl, hyphen-dutch), poppler, en Pillow,
numpy en pikepdf. Opmaak en vaste teksten staan in `tools/bundel/`. Uitvoer: `bundels/<vak>.pdf` (niet in git; de gepubliceerde kopie staat in `docs/bundels/`).
