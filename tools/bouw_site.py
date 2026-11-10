"""
Zet de gegevens voor de site klaar in docs/data/.

Leest bronnen/databank.json (vragen), indeling/<vak>.json (onderwerp per vraag, met de hand
ingedeeld volgens de syllabus), bronnen/snij.json (beelden per vraag) en bronnen/documenten.json
(links naar de originele pdf's op examenblad.nl).

Draaien (vanuit de map eindexamen-oefenen, na snij.py):
    python3 tools/bouw_site.py
"""
import json
from datetime import date
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
BRON = ROOT / 'bronnen'
UIT = ROOT / 'docs' / 'data'

# ---------- onderwerpen per vak, gegroepeerd per domein uit de syllabus ----------
# (sleutel, naam, syllabuscode, korte omschrijving)
VAKKEN = {
    'wiskunde-a-havo': {
        'niveau': 'havo', 'naam': 'Wiskunde A', 'domeinen': [
            ('Algebra en rekenen', [
                ('rekenen', 'Rekenen: procenten, verhoudingen en eenheden', 'B1', 'Procentuele verandering, indexcijfers, omrekenen en afronden.'),
                ('algebra', 'Formules herleiden', 'B2', 'Een formule omwerken tot een gevraagde vorm.'),
            ]),
            ('Verbanden', [
                ('tabellen', 'Tabellen', 'C1', 'Gegevens uit een tabel halen, aanvullen en interpoleren.'),
                ('grafieken', 'Grafieken, vergelijkingen en ongelijkheden', 'C2', 'Grafieken aflezen en tekenen, vergelijkingen en ongelijkheden oplossen.'),
                ('formules', 'Formules met meer variabelen', 'C3', 'Formules gebruiken, opstellen en beredeneren zonder getallenvoorbeelden.'),
                ('lineair', 'Lineaire verbanden', 'C4', 'Rechte lijnen: richtingscoëfficiënt, formule opstellen, extrapoleren.'),
                ('exponentieel', 'Exponentiële verbanden', 'C5', 'Groeifactor, groeipercentage, verdubbelings- en halveringstijd.'),
            ]),
            ('Statistiek', [
                ('data-presentatie', 'Data presenteren en beoordelen', 'E1', 'Diagrammen lezen, kiezen en beoordelen.'),
                ('data-verwerken', 'Data verwerken', 'E2', 'Soorten variabelen, centrum- en spreidingsmaten, frequenties en kwartielen.'),
                ('verdelingen', 'Verdelingen en de normale verdeling', 'E3', 'Vorm van een verdeling, vuistregels van de normale verdeling.'),
                ('verschil', 'Verschil tussen twee groepen', 'E4', 'Effectgrootte, phi, max Vcp en boxplots met het formuleblad.'),
                ('steekproef', 'Steekproeven en betrouwbaarheidsintervallen', 'E4', 'Onderzoeksopzet, representativiteit en 95%-betrouwbaarheidsintervallen.'),
            ]),
        ]},
    'wiskunde-b-havo': {
        'niveau': 'havo', 'naam': 'Wiskunde B', 'domeinen': [
            ('Functies, grafieken en vergelijkingen', [
                ('standaardfuncties', 'Standaardfuncties en transformaties', 'B1', 'Machts-, wortel- en gebroken functies, translaties en vermenigvuldigingen.'),
                ('exp-log', 'Exponentiële en logaritmische functies', 'B1', 'Exacte vergelijkingen met machten en logaritmen, rekenregels.'),
                ('vergelijkingen', 'Vergelijkingen en ongelijkheden', 'B2', 'Exact en met de GR oplossen, snijpunten berekenen.'),
                ('evenredigheid', 'Evenredigheidsverbanden', 'B3', 'Recht en omgekeerd evenredig, machtsverbanden in een context.'),
                ('periodiek', 'Periodieke functies', 'B4', 'Sinusoïden: evenwichtsstand, amplitude, periode en exacte oplossingen.'),
            ]),
            ('Meetkundige berekeningen', [
                ('afstanden-hoeken', 'Afstanden en hoeken', 'C1', 'Sinus- en cosinusregel, goniometrie in driehoeken.'),
                ('coordinaten', 'Meetkunde met coördinaten', 'C2', 'Lijnen, cirkels, loodrecht staan, afstanden en raken.'),
            ]),
            ('Toegepaste analyse', [
                ('veranderingen', 'Veranderingen', 'D1', 'Differentiequotiënt en helling uit een grafiek.'),
                ('afgeleide', 'Afgeleide functies', 'D2/D3', 'Differentiëren met de regels, helling in een punt.'),
                ('toepassing', 'Toepassingen van de afgeleide', 'D4', 'Raaklijnen, extreme waarden en optimaliseren.'),
            ]),
        ]},
    'wiskunde-a-vwo': {
        'niveau': 'vwo', 'naam': 'Wiskunde A', 'domeinen': [
            ('Algebra en tellen', [
                ('algebra', 'Algebra: herleiden en rekenregels', 'B1', 'Formules omwerken, rekenregels voor machten en logaritmen.'),
                ('tellen', 'Telproblemen', 'B2', 'Combinaties, permutaties, rooster- en boomdiagrammen.'),
            ]),
            ('Verbanden', [
                ('lin-kwadr', 'Lineaire en kwadratische functies', 'C1', 'Rechte lijnen en parabolen in een context.'),
                ('machts', 'Machtsfuncties en evenredigheid', 'C1', 'Machtsverbanden, gebroken formules, recht en omgekeerd evenredig.'),
                ('exp-log', 'Exponentiële en logaritmische functies', 'C1', 'Groeimodellen, e-machten, ln en log, logaritmische schaal.'),
                ('periodiek', 'Periodieke functies', 'C1', 'Sinusoïden opstellen en gebruiken.'),
                ('vergelijkingen', 'Formules, vergelijkingen en ongelijkheden', 'C2', 'Formules opstellen en gebruiken, oplossen met of zonder GR.'),
            ]),
            ('Verandering', [
                ('rijen', 'Rijen', 'D1', 'Rekenkundige en meetkundige rijen, recursieve en directe formules.'),
                ('helling', 'Helling en veranderingssnelheid', 'D2', 'Helling uit een grafiek, toename- en afnamediagrammen.'),
                ('afgeleide', 'Afgeleide en extreme waarden', 'D3', 'Differentiëren, toenemend/afnemend stijgend, maximum en minimum.'),
            ]),
        ]},
    'wiskunde-b-vwo': {
        'niveau': 'vwo', 'naam': 'Wiskunde B', 'domeinen': [
            ('Functies, grafieken en vergelijkingen', [
                ('formules', 'Formules en functies', 'B1', 'Formules uit een context gebruiken en herleiden.'),
                ('standaardfuncties', 'Standaardfuncties en transformaties', 'B2/B3', 'Grafieken van standaardfuncties en transformaties.'),
                ('exp-log', 'Exponentiële en logaritmische functies', 'B2', 'e-machten, ln en logaritmen exact.'),
                ('inverse', 'Inverse functies', 'B4', 'Inverse opstellen en gebruiken.'),
                ('vergelijkingen', 'Vergelijkingen en ongelijkheden', 'B5', 'Exact oplossen, ook met absolute waarde en parameters.'),
                ('asymptoten', 'Asymptoten, limieten en perforaties', 'B6', 'Horizontale, verticale en scheve asymptoten, limietgedrag.'),
            ]),
            ('Differentiaal- en integraalrekening', [
                ('afgeleide', 'Afgeleide: raaklijnen en extremen', 'C1', 'Raaklijnen, raken, extreme waarden en buigpunten.'),
                ('differentieren', 'Technieken voor differentiëren', 'C2', 'Product-, quotiënt- en kettingregel, een afgeleide bewijzen.'),
                ('integraal', 'Integraalrekening', 'C3', 'Primitiveren, oppervlakte en inhoud van omwentelingslichamen.'),
            ]),
            ('Goniometrische functies', [
                ('goniometrie', 'Goniometrische functies', 'D', 'Sinus en cosinus, exacte vergelijkingen, formules met periode.'),
            ]),
            ('Meetkunde met coördinaten', [
                ('meetkunde', 'Meetkunde: lijnen, cirkels en hoeken', 'E1/E2', 'Cirkelvergelijkingen, afstanden, hoeken, bewijzen met coördinaten.'),
                ('vectoren', 'Vectoren en inproduct', 'E3', 'Vectorvoorstellingen, inproduct, hoeken tussen vectoren, zwaartepunt.'),
                ('beweging', 'Bewegingsvergelijkingen', 'E4', 'Banen, snelheid en snelheidsvectoren bij een bewegend punt.'),
            ]),
        ]},
    'wiskunde-c-vwo': {
        'niveau': 'vwo', 'naam': 'Wiskunde C', 'domeinen': [
            ('Algebra en tellen', [
                ('rekenen-algebra', 'Rekenen en algebra', 'B1', 'Procenten, verhoudingen, eenheden en formules herleiden.'),
                ('tellen', 'Telproblemen', 'B2', 'Combinaties, permutaties en systematisch tellen.'),
            ]),
            ('Verbanden', [
                ('lin-kwadr', 'Lineaire en kwadratische verbanden', 'C', 'Rechte lijnen, parabolen en lineair extrapoleren.'),
                ('machts', 'Machtsverbanden', 'C', 'Machtsformules en evenredigheid in een context.'),
                ('exp-log', 'Exponentiële en logaritmische verbanden', 'C', 'Groeifactoren, logaritmische schaal, log-formules.'),
                ('periodiek', 'Periodieke verschijnselen', 'C', 'Periode, frequentie en sinusvormige verbanden.'),
                ('vergelijkingen', 'Formules en vergelijkingen', 'C', 'Formules gebruiken en vergelijkingen oplossen in een context.'),
            ]),
            ('Veranderingen', [
                ('rijen', 'Rijen', 'D', 'Recursieve en directe formules, somrijen.'),
                ('veranderingen', 'Veranderingen', 'D', 'Toenemend en afnemend stijgen, helling uit een grafiek.'),
            ]),
            ('Logisch redeneren', [
                ('logica', 'Logisch redeneren', 'F', 'Logische symbolen, Venn-diagrammen en sluitende redeneringen.'),
            ]),
            ('Vorm en ruimte', [
                ('ruimte', 'Vorm en ruimte', 'G', 'Aanzichten, perspectief, verdwijnpunten en ruimtelijke berekeningen.'),
            ]),
        ]},
}
# bètavakken: onderwerpen volgens de CE-subdomeinen van de syllabus 2026
BINAS = 'Bij dit examen gebruik je Binas of ScienceData. Die staan niet bij de originele stukken.'
VAKKEN['natuurkunde-havo'] = {
    'niveau': 'havo', 'naam': 'Natuurkunde', 'opmerking': BINAS, 'domeinen': [
        ('Vaardigheden', [
            ('onderzoek', 'Onderzoek, eenheden en modellen', 'A', 'Eenheden afleiden, verbanden en grafieken, meten en schatten.'),
        ]),
        ('Beeld- en geluidstechniek', [
            ('trillingen', 'Trillingen', 'B1', 'Periode, frequentie, oscillogrammen, massa-veersysteem en resonantie.'),
            ('golven', 'Golven en geluid', 'B1', 'Lopende en staande golven, knopen en buiken, muziekinstrumenten.'),
            ('straling', 'Ioniserende straling', 'B2', 'Vervalreacties, activiteit, dosis, halveringstijd en halveringsdikte.'),
            ('beeldvorming', 'Elektromagnetische straling en fotonen', 'B2', 'Spectrum, fotonenergie, röntgen, CT en echografie.'),
        ]),
        ('Beweging en energie', [
            ('beweging', 'Bewegingen en diagrammen', 'C1', '(x,t)- en (v,t)-diagrammen, raaklijnen en oppervlakte onder de grafiek.'),
            ('krachten', 'Krachten en de wetten van Newton', 'C1', 'Krachten construeren en ontbinden, Fres = m·a, wrijving.'),
            ('moment', 'Momenten en hefbomen', 'C1', 'Arm, draaipunt en de momentenwet.'),
            ('energie', 'Arbeid, energie en vermogen', 'C2', 'Arbeid, kinetische en zwaarte-energie, rendement en vermogen.'),
        ]),
        ('Materialen', [
            ('stoffen', 'Stoffen, warmte en materialen', 'D1', 'Faseovergangen, soortelijke warmte, warmtetransport, dichtheid, debiet en rek.'),
        ]),
        ('Aarde en heelal', [
            ('heelal', 'Cirkelbewegingen, gravitatie en heelal', 'E1', 'Baansnelheid, middelpuntzoekende kracht, satellieten, sterren en de wet van Wien.'),
        ]),
        ('Meten en regelen', [
            ('elektriciteit', 'Elektrische schakelingen', 'G1', 'Spanning, stroom, weerstand, serie en parallel, vermogen en energie.'),
        ]),
    ]}

