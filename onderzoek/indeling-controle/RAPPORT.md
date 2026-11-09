# Controle van de indeling per onderwerp tegen de examenstof (november 2026)

Vraag: klopt de indeling van de examenvragen op de site met wat het College voor Toetsen en Examens als examenstof
voorschrijft, en hoe verhoudt die zich tot bestaande examenbundels?

Bronnen: de syllabi centraal examen 2025/2026 van examenblad.nl (`bronnen/syllabus/`), met per vak de tabel
*Domeinindeling en CE-toekenning* en de zin "Het centraal examen heeft betrekking op ..." uit het examenprogramma;
de inhoudsopgave van de Examenbundel havo biologie (ThiemeMeulenhoff, 2022/2023) en van Samengevat scheikunde
(ThiemeMeulenhoff). Script: `ce_toekenning.py` (uitkomst in `ce_toekenning.json`).

## Kort oordeel

| Vak | Oordeel | Wat er moet gebeuren |
|---|---|---|
| Wiskunde A/B havo, A/B/C vwo | **Klopt** | Niets. De onderwerpen volgen de CE-subdomeinen één op één; wat alleen schoolexamen is (statistiek bij A en C vwo, telproblemen bij A havo, D Verandering bij A havo), staat terecht niet op de site. |
| Natuurkunde havo en vwo | **Klopt** | Niets. Alle onderwerpen vallen onder CE-subdomeinen (havo: B1, B2, C1, C2, D1, E1, G1; vwo: B1, B2, C1–C3, D1, D2, E2, F1); de keuzedomeinen (bk) en I (onderzoek en ontwerp) zijn terecht weggelaten. |
| Scheikunde havo en vwo | **Inhoud klopt, codes niet** | Een paar onderwerpen dragen de code van een subdomein dat alleen schoolexamen is. De syllabus ordent de examenstof sinds kort in *sferen* (M, R, R&A, T, L); die codes horen op de site. |
| Biologie havo | **Structuur deels onjuist** | Twee onderwerpen hangen aan stof die bij havo alleen schoolexamen is (voortplanting, en de codes B6–B7 bij zenuwstelsel). De 14 "voortplanting"-vragen gaan in werkelijkheid over andere CE-stof. |
| Biologie vwo | **Codes onjuist** | De site gebruikt de havo-nummering, maar vwo heeft een andere nummering én een andere CE-stof (bij vwo zitten eiwitsynthese en voortplanting wél in het CE). |

Steekproef per vraag: 49 willekeurige vragen uit 7 vakken nagelopen; 48 staan bij een passend onderwerp, 1 is een
twijfelgeval (natuurkunde vwo, *Beker van Lycurgus*: absorptiepiek, nu bij golven, kan ook bij E2). De indeling
per vraag is dus betrouwbaar; de verbeteringen zitten in structuur en codes.

## Per vak

### Wiskunde

CE volgens de syllabi: A havo C + B1, B2, E1–E4 · B havo B, C, D · A vwo B, C, D · B vwo B, C, D, E · C vwo B, C, D,
F, G. De site heeft precies deze subdomeinen als onderwerpen. Kleine onderwerpen (tabellen 4 vragen, inverse functies 4,
helling 4, technieken voor differentiëren 5, periodiek bij C 3) zijn klein omdat het examen er weinig over vraagt, niet
door een verkeerde indeling. Overweging voor later: heel kleine onderwerpen samenvoegen voor de leerling (bijv.
*afgeleide functies* en *technieken voor differentiëren* bij B vwo), met behoud van beide syllabuscodes.

### Natuurkunde

Klopt. Opmerking: domein H (natuurkunde en technologie) en de vaardigheden (A) worden in het CE getoetst *in combinatie
met* de andere domeinen; een apart onderwerp "Onderzoek, eenheden en modellen" (A) is daarom verdedigbaar.

### Scheikunde

CE havo: B1–B5, C1–C3, C6–C8, D1, D3, E1, F1, F3, G1, G2. **Alleen SE: C4 Chemisch evenwicht, C5 Technologische aspecten.**
CE vwo: B1–B4, C1–C6, D1, D3, E1, E2, F1–F3, G1–G3. **Alleen SE: C7 Classificatie van reacties, C8 Technologische aspecten.**

| Onderwerp op de site | Code nu | Probleem | Voorstel (sfeer uit de syllabus) |
|---|---|---|---|
| Industriële processen (havo) | C5 | C5 is alleen SE | T1 Industriële processen en groene chemie; R4 Chemische procesontwerpen |
| Industriële processen (vwo) | C8 | C8 is alleen SE | T1 Industriële processen |
| Zuren en basen (vwo) | C7 | C7 is alleen SE | R1 Chemische processen |
| Redox (vwo) | C7 | C7 is alleen SE | R1 Chemische processen |
| Koolstofverbindingen (vwo) | B/C7 | C7 is alleen SE | M3–M4 Bindingen, structuren en eigenschappen |
| Overige onderwerpen | B…, C… | kloppen, maar de syllabus spreekt in sferen | M1–M7, R1–R5, R&A1–3, T1–T6, L1–L2 |

