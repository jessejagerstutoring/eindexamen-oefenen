"""
Databank van de centrale examens wiskunde (examenblad.nl, examenjaren 2018 t/m nu).

Leest de teksten die haal_op.py heeft gemaakt. Het correctievoorschrift geeft de structuur
(opgave, vraagnummer, maximumscore, antwoordmodel); uit de opgaven komen de vraagtekst en de
inleiding (context). Elke vraag krijgt één onderwerp uit ONDERWERPEN van zijn vak: het onderwerp
waarvan de zoekwoorden het vaakst voorkomen in de vraag (telt zwaar) en het antwoordmodel.

Draaien (vanuit de map eindexamen-oefenen, na haal_op.py):
    python3 tools/bouw_databank.py

Uitvoer:
    bronnen/databank.json   alle vragen met tekst, antwoordmodel en onderwerp
    bronnen/RAPPORT.md      per vak: wat komt hoe vaak terug, in hoeveel examens, hoeveel punten

Klopt een indeling niet, zet dan de vraag in HANDMATIG (sleutel zoals 'ha-1024-a-25-1:7').
"""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

HIER = Path(__file__).parent.parent / 'bronnen'

VAKNAAM = {
    'wiskunde-vmbo-bb': 'Wiskunde vmbo-bb', 'wiskunde-vmbo-kb': 'Wiskunde vmbo-kb', 'wiskunde-vmbo-gl-tl': 'Wiskunde vmbo-gl/tl',
    'wiskunde-a-havo': 'Wiskunde A havo', 'wiskunde-b-havo': 'Wiskunde B havo',
    'wiskunde-a-vwo': 'Wiskunde A vwo', 'wiskunde-b-vwo': 'Wiskunde B vwo', 'wiskunde-c-vwo': 'Wiskunde C vwo',
}