VAKKEN['natuurkunde-vwo'] = {
    'niveau': 'vwo', 'naam': 'Natuurkunde', 'opmerking': BINAS, 'domeinen': [
        ('Vaardigheden', [
            ('onderzoek', 'Onderzoek, eenheden en modellen', 'A', 'Eenheden afleiden, meetonzekerheid, grafieken en computermodellen.'),
        ]),
        ('Golven', [
            ('trillingen', 'Trillingen', 'B1', 'Periode, frequentie, massa-veersysteem en resonantie.'),
            ('golven', 'Golven, geluid en interferentie', 'B1', 'Staande golven, golfsnelheid, interferentie en tralies.'),
        ]),
        ('Straling en beeldvorming', [
            ('straling', 'Ioniserende straling', 'B2', 'Vervalreacties, activiteit, dosis, halveringstijd en halveringsdikte.'),
            ('beeldvorming', 'Fotonen en medische beeldvorming', 'B2', 'Fotonenergie, röntgen, CT, MRI, PET en echografie.'),
        ]),
        ('Beweging en wisselwerking', [
            ('beweging', 'Bewegingen en diagrammen', 'C1', '(x,t)- en (v,t)-diagrammen, raaklijnen en oppervlakte onder de grafiek.'),
            ('krachten', 'Krachten en de wetten van Newton', 'C1', 'Krachten construeren en ontbinden, Fres = m·a, luchtweerstand.'),
            ('energie', 'Arbeid, energie en vermogen', 'C2', 'Arbeid, energiebehoud, rendement en vermogen.'),
            ('gravitatie', 'Cirkelbewegingen en gravitatie', 'C3', 'Middelpuntzoekende kracht, gravitatie-energie, satellieten en ontsnappingssnelheid.'),
        ]),
        ('Elektriciteit en magnetisme', [
            ('elektriciteit', 'Elektrische schakelingen', 'D1', 'Spanning, stroom, weerstand, Kirchhoff, vermogen en energie.'),
            ('velden', 'Elektrische en magnetische velden', 'D2', 'Elektrisch veld, lorentzkracht, geladen deeltjes in velden en inductie.'),
        ]),
        ('Sterren en quantumwereld', [
            ('sterren', 'Straling van sterren en spectra', 'E2', 'Wien, Stefan-Boltzmann, energieniveaus, spectraallijnen en dopplereffect.'),
            ('quantum', 'Quantumwereld', 'F1', 'Debroglie-golflengte, energieput, tunneling en fotonen als deeltjes.'),
        ]),
    ]}


