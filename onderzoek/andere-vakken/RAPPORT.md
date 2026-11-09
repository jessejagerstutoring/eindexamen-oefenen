# Andere vakken: werkt de methode ook daar?

Onderzoek van november 2026. Alles staat in `onderzoek/andere-vakken/` en raakt de site (`docs/`) en de bètavakken
(`bronnen/`) niet. Of en wanneer deze vakken op de site komen, is een aparte beslissing.

## Kort antwoord

**Technisch werkt de methode bij bijna alle vakken.** Bij 29 van de 33 vakonderdelen vinden de bestaande scripts
**alle vragen en alle antwoordmodellen** terug, met hun positie in de pdf, dus ze kunnen worden uitgesneden zoals nu.
De echte verschillen zitten ergens anders:

1. **Bronnen- en tekstboekjes.** Bij talen, Nederlands, geschiedenis, aardrijkskunde en maatschappijwetenschappen
   staat een groot deel van wat je nodig hebt in een apart boekje. Een vraag los tonen kan alleen als de bijbehorende
   tekst of bron er ook bij komt. Dat moet er voor deze vakken nog bij worden gebouwd.
2. **De indeling per onderwerp.** Bij aardrijkskunde (domein) en geschiedenis (tijdvak) staat die als kopje in het
   examen, dus dat kan automatisch. Bij economie, bedrijfseconomie, filosofie en maatschappijwetenschappen moet het met
   de hand, net als bij de bètavakken. Bij talen past "per onderwerp" niet: daar oefen je per tekst of per vraagtype.
3. **Auteursrecht.** De teksten in de taalexamens komen uit kranten, websites en romans van derden. Het hergebruikrecht
   van het CvTE geldt voor de examens zelf. Of het ook geldt voor die teksten, moet je nagaan voordat je ze publiceert.
   Hetzelfde geldt in mindere mate voor bronnen bij geschiedenis, aardrijkskunde en maatschappijwetenschappen.

**Advies:** houd de site gericht op wiskunde en de bètavakken. Wil je uitbreiden, begin dan met **economie** en
**bedrijfseconomie**: die werken precies zoals de bètavakken (een context met vragen, geen apart boekje), bijna geen
auteursrechtvraag, en veel leerlingen. Daarna komen **aardrijkskunde** en **geschiedenis**, waar de indeling grotendeels
vanzelf gaat maar de bronnen erbij moeten. Talen en Nederlands zijn het meeste werk en hebben de grootste
auteursrechtvraag. Kunst algemeen en muziek vallen af.

## Wat er gemeten is

`analyse.py` gebruikt dezelfde code als de site en de bundels (`tools/snij.py`, `tools/bouw_databank.py`). Per vak,
havo en vwo samen per vakonderdeel, centrale examens 2018–2026 (in 2020 waren er geen):

| Vak | Examens | Vragen | Meerkeuze | Gekoppeld | In pdf | Verwijst naar bron/tekst | Bronnenboekje (blz.) |
|---|---|---|---|---|---|---|---|
| Economie havo | 16 | 465 | 0 % | 100 % | 100 % | 35 % | 5 |
| Economie vwo | 16 | 465 | 0 % | 100 % | 100 % | 0 % | – |
| Bedrijfseconomie havo | 12 | 351 | 3 % | 100 % | 100 % | 0 % | 8 |
| Bedrijfseconomie vwo | 12 | 363 | 1 % | 100 % | 100 % | 0 % | 9 |
| Filosofie havo | 16 | 401 | 0 % | 100 % | 100 % | 25 % | – |
| Filosofie vwo | 16 | 345 | 0 % | 100 % | 100 % | 26 % | – |
| Aardrijkskunde havo | 16 | 453 | 0 % | 100 % | 100 % | 75 % | 10 |
| Aardrijkskunde vwo | 16 | 445 | 0 % | 100 % | 100 % | 75 % | 8 |
| Geschiedenis havo | 16 | 415 | 0 % | 100 % | 100 % | 53 % | 10 |
| Geschiedenis vwo | 16 | 419 | 0 % | 100 % | 100 % | 55 % | 11 |
| Maatschappijwetenschappen havo | 16 | 411 | 3 % | 100 % | 100 % | 76 % | 8 |
| Maatschappijwetenschappen vwo | 16 | 413 | 1 % | 97 % | 100 % | 74 % | 10 |
| Nederlands havo | 16 | 617 | 32 % | 97 % | 100 % | alle (per tekst) | 11 |
| Nederlands vwo | 16 | 612 | 27 % | 99 % | 100 % | alle (per tekst) | 10 |
| Engels havo | 16 | 661 | 70 % | 100 % | 100 % | alle (per tekst) | 18 |
| Engels vwo | 16 | 578 | 72 % | 100 % | 100 % | alle (per tekst) | 19 |
| Duits havo | 16 | 665 | 67 % | 100 % | 100 % | alle (per tekst) | 16 |
| Duits vwo | 16 | 657 | 73 % | 94 % | 100 % | alle (per tekst) | 16 |
| Frans havo | 16 | 682 | 69 % | 100 % | 100 % | alle (per tekst) | 18 |
| Frans vwo | 16 | 580 | 70 % | 94 % | 100 % | alle (per tekst) | 18 |
| Spaans havo | 15 | 485 | 71 % | 92 % | 100 % | alle (per tekst) | 16 |
| Spaans vwo | 16 | 572 | 68 % | 94 % | 100 % | alle (per tekst) | 16 |
| Latijn vwo | 16 | 427 | 4 % | 100 % | 100 % | alle (per tekst) | 8 |
| Grieks vwo | 16 | 421 | 2 % | 100 % | 100 % | alle (per tekst) | 9 |
| Kunst algemeen havo/vwo | 10 + 10 | – | – | – | 0 % | – | – |
| Muziek havo/vwo | 8 + 8 | – | – | – | 0 % | – | – |