# ---------- onderwerpen per soort vak: (sleutel, naam, zoekwoorden) ----------
# zoekwoorden zijn reguliere expressies op kleine letters
STAT = [
    ('toetsen', 'Hypothesen toetsen', r'hypothese|toetsingsprocedure|toetsingsgrootheid|significantieniveau|overschrijdingskans|verwerp|kritieke gebied|kritiek gebied'),
    ('betrouwbaarheid', 'Betrouwbaarheidsintervallen', r'betrouwbaarheidsinterval|populatieproportie|populatiegemiddelde|betrouwbaarheidsinterval'),
    ('verschil', 'Verschil tussen groepen (effectgrootte, phi, boxplots)', r'effectgrootte|\bphi\b|kruistabel|max ?vcp|cumulatie?f? percentage|verschil (is |tussen .*)?(groot|gering|middelmatig)|boxplot'),
    ('normaal', 'Normale verdeling', r'normaal verdeeld|normale verdeling|normale kromme|normaal-?verdel|normalcdf|invnorm|standaardafwijking'),
    ('binomiaal', 'Binomiale verdeling', r'binomia|binompdf|binomcdf|succeskans'),
    ('kans', 'Kansrekening en verwachtingswaarde', r'\bkans\b|kansen|verwachtingswaarde|verwachte|kansverdeling|kansboom|gemiddeld .*winst'),
    ('tellen', 'Combinatoriek (tellen)', r'hoeveel (verschillende )?(mogelijkheden|manieren|codes|volgordes|combinaties|routes)|combinatie|permutatie|faculteit|boomdiagram|wegendiagram|rooster'),
    ('beschrijvend', 'Beschrijvende statistiek', r'gemiddelde|mediaan|kwartiel|modus|frequentie|histogram|steekproef|percentiel|spreidingsbreedte|klassen|staafdiagram|cirkeldiagram|ogief'),
]
ANALYSE_A = [
    ('afgeleide', 'Afgeleide en veranderingssnelheid', r'afgeleide|differentie|helling|raaklijn|toenamediagram|veranderingssnelheid|groeisnelheid|hellinggrafiek|snelheid waarmee|neemt .* (sneller|langzamer)|stijgt .* (sneller|langzamer)|toenemend|afnemend (stijgend|dalend)'),
    ('exponentieel', 'Exponentiële groei', r'groeifactor|groeipercentage|exponenti|halverings|verdubbelings|procent per|% per|toename per (jaar|maand|week|dag)|\^ ?t\b|helft|\bg ?= ?\d'),
    ('logaritme', 'Logaritmen', r'\blog\b|logaritm|\bln\b|log-?schaal|logaritmisch|richter|decibel|\bdb\b'),
    ('periodiek', 'Periodieke functies', r'periodiek|sinus|\bsin\b|periode|amplitude|evenwichtsstand'),
    ('rijen', 'Rijen en recursie', r'\brij\b|rijen|recursi|directe formule|somformule|\bterm\b|termen'),
    ('formules', 'Formules en verbanden (lineair, machts, omgekeerd evenredig)', r'formule|herleid|lineair|evenredig|machtsverband|machtsfunctie|kwadratisch|parabool|verband|schrijf .* in de vorm|wortel'),
    ('grafieken', 'Grafieken en vergelijkingen', r'grafiek|vergelijking|ongelijkheid|bereken (algebraïsch )?(bij welke|wanneer|vanaf|in welk)|snijpunt|maximum|minimum|top'),
    ('rekenen', 'Rekenen met procenten en verhoudingen', r'procent|percentage|%|verhouding|index|indexcijfer|schaal|gemiddelde snelheid|eenheid'),
    ('logica', 'Logisch redeneren en grafen', r'graaf|grafen|logisch|ware uitspraak|redeneer|beweer|venn|schema|tabel .* (invullen|aanvullen)'),
]
ANALYSE_B = [
    ('integraal', 'Integraalrekening (oppervlakte, inhoud)', r'integra|primitie|oppervlakte (van|tussen|onder) .*(grafiek|vlakdeel|gebied)|inhoud .*(omwentel|wentel)|omwentel|wentel'),
    ('afgeleide', 'Differentiëren en raaklijnen', r'afgeleide|differentie|helling|raaklijn|richtingscoëfficiënt|extreme? waarde|maxim|minim|buigpunt|toenemend|afnemend|snelheid'),
    ('goniometrie', 'Goniometrie en periodieke functies', r'\bsin|\bcos|\btan|radialen|goniometri|periode|amplitude|evenwichtsstand|sinusoïde'),
    ('exp-log', 'Exponentiële en logaritmische functies', r'\be\^|\be\b|exponenti|\blog\b|\bln\b|logaritm|groeifactor|halverings|verdubbel'),
    ('meetkunde', 'Meetkunde met coördinaten en vectoren', r'cirkel|vector|hoek|driehoek|vierhoek|afstand|middelloodlijn|loodrecht|evenwijdig|coördinaten|punt [a-z] |bissectrice|parameter|bewegingsvergelijking|raakt'),
    ('transformaties', 'Functies, transformaties en asymptoten', r'verschuiv|vermenigvuldig|transformatie|asymptoot|asymptoten|symmetrisch|domein|bereik|inverse|samengestelde|spiegel'),
    ('vergelijkingen', 'Vergelijkingen en ongelijkheden', r'vergelijking|ongelijkheid|exact|algebraïsch|snijpunt|nulpunt|los op|bereken .* waarde'),
    ('formules', 'Formules herleiden en modelleren', r'formule|herleid|schrijf .* in de vorm|toon aan|druk .* uit|model|evenredig|wortel|gebroken'),
]
VMBO = [
    ('ruimte', 'Ruimtemeetkunde (inhoud, oppervlakte, aanzichten)', r'inhoud|oppervlakte|aanzicht|uitslag|kubus|balk|cilinder|prisma|piramide|kegel|\bbol\b|doorsnede|liter|cm³|m³|dm³|cm2|m2|cm²|m²'),
    ('vlak', 'Vlakke meetkunde (Pythagoras, goniometrie, hoeken)', r'pythagoras|schuine|tangens|sinus|cosinus|\btan\b|\bsin\b|\bcos\b|hoek|driehoek|graden|loodrecht|omtrek|cirkel|straal|diameter'),
    ('schaal', 'Schaal, vergroten en tekenen', r'schaal|vergroting|vergrotingsfactor|verkleining|teken|tekening|ware grootte|constructie|kaart'),
    ('procenten', 'Procenten en verhoudingen', r'procent|%|korting|btw|rente|verhouding|prijs|euro|€|goedkoper|duurder'),
    ('formules', 'Formules, grafieken en vergelijkingen', r'formule|grafiek|tabel|lineair|kwadratisch|vergelijking|assenstelsel|snijpunt|toename|afname|recht evenredig|patroon'),
    ('statistiek', 'Statistiek en kans', r'gemiddelde|mediaan|modus|diagram|kans|frequentie|steekproef|boxplot|spreiding'),
    ('rekenen', 'Rekenen en eenheden (tijd, snelheid, omrekenen)', r'omreken|km/u|km/h|snelheid|tijd|minuten|uur|seconden|eenheid|meter|kilometer|gram|kilo|afgerond'),
]
ONDERWERPEN = {
    'wiskunde-a-havo': ANALYSE_A + STAT, 'wiskunde-a-vwo': ANALYSE_A + STAT, 'wiskunde-c-vwo': ANALYSE_A + STAT,
    'wiskunde-b-havo': ANALYSE_B, 'wiskunde-b-vwo': ANALYSE_B,
    'wiskunde-vmbo-bb': VMBO, 'wiskunde-vmbo-kb': VMBO, 'wiskunde-vmbo-gl-tl': VMBO,
}
HANDMATIG = {}