def scheikunde(niveau, c):
    """Onderwerpen scheikunde. De codes zijn de (sub)sferen uit de syllabus 2026 (M Materie, R Reacties, R&A Rekenen
    en analyse, T Technologie en duurzaamheid, L Chemie van het leven); ze verschillen per niveau. Zie
    onderzoek/indeling-controle/RAPPORT.md: de oude subdomeincodes C5, C7 en C8 zijn deels alleen schoolexamen."""
    return {'niveau': niveau, 'naam': 'Scheikunde', 'opmerking': BINAS, 'domeinen': [
        ('Stoffen en deeltjes', [
            ('bouw', 'Atoombouw, bindingen en structuren', c['bouw'], 'Ionen, roosters, polariteit, waterstofbruggen, oplosbaarheid en faseovergangen.'),
            ('organisch', 'Koolstofverbindingen en polymeren', c['organisch'], 'Naamgeving, structuurformules, esters, additie, condensatie en kunststoffen.'),
        ]),
        ('Chemische processen', [
            ('reacties', 'Reactievergelijkingen', c['reacties'], 'Reacties opstellen en kloppend maken, verbranding en neerslagreacties.'),
            ('rekenen', 'Chemisch rekenen', c['rekenen'], 'Mol, massa, concentratie, massapercentage, ppm en rendement.'),
            ('energie', 'Energie en reactiewarmte', c['energie'], 'Vormingswarmte, exotherm en endotherm, energiediagrammen.'),
            ('snelheid', 'Reactiesnelheid en katalyse', c['snelheid'], 'Botsende-deeltjesmodel, verdelingsgraad, temperatuur en katalysatoren.'),
            ('evenwicht', 'Chemisch evenwicht', c.get('evenwicht', ''), 'Evenwichtsvoorwaarde, evenwichtsconstante en verschuiving.'),
            ('zuurbase', 'Zuren en basen', c['zuurbase'], 'pH, [H⁺] en [OH⁻], zuur-basereacties, buffers en titraties.'),
            ('redox', 'Redoxreacties en elektrochemie', c['redox'], 'Oxidator en reductor, halfreacties, batterijen, brandstofcellen en elektrolyse.'),
        ]),
        ('Chemie in de praktijk', [
            ('analyse', 'Scheiden, analyseren en veiligheid', c['analyse'], 'Scheidingsmethoden, chromatografie, ijklijnen en H- en P-zinnen.'),
            ('proces', 'Industriële processen en blokschema\'s', c['proces'], 'Blokschema\'s, stofstromen, recirculatie en procesvoering.'),
            ('duurzaam', 'Groene chemie en duurzaamheid', c['duurzaam'], 'Atoomeconomie, uitgangspunten van de groene chemie, broeikaseffect en kringlopen.'),
            ('leven', 'Chemie van het leven', c['leven'], 'Eiwitten, aminozuren, koolhydraten, vetten en enzymen.'),
        ]),
    ]}