- *Gekoppeld*: vraagnummers in de opgaven die ook in het correctievoorschrift staan. Waar het onder de 100 % zit
  (talen, Nederlands), mist de tekstherkenning een paar vragen. De herkenning in de pdf ("In pdf") vindt ze wel allemaal,
  dus dit is op te lossen.
- *Verwijst*: de vraag of de inleiding ervoor noemt een bron, tekst, kaart of bijlage met een nummer.
- Ook opgehaald maar klein: de bezemexamens geschiedenis en de pilotexamens maatschappijwetenschappen.
- Zonder centraal examen (bewust niet meegenomen): informatica, NLT, ANW, wiskunde D, O&O, maatschappijleer,
  CKV, LO en BSM. De kleine talen (Arabisch, Turks, Russisch, Italiaans, Fries, Chinees) en de "elementair"-examens
  zijn niet opgehaald. Er staan alleen syllabi van in `bronnen/syllabus/`.

## Per groep vakken

### Economie en bedrijfseconomie: klaar voor dezelfde aanpak

Deze vakken zijn opgebouwd als de bètavakken: een opgave met een context, tabellen en figuren, en daarna vragen. De
vragen staan in het opgavenboekje. Bij economie havo en bedrijfseconomie staat soms een bijlage met extra informatie.

- **Site:** kan meteen met de huidige pijplijn. Indeling per concept (economie: schaarste, ruil, markt, ruilen over de
  tijd, samenwerken en onderhandelen, risico en informatie, welvaart en groei, goede tijden en slechte tijden) of per
  domein (bedrijfseconomie: rechtsvormen, organisatie en personeel, investeren en financieren, marketing, financieel
  beleid, verslaggeving).
- **Indeling:** met de hand, zoals bij de bètavakken (ca. 930 + 710 vragen). `indeling.py` geeft per economievraag al
  een voorstel op trefwoorden, maar dat is te grof om zonder nakijken te gebruiken.
- **Bundel:** kan meteen, met het bijlageboekje achter elk examen in deel 2.
- Bedrijfseconomie bestaat als CE-vak pas sinds 2021 (daarvoor heette het M&O), dus er zijn 12 examens.

### Aardrijkskunde en geschiedenis: indeling gaat bijna vanzelf, bronnen moeten erbij

- Het **domein** (aardrijkskunde: Wereld, Aarde, Ontwikkelingsland, Leefomgeving) en het **tijdvak** (geschiedenis:
  Prehistorie en oudheid, Middeleeuwen, Vroegmoderne tijd, Moderne tijd) staan als kopje in het examen. `indeling.py`
  deelt daarmee 96 % van de vragen automatisch in. Een fijnere indeling (kenmerkende aspecten, historische contexten,
  subdomeinen) moet met de hand.
- Ruim de helft (geschiedenis) tot driekwart (aardrijkskunde) van de vragen gebruikt een bron uit het
  **bronnenboekje** (10 blz. per examen). Voor de site moet de snijcode die bronnen ook kunnen uitsnijden en bij de vraag
  tonen. Dat is nieuw werk, maar het patroon "Gebruik bron 3" is regelmatig.
- **Bundel:** goed te doen. Deel 2 krijgt het bronnenboekje achter elk examen. Bij deel 1 per onderwerp kost het
  meer pagina's, omdat bronnen soms bij meerdere vragen horen.

