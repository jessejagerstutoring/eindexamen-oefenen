"""
Zet de gegevens voor de site klaar in docs/data/.

Leest bronnen/databank.json (vragen), indeling/<vak>.json (onderwerp per vraag, met de hand
ingedeeld volgens de syllabus), bronnen/snij.json (beelden per vraag) en bronnen/documenten.json
(links naar de originele pdf's op examenblad.nl).

Draaien (vanuit de map eindexamen-oefenen, na snij.py):
    python3 tools/bouw_site.py
"""
import json
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

NIVEAUS = {'havo': 'Havo', 'vwo': 'Vwo'}


def main():
    bank = json.loads((BRON / 'databank.json').read_text())
    snij = json.loads((BRON / 'snij.json').read_text())
    docs = json.loads((BRON / 'documenten.json').read_text())
    per_examen = defaultdict(dict)
    for d in docs:
        sleutel = re.sub(r'-(o|c|u|c-a\d?|o-e|q|b)$', '', d['code'])
        per_examen[sleutel].setdefault(d['soort'], d['url'])
    UIT.mkdir(parents=True, exist_ok=True)
    overzicht = {'niveaus': NIVEAUS, 'vakken': {}}
    for vak, info in VAKKEN.items():
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
            'domeinen': [{'naam': dn, 'onderwerpen': [{'id': s, 'naam': n, 'code': c, 'omschrijving': o, 'vragen': tel[s][0], 'punten': tel[s][1]} for s, n, c, o in lijst]} for dn, lijst in info['domeinen']],
        }
        print(f'{vak}: {len(vragen)} vragen, {len(examens)} examens' + (f', {len(gemist)} overgeslagen: {gemist[:5]}' if gemist else ''))
    (UIT / 'vakken.json').write_text(json.dumps(overzicht, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