# evenwicht is bij havo alleen schoolexamen (C4): geen onderwerp
VAKKEN['scheikunde-havo'] = scheikunde('havo', {'bouw': 'M1–M5', 'organisch': 'M1, R1–R2', 'reacties': 'R1', 'rekenen': 'R&A1',
                                               'energie': 'R5', 'snelheid': 'R3', 'zuurbase': 'R1, R&A1', 'redox': 'R1',
                                               'analyse': 'R&A2', 'proces': 'T1, R4', 'duurzaam': 'T1–T4', 'leven': 'L1'})
VAKKEN['scheikunde-havo']['domeinen'][1][1][:] = [o for o in VAKKEN['scheikunde-havo']['domeinen'][1][1] if o[0] != 'evenwicht']
VAKKEN['scheikunde-vwo'] = scheikunde('vwo', {'bouw': 'M1–M5', 'organisch': 'M1, R1–R2', 'reacties': 'R1', 'rekenen': 'R&A1',
                                             'energie': 'R5', 'snelheid': 'R2–R3', 'evenwicht': 'R4', 'zuurbase': 'R1, R&A1', 'redox': 'R1',
                                             'analyse': 'R&A2', 'proces': 'T1', 'duurzaam': 'T2–T6', 'leven': 'L1–L2'})