### Maatschappijwetenschappen en filosofie

- Maatschappijwetenschappen: driekwart van de vragen gebruikt een bron uit het bronnenboekje. Indeling per kernconcept
  (vorming, verhouding, binding, verandering) moet met de hand.
- Filosofie: teksten staan in het opgavenboekje zelf, dus de vragen zijn wel los te tonen. Indeling per domein
  (wijsgerige antropologie, ethiek, sociale filosofie) met de hand, en een kwart van de vragen gaat over een tekst.
- De syllabus van filosofie wisselt elke paar jaar van thema. Oudere examens passen dan minder goed bij de stof van
  nu. Dat maakt een indeling per onderwerp minder waardevol.

### Nederlands en de moderne vreemde talen

- Het centraal examen toetst alleen **leesvaardigheid**. Elke vraag hoort bij een tekst uit het tekstboekje (10–19 blz.,
  ca. 11 teksten per examen bij de vreemde talen, 3–4 bij Nederlands).
- "Per onderwerp" bestaat hier niet. Logische eenheden zijn **per tekst** (een tekst met al zijn vragen) en
  **per vraagtype**: `indeling.py` herkent al open plek, juist/onjuist, citeren, functie of verband, hoofdgedachte,
  samenvatten, argumentatie, betekenis en toon. Bij de vreemde talen is 70 % meerkeuze met een korte vraag. Die
  herkent het script nog niet goed (ze staan als "detailvraag").
- **Site:** dit vraagt een andere weergave: tekst links, vragen rechts, met het antwoordblad.
- **Auteursrecht:** zie hierboven. Dit is het grootste punt bij deze vakken.
- **Bundel:** technisch eenvoudig (tekstboekje plus opgaven per examen), maar per examen ongeveer 40 pagina's. Een
  bundel van 280 pagina's past dan zo'n 5–6 complete examens. Een indeling per onderwerp voegt niets toe.

### Latijn en Grieks

Vertaal- en interpretatievragen bij een vaste auteur die elk jaar wisselt. Oudere examens gaan over een andere auteur
en andere teksten. Per onderwerp oefenen werkt niet goed. Complete examens oefenen wel. Lage prioriteit.

### Kunst algemeen en muziek: valt af

De opgaven zijn plaatjes zonder tekstlaag. Het examen werkt met beeld- en geluidsfragmenten op de computer, die niet
op examenblad.nl staan. De methode werkt hier niet.

## Wat er klaarstaat

| Bestand | Wat |
|---|---|
| `bronnen/` | Alle opgaven, correctievoorschriften, bijlagen, antwoordbladen en aanvullingen 2018–2026, havo en vwo (4,1 GB, lokaal; de pdf's, tekstversies en syllabi staan niet in git en zijn opnieuw op te halen met `haal_op.py`). Ook de syllabi 2026. |
| `bronnen/documenten*.json` | Lijst van alle documenten (per jaar, van `haal_op.py --jaar`). |
| `data/vakken.json`, `data/examens.json` | De metingen hierboven, per vak en per examen. |
| `data/verwijzingen.json` | Aandeel vragen dat een bron of tekst nodig heeft. |
| `data/indeling/<vak>.json` | Elke vraag met examen, nummer, punten, meerkeuze, opgave, en waar mogelijk sectie (domein of tijdvak), tekst en vraagtype, of een voorstel (economie). |
| `analyse.py`, `indeling.py` | Opnieuw draaien na nieuwe examens. |

Opnieuw ophalen of bijwerken (vanuit `eindexamen-oefenen`):

```
python3 tools/haal_op.py economie geschiedenis ... --doel onderzoek/andere-vakken/bronnen --jaar 2027 --niveau havo vwo
~/env/bin/python onderzoek/andere-vakken/analyse.py
~/env/bin/python onderzoek/andere-vakken/indeling.py
```

## Als je een vak wilt toevoegen

1. Kies het vak en leg de juridische vraag (bronnen en teksten van derden) voor bij het CvTE, of houd het bij vakken
   zonder.
2. Zet het vak met zijn domeinen in `VAKKEN` (`tools/bouw_site.py`) en verplaats de documenten naar `bronnen/` (of laat
   de site-scripts `onderzoek/andere-vakken/bronnen` lezen).
3. Deel de vragen in. Gebruik `data/indeling/<vak>.json` als begin: sectie en voorstel overnemen en per vraag nakijken.
4. Voor vakken met een bronnenboekje: snijcode uitbreiden zodat "Gebruik bron N" de bron uit de bijlage meeneemt.
5. Daarna werkt alles zoals bij de bètavakken (snijden, site, bundel).
