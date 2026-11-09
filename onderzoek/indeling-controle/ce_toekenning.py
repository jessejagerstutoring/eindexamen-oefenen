"""
Leest uit de syllabi (bronnen/syllabus/<vak>.txt, pdftotext -layout) welke (sub)domeinen in het centraal examen
getoetst kunnen worden. Elke syllabus heeft een tabel 'Domeinindeling en CE-toekenning' met kolommen als
'in CE' / 'moet in SE' / 'mag in SE' (bèta) of 'CE' / 'SE' (biologie). Per regel met een kruisje bepaalt dit
script in welke kolom het kruisje staat.

Draaien (vanuit eindexamen-oefenen):  python3 onderzoek/indeling-controle/ce_toekenning.py
Uitvoer: onderzoek/indeling-controle/ce_toekenning.json  {vak: [{code, naam, ce, se, opmerking}]}
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
SYL = ROOT / 'bronnen' / 'syllabus'
VAKKEN = ['wiskunde-a-havo', 'wiskunde-b-havo', 'wiskunde-a-vwo', 'wiskunde-b-vwo', 'wiskunde-c-vwo',
          'natuurkunde-havo', 'natuurkunde-vwo', 'scheikunde-havo', 'scheikunde-vwo', 'biologie-havo', 'biologie-vwo']
CODE = re.compile(r'(?<![A-Za-z0-9])([A-I](?:\d{1,2})?\*?)(?![A-Za-z0-9])')


def kolommen(regels, i):
    """Posities van de kolomkoppen ('in CE', 'CE', 'SE', 'moet in SE', 'mag in SE') rond regel i."""
    kop = ' '.join(regels[i:i + 2])
    pos = {}
    for r in regels[i:i + 2]:
        for m in re.finditer(r'\b(CE\d?|SE|moet|mag)\b', r):
            pos.setdefault(m.group(1).rstrip('0123456789'), []).append(m.start())
    return pos, kop


def tabel(vak):
    regels = (SYL / f'{vak}.txt').read_text(errors='replace').split('\n')
    start = next((i for i, r in enumerate(regels) if re.search(r'\bin\s*$|\bCE\d?\s+SE\b|in CE|in\s+moet\s+mag', r)
                  and re.search(r'Domein', ' '.join(regels[max(0, i - 2):i + 1]))), None)
    if start is None:
        return []
    # kolomgrenzen: het midden tussen CE en de eerste SE-kolom
    kop = '\n'.join(regels[start:start + 2])
    ce_x = max([m.start() for m in re.finditer(r'\bCE\d?\b', kop.split('\n')[-1])] +
               [m.start() for m in re.finditer(r'\bin\b', kop.split('\n')[0])][-1:] or [0])
    se_cols = [m.start() for r in regels[start:start + 2] for m in re.finditer(r'\b(SE|moet|mag)\b', r)]
    uit, huidig_domein = [], ''
    for r in regels[start + 2:start + 80]:
        if re.search(r'Pagina \d+ van|^\s*\*|bk =|Let op|^\s*\d\s*$', r) and uit:
            if re.search(r'Pagina \d+ van', r):
                continue
        xs = [m.start() for m in re.finditer(r'(?<![A-Za-z])(X\d?|bk\*?)(?![A-Za-z])', r)]
        codes = CODE.findall(r[:max(xs)] if xs else r)
        if not xs:
            if re.match(r'\s{0,8}(BIJLAGE|\d\s+[A-Z])', r) and uit:
                break
            continue
        naam = re.sub(r'\s{2,}', ' | ', r[:min(xs)].strip())
        ce = any(abs(x - ce_x) <= 4 for x in xs)
        se = [x for x in xs if abs(x - ce_x) > 4]
        bk = 'bk' in r
        uit.append({'regel': naam, 'ce': ce, 'se': bool(se) or bk, 'beperkte_keuze': bk})
    return uit


def main():
    alles = {}
    for vak in VAKKEN:
        t = tabel(vak)
        alles[vak] = t
        print(f'\n=== {vak}')
        for x in t:
            print(f"  {'CE' if x['ce'] else '  '} {'SE' if x['se'] else '  '} {'bk' if x['beperkte_keuze'] else '  '}  {x['regel'][:90]}")
    (Path(__file__).parent / 'ce_toekenning.json').write_text(json.dumps(alles, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