Evenwicht staat bij havo terecht niet als onderwerp (bij vwo wel: R4 Chemisch evenwicht).
Vergelijking: Samengevat scheikunde gebruikt vijf grote hoofdstukken (atomen en stoffen, reacties, koolstofchemie en
biochemie, energie, industrie en milieu); de site is fijner verdeeld (12–13 onderwerpen). Dat is voor oefenen per
onderwerp een voordeel.

### Biologie havo

CE: B2, B3, B4, B5, B8, C1, D4, E4, F1, F2 (in de nieuwe nummering M2, M3, M7, M8, O1, O2, O3, P1, P3, P4).
**Alleen SE: B1 eiwitsynthese, B6 beweging, B7 waarneming, C2, C3, D1, D2 gedrag, D3 seksualiteit, E1 DNA-replicatie,
E2 levenscyclus, E3 voortplanting, F3 biodiversiteit.**

| Onderwerp op de site | Code nu | Vragen | Probleem | Voorstel |
|---|---|---|---|---|
| Voortplanting | E2–E3 | 14 | E2 en E3 zijn alleen SE; de vragen gaan over celdifferentiatie (C1), klonen en variatie bij gewassen (F1), weeën/hormonen (B4) en bestuiving (D4) | onderwerp opheffen bij havo; elke vraag naar het juiste CE-onderwerp |
| DNA en eiwitsynthese | B1, E1 | 48 | B1 en E1 zijn alleen SE; in het CE valt dit onder genexpressie | code C1 (M3 Zelforganisatie van cellen: genexpressie) |
| Zenuwstelsel | B6–B7 | 52 | B6 en B7 zijn alleen SE; de vragen gaan over neurale regulatie | code B4 (O2.3 Neurale regulatie) |
| Cellen | B2, D1 | 18 | D1 is alleen SE | code B2, C1 |
| Ecologie | B8, D2, D4 | 132 | D2 (gedrag) is alleen SE | code B8, D4 |
| Evolutie | F | 66 | F3 is alleen SE | code F1, F2 |

De Examenbundel havo biologie heeft een vergelijkbare indeling (cellen, voortplanting, erfelijkheid, DNA,
genexpressie, evolutie, fotosynthese en dissimilatie, ecosystemen, vertering, bloedsomloop, gaswisseling,
uitscheiding, gedrag, zintuigen, zenuwstelsel, afweer) en markeert *voortplanting en ontwikkeling*, *gedrag en
seksualiteit*, *celcyclus* en *eiwitsynthese* met een sterretje: "alleen bestemd voor het schoolexamen". Dat
bevestigt dit oordeel.

### Biologie vwo

CE: B1, B2, B3, B4, B5, B8, C1, C3, D1, D2, D5, E3, F1, F2. **Alleen SE: B6, B7, C2, D3 gedrag, D4 seksualiteit,
E1 DNA-replicatie, E2 levenscyclus, F3, F4.** De vwo-nummering wijkt af van havo (bij vwo is D4 seksualiteit en
D5 interactie in ecosystemen; erfelijkheid valt onder E3).

| Onderwerp | Code nu (havo-nummering) | Voorstel vwo |
|---|---|---|
| Cellen | B2, D1 | B2, C1, D1, D2 |
| DNA en eiwitsynthese | B1, E1 | B1, C1 (E1 is SE) |
| Voortplanting | E2–E3 | E3 (CE bij vwo) |
| Erfelijkheid | E4 | E3 (E4 bestaat niet bij vwo) |
| Zenuwstelsel | B6–B7 | B4 (B6, B7 zijn SE) |
| Ecologie | B8, D2, D4 | B8, C3, D5 |
| Evolutie | F | F1, F2 |

## Voorstel

1. **Biologie havo:** onderwerp *voortplanting* opheffen en de 14 vragen per vraag herindelen; codes aanpassen zoals hierboven.
2. **Biologie vwo:** eigen onderwerpenlijst met vwo-codes (nu delen havo en vwo dezelfde functie in `bouw_site.py`).
3. **Scheikunde:** codes vervangen door de sfeercodes uit de syllabus; namen blijven grotendeels gelijk.
4. **Wiskunde en natuurkunde:** niets veranderen; eventueel het twijfelgeval *Beker van Lycurgus* nalopen.
5. Daarna: site-gegevens en vaste pagina's opnieuw maken en de bundels van biologie en scheikunde opnieuw bouwen
   (de indeling van deel 1 verandert).

Kanttekening: de vragen beslaan 2018–2026, en in die periode zijn syllabi bijgesteld (bij natuurkunde en scheikunde
geldt voor 2026 een "nadere vaststelling"). Ik heb alleen de syllabi 2025/2026 vergeleken, niet die van elk
eerder jaar. Het voorstel gebruikt de codes van de syllabus 2026, omdat leerlingen die nu gebruiken; een vraag uit
bijvoorbeeld 2019 kan onder een oudere syllabus net anders zijn bedoeld. Als controle kan per vak de oudste en de
nieuwste syllabus worden vergeleken voordat de wijzigingen worden doorgevoerd.