def biologie(niveau):
    """Onderwerpen biologie, met de codes van de subdomeinen van het centraal examen. Havo en vwo verschillen: bij
    havo zijn eiwitsynthese (B1), DNA-replicatie (E1) en voortplanting (E2, E3) alleen schoolexamen, bij vwo zitten
    B1 en E3 wel in het CE; vwo nummert D en E anders. Zie onderzoek/indeling-controle/RAPPORT.md."""
    havo = niveau == 'havo'
    cel_en_erf = [
        ('cel', 'Cellen, organellen en transport', 'B2, C1' if havo else 'B2, C1, D1–D2', 'Organellen, celmembraan, osmose, diffusie, organisatieniveaus en celdifferentiatie.'),
        ('stofwisseling', 'Stofwisseling en enzymen', 'B2', 'Enzymen, dissimilatie, gisting, assimilatie en energie.'),
        ('dna', 'DNA en genexpressie' if havo else 'DNA, eiwitsynthese en genexpressie', 'C1' if havo else 'B1, C1',
         'Genen, genexpressie, mutaties en biotechnologie.' if havo else 'Transcriptie, translatie, codons, mutaties, genexpressie en biotechnologie.'),
    ]
    if not havo:
        cel_en_erf.append(('voortplanting', 'Celdeling en voortplanting', 'E3', 'Meiose, bevruchting, geslachtelijke en ongeslachtelijke voortplanting.'))
    cel_en_erf += [
        ('erfelijkheid', 'Erfelijkheid en stambomen', 'E4' if havo else 'E3', 'Kruisingsschema\'s, dominant en recessief, X-chromosomaal en kansen.'),
        ('evolutie', 'Evolutie, variatie en selectie', 'F1, F2', 'Natuurlijke en kunstmatige selectie, variatie, klonen, soortvorming en resistentie.'),
    ]
    return {'niveau': niveau, 'naam': 'Biologie', 'opmerking': BINAS.replace('Binas of ScienceData', 'het informatieboek Binas of ScienceData'), 'domeinen': [
        ('Vaardigheden', [
            ('onderzoek', 'Onderzoek en experimenten', 'A5', 'Hypothese, variabelen, controlegroep, werkplan, betrouwbaarheid en conclusies.'),
        ]),
        ('Cel en erfelijkheid', cel_en_erf),
        ('Het menselijk lichaam', [
            ('vertering', 'Voeding en vertering', 'B3', 'Spijsverteringskanaal, enzymen, resorptie, lever en voedingsstoffen.'),
            ('transport', 'Ademhaling, bloedsomloop en uitscheiding', 'B3', 'Longen, hart, bloedvaten, bloed en nieren.'),
            ('regeling', 'Hormonen en homeostase', 'B4', 'Hormoonklieren, terugkoppeling, glucoseregulatie, ADH en de menstruatiecyclus.'),
            ('zenuw', 'Zenuwstelsel en reflexen', 'B4', 'Neurale regulatie: zenuwcellen, synaps, reflexen, hersenen en het autonome zenuwstelsel.'),
            ('afweer', 'Afweer en bloedgroepen', 'B5', 'Aspecifieke en specifieke afweer, vaccinatie, immuniteit en bloedgroepen.'),
        ]),
        ('Planten en ecologie', [
            ('plant', 'Planten', 'B3, B8', 'Fotosynthese, hout- en bastvaten, huidmondjes, wortels en beperkende factoren.'),
            ('ecologie', 'Ecosystemen en kringlopen', 'B8, D4' if havo else 'B8, C3, D5', 'Voedselwebben, energiestroom, relaties tussen soorten, populaties, stikstofkringloop, exoten en duurzaamheid.'),
        ]),
    ]}