KOPTEKST = re.compile(r'^\s*([A-Z]{2}-\d{4}-[a-z]-\d\d-[12]-[a-z])\b|lees verder|^\s*\d+\s*/\s*\d+\s*$|einde\s*$', re.I)


def vaknaam(vak):
    kaal = vak.replace('-bezemexamen', '')
    return VAKNAAM.get(kaal, kaal) + (' (bezemexamen, oud programma)' if kaal != vak else '')


def schoon(regels):
    return re.sub(r'\s+', ' ', ' '.join(r.strip() for r in regels)).strip()


def lees_correctie(pad):
    """[(opgave-titel, vraagnr, maximumscore, antwoordmodel)] uit een correctievoorschrift."""
    regels = pad.read_text(encoding='utf-8', errors='replace').split('\n')
    vragen, titel, huidige, verwacht = [], '', None, 1
    for i, r in enumerate(regels):
        if re.search(r'bronvermelding', r, re.I) and vragen:
            break
        m = re.match(r'^\s{0,10}(\d{1,2})\s+maximumscore\s+(\d+)', r) or re.match(r'^\s{0,10}(\d{1,2})\s+([A-F])\s*$', r)
        if m:
            nr = int(m.group(1))
            if nr != verwacht or re.search(r'vakspecifieke regel', ' '.join(regels[i + 1:i + 3])):  # bijvoorbeeld een totaal onderaan, of een opsomming in de algemene regels
                continue
            # de titel van een opgave staat vlak boven de eerste vraag, smal ingesprongen, na een lege regel
            k = i - 1
            while k > 0 and not regels[k].strip():
                k -= 1
            kandidaat = regels[k]
            if kandidaat.strip() and len(kandidaat) - len(kandidaat.lstrip()) <= 8 and len(kandidaat.strip()) < 70 \
                    and not regels[k - 1].strip() and not re.search(r'maximumscore|^\s*[•▪-]', kandidaat):
                titel = kandidaat.strip()
                if huidige and huidige['model'] and huidige['model'][-1].strip() == titel:
                    huidige['model'].pop()
            mk = not m.group(2).isdigit()  # meerkeuzevraag: alleen de letter, de punten staan in de opgaven
            huidige = {'titel': titel, 'nr': nr, 'punten': None if mk else int(m.group(2)), 'model': [f'Antwoord {m.group(2)}'] if mk else []}
            vragen.append(huidige)
            verwacht += 1
        elif huidige is not None and not KOPTEKST.search(r):
            huidige['model'].append(r)
    for v in vragen:
        v['model'] = schoon(v['model'])[:1500]
    return vragen


