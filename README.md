# Eindexamen Oefenen

Een web-app waarin leerlingen echte centrale examenvragen wiskunde oefenen per onderwerp, zoals in een examenbundel.
De leerling kiest niveau en vak, klikt op een onderwerp en krijgt een lijst van alle examenvragen over dat onderwerp
(met jaar, tijdvak, opgave en vraagnummer). Per vraag staan de inleiding, figuren en tabellen precies zoals in het examen,
met daaronder het antwoordmodel uit het correctievoorschrift. De leerling geeft zichzelf punten; de voortgang blijft
in de browser. Bij *Mijn voortgang* ziet de leerling per onderwerp zijn score en een advies wat hij nu het beste
kan oefenen (lage score en veel punten per examen gaan voor). Bij elke vraag kan de leerling een korte hint openen.

Nu: havo wiskunde A en B, vwo wiskunde A, B en C, examenjaren 2018 t/m 2026 (2020 had geen centrale examens).

## Opbouw

| Map | Inhoud |
|---|---|
| `docs/` | De site (statisch, GitHub Pages): `index.html`, `app.js`, `app.css`, `data/*.json`, `img/<examen>/` |
| `tools/haal_op.py` | Haalt opgaven, correctievoorschriften en uitwerkbijlagen op van examenblad.nl |
| `tools/bouw_databank.py` | Leest de teksten in: per vraag opgave, nummer, punten, vraagtekst en antwoordmodel |
| `tools/snij.py` | Snijdt per vraag het stuk van de opgave en het antwoordmodel uit de pdf (WebP-beelden) |
| `tools/bouw_site.py` | Zet de onderwerpen per vak (volgens de syllabus) en de vragen klaar in `docs/data/` |
| `hints/<vak>.json` | Per vraag een korte hint (zonder het antwoord), met de hand geschreven op basis van vraag en antwoordmodel |
| `indeling/<vak>.json` | Het onderwerp van elke vraag, met de hand ingedeeld volgens de subdomeinen van de syllabus |
| `bronnen/` | Documentenlijst, databank, teksten en syllabi (de pdf's zelf staan niet in git) |

## Bijwerken met nieuwe examens

```sh
python3 tools/haal_op.py          # nieuwe documenten ophalen (bestaande worden overgeslagen)
python3 tools/bouw_databank.py    # vragen inlezen
python3 tools/snij.py             # beelden snijden (Python met Pillow nodig)
# nieuwe vragen een onderwerp geven in indeling/<vak>.json
python3 tools/bouw_site.py        # site-gegevens bijwerken
```

`snij.py` en `bouw_site.py` melden vragen die ze niet konden plaatsen.

## Bron

De examens en correctievoorschriften zijn van het College voor Toetsen en Examens (CvTE), gepubliceerd op
[examenblad.nl](https://www.examenblad.nl). © Staat der Nederlanden. Hergebruik is toegestaan met bronvermelding
(examenblad.nl/over-examenblad/copyright). Bij elke vraag staat de bron met een link naar het originele examen.