VAKKEN['biologie-havo'] = biologie('havo')
VAKKEN['biologie-vwo'] = biologie('vwo')

# ---------- vmbo: een syllabus per vak voor alle leerwegen; per leerweg alleen de exameneenheden van het CE ----------
# (bron: syllabi centraal examen 2026, tabel 'Verdeling examinering CE/SE'; gl en tl hebben hetzelfde examen)
VMBO_NAAM = {'bb': 'vmbo-bb', 'kb': 'vmbo-kb', 'gt': 'vmbo-gt'}


def wiskunde_vmbo(lw):
    gt = lw == 'gt'
    k4 = 'WI/K/4' + (', V/1' if gt else '')
    d = {'niveau': VMBO_NAAM[lw], 'naam': 'Wiskunde', 'domeinen': [
        ('Algebraïsche verbanden', [
            ('grafieken', 'Tabellen en grafieken', k4, 'Aflezen, tekenen, vergelijken en interpreteren; snijpunten, maxima en minima.'),
            ('formules', 'Rekenen met formules', k4, 'Waarden invullen, formules opstellen en gebruiken, woordformules.'),
            ('lineair', 'Lineaire verbanden', k4, 'Formules van de vorm y = ax + b, steilheid en beginwaarde.'),
            ('exponentieel', 'Exponentiële verbanden', k4, 'Groeifactor, procentuele groei, rente op rente, verdubbelings- en halveringstijd.'),
            ('andere-verbanden', 'Kwadratische, wortel-, omgekeerd evenredige en periodieke verbanden', k4, 'Parabolen, machten, y = a/x, periode en amplitude.'),
        ]),
        ('Rekenen, meten en schatten', [
            ('rekenen', 'Procenten, verhoudingen en breuken', 'WI/K/5', 'Handig rekenen in alledaagse situaties, procenten, korting en btw, verhoudingen.'),
            ('meten', 'Eenheden, schaal en schatten', 'WI/K/5', 'Eenheden omrekenen, tijd en snelheid, schaal, afronden en schatten.'),
        ]),
        ('Meetkunde', [
            ('oppervlakte-inhoud', 'Omtrek, oppervlakte en inhoud', 'WI/K/6', 'Oppervlakte van vlakke figuren, inhoud van prisma, cilinder, kegel en bol.'),
            ('pythagoras-gonio', 'Stelling van Pythagoras en goniometrie', 'WI/K/6', 'Zijden berekenen met Pythagoras, hoeken en zijden met sinus, cosinus en tangens.'),
            ('ruimtefiguren', 'Ruimtefiguren, aanzichten en uitslagen', 'WI/K/6', 'Aanzichten, uitslagen, doorsneden, perspectief en kijklijnen.'),
            ('redeneren', 'Hoeken, gelijkvormigheid en meetkundig tekenen', 'WI/K/6', 'Hoeken berekenen, symmetrie, vergroten en verkleinen, constructies.'),
        ]),
    ]}
    if lw == 'bb':  # Pythagoras en goniometrie zitten bij bb niet in het CE
        d['domeinen'] = [(n, [o for o in l if o[0] != 'pythagoras-gonio']) for n, l in d['domeinen']]
    return d


def nask1_vmbo(lw):
    ond = [
        ('onderzoek', 'Onderzoeken en meten', 'NASK1/K/3', 'Meetinstrumenten, grootheden en eenheden, tabellen en grafieken, conclusies uit proeven.'),
        ('stoffen', 'Stoffen en materialen', 'NASK1/K/4', 'Stofeigenschappen, fasen en faseovergangen, dichtheid, mengsels en scheiden.'),
        ('elektriciteit', 'Elektrische energie', 'NASK1/K/5', 'Schakelingen, spanning, stroom, weerstand, vermogen, energie en kosten, veiligheid.'),
    ]
    if lw != 'bb':
        ond.append(('verbranden', 'Verbranden en verwarmen', 'NASK1/K/6', 'Verbranding, brandstoffen, warmte, isoleren en verwarmen.'))
    ond += [
        ('geluid', 'Geluid', 'NASK1/K/8', 'Trillingen, toonhoogte, frequentie, geluidssterkte, decibel en gehoorbescherming.'),
        ('kracht', 'Kracht en veiligheid', 'NASK1/K/9', 'Krachten, hefbomen, druk, beweging en snelheid, veiligheid.'),
    ]
    if lw == 'gt':
        ond += [
            ('verkeer', 'Veiligheid in het verkeer', 'NASK1/V/1', 'Snelheid, reactie- en remweg, stopafstand, bewegingsenergie en veiligheidsvoorzieningen.'),
            ('constructies', 'Constructies', 'NASK1/V/2', 'Krachten in constructies, momenten, stevigheid en materiaalkeuze.'),
        ]
    return {'niveau': VMBO_NAAM[lw], 'naam': 'Nask1', 'domeinen': [('Natuurkunde', ond)]}