def lees_opgaven(pad):
    """{vraagnr: (punten, vraagtekst, inleiding)} uit de opgaven; de inleiding is de tekst sinds de vorige vraag."""
    regels = [r for r in pad.read_text(encoding='utf-8', errors='replace').split('\n') if not KOPTEKST.search(r)]
    uit, sinds = {}, []
    i = 0
    while i < len(regels):
        m = re.match(r'^\s{0,8}(\d{1,2})p\s+(\d{1,2})\s+(.*)$', regels[i])
        if m:
            vraag, k = [m.group(3)], i + 1
            while k < len(regels) and regels[k].strip() and not re.match(r'^\s{0,8}\d{1,2}p\s', regels[k]):
                vraag.append(regels[k])
                k += 1
            uit[int(m.group(2))] = (int(m.group(1)), schoon(vraag)[:800], schoon(sinds)[-1500:])
            sinds, i = [], k
        else:
            sinds.append(regels[i])
            i += 1
    return uit


def onderwerp(vak, tekst, model, context):
    lijst = ONDERWERPEN.get(vak.replace('-bezemexamen', ''))
    if not lijst:
        return None, {}
    score = Counter()
    for sleutel, _, patroon in lijst:
        score[sleutel] += 3 * len(re.findall(patroon, tekst.lower())) + 1.5 * len(re.findall(patroon, model.lower())) + 0.75 * len(re.findall(patroon, context.lower()[-900:]))
    volgorde = {s: i for i, (s, _, _) in enumerate(lijst)}
    beste = max(score, key=lambda s: (score[s], -volgorde[s]))
    return (beste if score[beste] > 0 else None), {k: v for k, v in score.items() if v}


