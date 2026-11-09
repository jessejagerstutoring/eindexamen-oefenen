"""
Eerste indeling van de vragen uit de andere vakken, op basis van wat het examen zelf aangeeft.

Per vraag: examen, nummer, punten, meerkeuze of open, de opgave (titel), en waar mogelijk een indeling:
  - aardrijkskunde: het domein staat als kopje in het examen (Wereld, Aarde, Ontwikkelingsland, Leefomgeving)
  - geschiedenis: het tijdvak of thema staat als kopje in het examen (Vroegmoderne tijd, Moderne tijd, ...)
  - talen en Nederlands: de tekst waar de vraag bij hoort ('Tekst 4 Vraatzucht') en het vraagtype, herkend aan de
    formulering (open plek, juist/onjuist, citeren, functie of verband, hoofdgedachte, ...)
  - economie, bedrijfseconomie, maatschappijwetenschappen, filosofie: alleen de opgave; een voorstel voor het
    concept of domein op trefwoorden (zwak: altijd met de hand nakijken, zoals bij de bètavakken)

Draaien (vanuit de map eindexamen-oefenen, na analyse.py):
    ~/env/bin/python onderzoek/andere-vakken/indeling.py

Uitvoer: onderzoek/andere-vakken/data/indeling/<vak>.json en een telling in data/indeling/overzicht.json.
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HIER = Path(__file__).parent
sys.path.insert(0, str(HIER))
sys.path.insert(0, str(HIER.parent.parent / 'tools'))
from analyse import BRON, alle_documenten  # noqa: E402
from bouw_databank import KOPTEKST, lees_correctie  # noqa: E402

UIT = HIER / 'data' / 'indeling'

# kopjes die het examen zelf gebruikt
DOMEINKOP = {
    'aardrijkskunde': ['Wereld', 'Aarde', 'Ontwikkelingsland', 'Leefomgeving', 'Gebiedsstudie', 'Vaardigheden'],
    'geschiedenis': ['Prehistorie', 'Oudheid', 'Middeleeuwen', 'middeleeuwen', 'Vroegmoderne tijd', 'Moderne tijd',
                     'Tijd van', 'Thema', 'Historische context', 'Republiek', 'Verlichting', 'Duitsland', 'Koude Oorlog',
                     'Steden en burgers', 'Nederland', 'Britse', 'Oriëntatiekennis', 'Rechtsstaat', 'rechtsstaat'],
}
TEKSTKOP = re.compile(r'^\s{0,10}(Tekst|Text|Texte|Texto|Testo)\s+(\d{1,2})(?:\s+(?:en|t/m)\s+\d{1,2})?\b\s*(.*)$')
OPGAVEKOP = re.compile(r'^\s{0,10}Opgave\s+(\d{1,2})\b\s*(.*)$')
VRAAG = re.compile(r'^\s{0,8}(\d{1,2})p\s+(\d{1,2})\s+(.*)$')

# vraagtypes bij leesvaardigheid (de vragen staan in het Nederlands, ook bij de moderne vreemde talen)
VRAAGTYPES = [
    ('open plek', r'open plek|past (?:het best )?(?:in|op) de open|invullen op de plaats'),
    ('juist of onjuist', r'wel of niet overeen|juist of onjuist|klopt of niet|wel of niet in de tekst|geef (?:van|bij) elk(?:e)? .* aan of'),
    ('citeren', r'citeer|eerste (?:en laatste )?woord|schrijf .* over'),
    ('functie of verband', r'functie|verband|verhouding|relatie|hoe verhoudt|wat is de rol'),
    ('hoofdgedachte of bedoeling', r'hoofdgedachte|bedoeling|doel van|kernboodschap|hoofdzaak|strekking|standpunt|centrale vraag'),
    ('samenvatten', r'vat .* samen|samenvatting'),
    ('argumentatie', r'argument|drogreden|redenering|bewering .* onderbouw'),
    ('betekenis of verwijzing', r'wordt bedoeld met|betekent|verwijst|waar verwijst|met .* bedoelt'),
    ('toon of houding', r'toon|houding|ironisch|kritisch|positief|negatief'),
]

# zeer grove trefwoorden per concept (economie); alleen als voorstel
TREFWOORD = {
    'economie': [
        ('schaarste', r'schaars|alternatieve kosten|budgetlijn|keuze|opportunity'),
        ('ruil', r'ruil|specialis|comparatief|arbeidsverdeling|handel'),
        ('markt', r'markt|vraaglijn|aanbodlijn|evenwicht|prijs|consumentensurplus|producentensurplus|monopol|oligopol|elasticiteit'),
        ('ruilen over de tijd', r'sparen|lenen|rente|pensioen|hypotheek|vergrijzing|contante waarde|overheidsschuld|begroting'),
        ('samenwerken en onderhandelen', r'speltheorie|uitbetalingsmatrix|nash|gevangenendilemma|collectieve goederen|externe effecten|meelifter'),
        ('risico en informatie', r'risico|verzeker|informatie|asymmetrische|moral hazard|averechtse selectie|principaal'),
        ('welvaart en groei', r'welvaart|groei|productiviteit|bbp|inkomensverdeling|lorenz|gini|duurzaam'),
        ('goede tijden, slechte tijden', r'conjunctuur|inflatie|werkloosheid|bestedingen|monetair|ecb|wisselkoers|begrotingsbeleid|recessie'),
    ],
}


def vak_familie(vak):
    for f in ('aardrijkskunde', 'geschiedenis', 'economie', 'bedrijfseconomie', 'maatschappij-wetenschappen', 'filosofie',
              'nederlands', 'latijnse', 'griekse', 'kunst', 'muziek'):
        if vak.startswith(f):
            return f
    return 'talen'


def vraagtype(tekst, mk):
    t = tekst.lower()
    for naam, patroon in VRAAGTYPES:
        if re.search(patroon, t):
            return naam
    return 'detailvraag (meerkeuze)' if mk else 'open vraag'


def lees(vak, ex, dd):
    """Alle vragen van één examen, met de kopjes waar ze onder staan."""
    o, c = dd.get('opgaven'), dd.get('correctievoorschrift')
    if not o or not c:
        return []
    cor = {v['nr']: v for v in lees_correctie(BRON / c['tekst'])}
    fam = vak_familie(vak)
    koppen = DOMEINKOP.get(fam, [])
    regels = [r for r in (BRON / o['tekst']).read_text(errors='replace').split('\n') if not KOPTEKST.search(r)]
    sectie = opgave = tekst = None
    uit, i, vorige_leeg = [], 0, True
    while i < len(regels):
        r = regels[i]
        m = VRAAG.match(r)
        if m:
            vraag, k = [m.group(3)], i + 1
            while k < len(regels) and regels[k].strip() and not VRAAG.match(regels[k]):
                vraag.append(regels[k].strip())
                k += 1
            nr = int(m.group(2))
            v = cor.get(nr, {})
            mk = v.get('punten') is None and bool(v)
            q = {'id': f'{ex}:{nr}', 'examen': ex, 'nr': nr, 'punten': int(m.group(1)), 'meerkeuze': mk,
                 'vraag': re.sub(r'\s+', ' ', ' '.join(vraag)).strip()[:300]}
            if opgave:
                q['opgave'] = opgave
            if sectie:
                q['sectie'] = sectie
            if tekst:
                q['tekst'] = tekst
            if fam in ('talen', 'nederlands', 'latijnse', 'griekse'):
                q['vraagtype'] = vraagtype(q['vraag'], mk)
            if fam in TREFWOORD:
                score = Counter()
                for naam, pat in TREFWOORD[fam]:
                    score[naam] = len(re.findall(pat, (q['vraag'] + ' ' + v.get('model', '')).lower()))
                beste = max(score, key=score.get)
                if score[beste]:
                    q['voorstel'] = beste
            uit.append(q)
            i, vorige_leeg = k, False
            continue
        s = r.strip()
        if s:
            mo, mt = OPGAVEKOP.match(r), TEKSTKOP.match(r)
            if mo:
                opgave = f'Opgave {mo.group(1)}' + (f' {mo.group(2).strip()}' if mo.group(2).strip() else '')
            elif mt and len(s) < 80:
                tekst = s
            elif vorige_leeg and len(s) < 50 and len(r) - len(r.lstrip()) <= 8 and any(s.startswith(k) or k in s for k in koppen):
                sectie = s
        vorige_leeg = not s
        i += 1
    return uit


def main():
    per = defaultdict(dict)
    meta = {}
    for d in alle_documenten():
        ex = re.sub(r'-(o|c|u|b|q|a|c-a\d?|o-e)$', '', d['code'])
        per[(d['vak'], ex)].setdefault(d['soort'], d)
        meta[ex] = (d['jaar'], d['tijdvak'])
    UIT.mkdir(parents=True, exist_ok=True)
    overzicht = {}
    for vak in sorted({v for v, _ in per}):
        vragen = []
        for (v, ex), dd in sorted(per.items()):
            if v != vak:
                continue
            for q in lees(vak, ex, dd):
                q['jaar'], q['tijdvak'] = meta[ex]
                vragen.append(q)
        if not vragen:
            overzicht[vak] = {'vragen': 0}
            continue
        (UIT / f'{vak}.json').write_text(json.dumps(vragen, ensure_ascii=False, indent=1))
        o = {'vragen': len(vragen), 'meerkeuze': sum(q['meerkeuze'] for q in vragen)}
        for veld in ('sectie', 'vraagtype', 'voorstel'):
            tel = Counter(q.get(veld) for q in vragen if veld in q or veld == 'sectie')
            if any(k for k in tel):
                o[veld] = dict(tel.most_common())
        o['met_tekst'] = sum(1 for q in vragen if 'tekst' in q)
        overzicht[vak] = o
        print(f"{vak:36} {len(vragen):5} vragen  " + ', '.join(f"{k}: {len(v) if isinstance(v, dict) else v}" for k, v in o.items() if k != 'vragen'))
    (UIT / 'overzicht.json').write_text(json.dumps(overzicht, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