def nask2_vmbo():
    return {'niveau': 'vmbo-gt', 'naam': 'Nask2', 'domeinen': [('Scheikunde', [
        ('onderzoek', 'Onderzoeken en practicum', 'NASK2/K/3', 'Proeven opzetten, meten, waarnemen en conclusies trekken.'),
        ('materie', 'Bouw van de materie', 'NASK2/K/11', 'Atomen, moleculen, ionen, het periodiek systeem en formules.'),
        ('reacties', 'Reacties en reactievergelijkingen', 'NASK2/K/10', 'Kenmerken van reacties, reactievergelijkingen kloppend maken, rekenen aan reacties.'),
        ('verbranding', 'Verbranding', 'NASK2/K/5', 'Verbrandingsvoorwaarden, verbrandingsproducten, brandblussen en luchtvervuiling.'),
        ('zuren', 'Water, zuren en basen', 'NASK2/K/7', 'pH, indicatoren, zure en basische oplossingen, neutraliseren en waterzuivering.'),
        ('productie', 'Productieprocessen en productonderzoek', 'NASK2/V/1, V/2', 'Productieprocessen, scheidingsmethoden, stoffen aantonen en productonderzoek.'),
    ])]}


def biologie_vmbo(lw):
    gt = lw == 'gt'
    ond = [
        ('onderzoek', 'Onderzoek doen', 'BI/K/3', 'Onderzoeksvraag, hypothese, variabelen, proeven en conclusies.'),
        ('cellen', 'Cellen en organisatie', 'BI/K/4', 'Cellen, celdelen, weefsels, organen en organismen; microscoop.'),
        ('ecologie', 'Planten, dieren en hun samenhang', 'BI/K/6', 'Voedselketens en -webben, kringlopen, fotosynthese, ecosystemen en indeling van organismen.'),
        ('voeding', 'Voeding, vertering en energie', 'BI/K/9', 'Voedingsstoffen, gezonde voeding, verteringsorganen en enzymen, energie.'),
        ('transport', 'Ademhaling, bloedsomloop en uitscheiding', 'BI/K/9', 'Longen, hart en bloedvaten, bloed, nieren en huid.'),
        ('prikkels', 'Reageren op prikkels', 'BI/K/11', 'Zintuigen, zenuwstelsel, reflexen en hormonen.'),
        ('voortplanting', 'Voortplanting en ontwikkeling', 'BI/K/12', 'Puberteit, geslachtsorganen, menstruatiecyclus, zwangerschap, anticonceptie en soa.'),
    ]
    if gt:
        ond += [
            ('erfelijkheid', 'Erfelijkheid en evolutie', 'BI/K/13', 'Chromosomen, genen, kruisingen, mutaties, natuurlijke selectie en evolutie.'),
            ('afweer', 'Bescherming en antistoffen', 'BI/V/1', 'Ziekteverwekkers, afweer, antistoffen, vaccinatie en bloedgroepen.'),
            ('gedrag', 'Gedrag bij mens en dier', 'BI/V/2', 'Gedragsvormen, prikkels en reacties, aangeboren en aangeleerd gedrag.'),
        ]
    return {'niveau': VMBO_NAAM[lw], 'naam': 'Biologie', 'domeinen': [('Biologie', ond)]}


for lw, achter in (('bb', 'bb'), ('kb', 'kb'), ('gt', 'gl-tl')):
    VAKKEN[f'wiskunde-vmbo-{achter}'] = wiskunde_vmbo(lw)
    VAKKEN[f'natuur-scheikunde-i-vmbo-{achter}'] = nask1_vmbo(lw)
    VAKKEN[f'biologie-vmbo-{achter}'] = biologie_vmbo(lw)
VAKKEN['natuur-scheikunde-ii-vmbo-gl-tl'] = nask2_vmbo()