def main():
    docs = json.loads((HIER / 'documenten.json').read_text())
    per_examen = defaultdict(dict)
    for d in docs:
        if d['soort'] in ('opgaven', 'correctievoorschrift'):
            sleutel = re.sub(r'-[oc]$', '', d['code'])
            per_examen[sleutel][d['soort']] = d
    alle, problemen = [], []
    for code, ex in sorted(per_examen.items()):
        meta = ex.get('correctievoorschrift') or ex.get('opgaven')
        cv = lees_correctie(HIER / ex['correctievoorschrift']['tekst']) if 'correctievoorschrift' in ex else []
        opg = lees_opgaven(HIER / ex['opgaven']['tekst']) if 'opgaven' in ex else {}
        if not cv:  # geen bruikbaar correctievoorschrift: dan alleen de opgaven
            cv = [{'titel': '', 'nr': nr, 'punten': p, 'model': ''} for nr, (p, _, _) in sorted(opg.items())]
        if not cv:
            problemen.append(f'{code}: geen vragen gevonden')
            continue
        if opg and len(opg) != len(cv):
            problemen.append(f'{code}: {len(cv)} vragen in correctievoorschrift, {len(opg)} in opgaven')
        for v in cv:
            p, tekst, context = opg.get(v['nr'], (None, '', ''))
            if v['punten'] is None:
                v['punten'] = p or 1
            elif p is not None and p != v['punten']:
                problemen.append(f"{code}:{v['nr']} punten {p} (opgaven) tegen {v['punten']} (correctievoorschrift)")
            sleutel = f"{code}:{v['nr']}"
            ow, scores = (HANDMATIG[sleutel], {}) if sleutel in HANDMATIG else onderwerp(meta['vak'], tekst, v['model'], context)
            alle.append({'id': sleutel, 'niveau': meta['niveau'], 'vak': meta['vak'], 'jaar': meta['jaar'], 'tijdvak': meta['tijdvak'],
                         'opgave': v['titel'], 'vraag': v['nr'], 'punten': v['punten'], 'tekst': tekst, 'context': context,
                         'antwoordmodel': v['model'], 'onderwerp': ow, 'scores': scores,
                         'bron': (ex.get('opgaven') or meta)['url']})
    (HIER / 'databank.json').write_text(json.dumps(alle, ensure_ascii=False, indent=1), encoding='utf-8')

    # ---------- rapport ----------
    r = ['# Centrale examens wiskunde, examenblad.nl', '',
         'Gemaakt door `bronnen/bouw_databank.py`. Bron: examenblad.nl (© Staat der Nederlanden).', '',
         '| Vak | Examens | Jaren | Vragen | Punten per examen | Vragen zonder onderwerp |', '|---|---|---|---|---|---|']
    vakken = sorted({d['vak'] for d in alle}, key=lambda v: (v.endswith('bezemexamen'), list(VAKNAAM).index(v.replace('-bezemexamen', '')) if v.replace('-bezemexamen', '') in VAKNAAM else 99))
    for vak in vakken:
        vs = [d for d in alle if d['vak'] == vak]
        ex = {d['id'].split(':')[0] for d in vs}
        jaren = sorted({d['jaar'] for d in vs})
        r.append(f"| {vaknaam(vak)} | {len(ex)} | {jaren[0]}–{jaren[-1]} | {len(vs)} | {round(sum(d['punten'] for d in vs) / len(ex))} | {sum(1 for d in vs if not d['onderwerp'])} |")
    for vak in vakken:
        vs = [d for d in alle if d['vak'] == vak]
        ex = sorted({d['id'].split(':')[0] for d in vs})
        tot = sum(d['punten'] for d in vs)
        namen = {s: n for s, n, _ in ONDERWERPEN.get(vak.replace('-bezemexamen', ''), [])}
        r += ['', f'## {vaknaam(vak)}', '', f'{len(ex)} examens, {len(vs)} vragen, {tot} punten.', '',
              '| Onderwerp | Vragen | In examens | Punten | Aandeel punten |', '|---|---|---|---|---|']
        per = defaultdict(list)
        for d in vs:
            per[d['onderwerp']].append(d)
        for ow, ds in sorted(per.items(), key=lambda kv: -sum(d['punten'] for d in kv[1])):
            p = sum(d['punten'] for d in ds)
            r.append(f"| {namen.get(ow, ow or '(geen)')} | {len(ds)} | {len({d['id'].split(':')[0] for d in ds})}/{len(ex)} | {p} | {round(100 * p / tot)}% |")
        r += ['', '<details><summary>Voorbeelden per onderwerp</summary>', '']
        for ow, ds in per.items():
            r.append(f"**{namen.get(ow, ow or '(geen)')}**")
            for d in ds[:3]:
                r.append(f"- {d['jaar']}-{d['tijdvak']} vraag {d['vraag']} ({d['punten']}p, {d['opgave']}): {d['tekst'][:150]}")
            r.append('')
        r.append('</details>')
    if problemen:
        r += ['', '## Controle', '', f'{len(problemen)} meldingen bij het inlezen:', ''] + [f'- {p}' for p in problemen]
    (HIER / 'RAPPORT.md').write_text('\n'.join(r) + '\n', encoding='utf-8')
    print(f'{len(alle)} vragen uit {len(per_examen)} examens; {sum(1 for d in alle if not d["onderwerp"])} zonder onderwerp; {len(problemen)} meldingen')
    for p in problemen[:25]:
        print('  ', p)


if __name__ == '__main__':
    main()