NIVEAUS = {'havo': 'Havo', 'vwo': 'Vwo', 'vmbo-bb': 'Vmbo bb', 'vmbo-kb': 'Vmbo kb', 'vmbo-gt': 'Vmbo gl/tl'}


def main():
    bank = json.loads((BRON / 'databank.json').read_text())
    snij = json.loads((BRON / 'snij.json').read_text())
    docs = json.loads((BRON / 'documenten.json').read_text())
    per_examen = defaultdict(dict)
    for d in docs:
        sleutel = re.sub(r'-(o|c|u|c-a\d?|o-e|q|b)$', '', d['code'])
        per_examen[sleutel].setdefault(d['soort'], d['url'])
    UIT.mkdir(parents=True, exist_ok=True)
    overzicht = {'niveaus': NIVEAUS, 'bijgewerkt': date.today().isoformat(), 'vakken': {}}
    for vak, info in VAKKEN.items():
        if not (ROOT / 'indeling' / f'{vak}.json').exists():  # nog niet ingedeeld
            continue
        indeling = json.loads((ROOT / 'indeling' / f'{vak}.json').read_text())
        hint_pad = ROOT / 'hints' / f'{vak}.json'
        hints = json.loads(hint_pad.read_text()) if hint_pad.exists() else {}
        onderwerpen = {s: (n, c, o) for _, lijst in info['domeinen'] for s, n, c, o in lijst}
        vragen, gemist = [], []
        # per opgave de stukken op volgorde, zodat elke vraag de inleiding en eerdere vragen meekrijgt
        stukken_opgave = defaultdict(list)
        for v in bank:
            if v['vak'] != vak:
                continue
            code = v['id'].split(':')[0]
            s = snij.get(code, {}).get(str(v['vraag']))
            if not s or not s.get('maat'):
                gemist.append(v['id'])
                continue
            groep = (code, v['opgave'])
            stukken_opgave[groep].append({'src': s['stuk'], 'w': s['maat'][0], 'h': s['maat'][1], 'vraag': v['vraag']})
            ow = indeling.get(v['id'])
            if ow not in onderwerpen:
                gemist.append(v['id'])
                continue
            links = per_examen[code]
            vragen.append({
                'id': v['id'], 'examen': code, 'jaar': v['jaar'], 'tijdvak': v['tijdvak'], 'opgave': v['opgave'],
                'vraag': v['vraag'], 'punten': v['punten'], 'onderwerp': ow,
                'stukken': list(stukken_opgave[groep]),
                'antwoord': {'src': s['antwoord'], 'w': s['antwoordMaat'][0], 'h': s['antwoordMaat'][1]} if s.get('antwoord') and s.get('antwoordMaat') else None,
                'tekst': v['tekst'],
                'pdf': {k: links.get(k) for k in ('opgaven', 'correctievoorschrift', 'uitwerkbijlage', 'correctievoorschrift-aanvulling', 'opgaven-erratum') if links.get(k)},
                'uitwerkbijlage': 'uitwerkbijlage' in v['tekst'].lower(),
                **({'hint': hints[v['id']]} if v['id'] in hints else {}),
            })
        vragen.sort(key=lambda q: (-q['jaar'], q['tijdvak'], q['vraag']))
        (UIT / f'{vak}.json').write_text(json.dumps({'vak': vak, 'vragen': vragen}, ensure_ascii=False, separators=(',', ':')))
        tel = defaultdict(lambda: [0, 0])
        for q in vragen:
            tel[q['onderwerp']][0] += 1
            tel[q['onderwerp']][1] += q['punten']
        examens = sorted({(q['jaar'], q['tijdvak'], q['examen']) for q in vragen}, reverse=True)
        overzicht['vakken'][vak] = {
            'niveau': info['niveau'], 'naam': info['naam'], 'opmerking': info.get('opmerking', ''), 'vragen': len(vragen), 'examens': [{'jaar': j, 'tijdvak': t, 'code': c} for j, t, c in examens],
            # onderwerpen zonder vragen (bijvoorbeeld evenwicht bij havo) laten we weg
            'domeinen': [d for d in ({'naam': dn, 'onderwerpen': [{'id': s, 'naam': n, 'code': c, 'omschrijving': o, 'vragen': tel[s][0], 'punten': tel[s][1]} for s, n, c, o in lijst if tel[s][0]]} for dn, lijst in info['domeinen']) if d['onderwerpen']],
        }
        print(f'{vak}: {len(vragen)} vragen, {len(examens)} examens' + (f', {len(gemist)} overgeslagen: {gemist[:5]}' if gemist else ''))
    (UIT / 'vakken.json').write_text(json.dumps(overzicht, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
