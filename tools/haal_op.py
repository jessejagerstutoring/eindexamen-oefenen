"""
Haalt de centrale examens (standaard wiskunde) van examenblad.nl op (examenjaren 2018 t/m nu).

Per examenjaar en niveau zoekt het script de vakpagina's van wiskunde, leest daar de
documenten van tijdvak 1 en 2 (opgaven, correctievoorschrift, aanvullingen, uitwerkbijlage)
en zet ze in pdf/<niveau>/<vak>/. Van elke pdf komt ook een tekstversie in tekst/ (pdftotext -layout).

Draaien (vanuit de map eindexamen-oefenen):
    python3 tools/haal_op.py                                   alle wiskundevakken, alle niveaus
    python3 tools/haal_op.py natuurkunde scheikunde --niveau havo vwo
    python3 tools/haal_op.py nederlands engels --doel onderzoek/andere-vakken/bronnen --niveau havo vwo
        (talen en maatschappijvakken; --doel houdt ze buiten bronnen/ en dus buiten de site; --doel vóór --niveau)
        met --jaar 2024 alleen dat jaar, in documenten-2024.json (zo kun je jaren parallel ophalen)

Al opgehaalde bestanden worden overgeslagen, dus opnieuw draaien haalt alleen wat nieuw is.
De pdf's blijven lokaal (*.pdf staat in .gitignore). Auteursrecht: Staat der Nederlanden;
hergebruik mag met bronvermelding en zonder wijzigingen (examenblad.nl/over-examenblad/copyright).
"""
import json
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HIER = Path(__file__).parent.parent / 'bronnen'
BASIS = 'https://www.examenblad.nl'
JAREN = range(2018, 2027)
NIVEAUS = ['vmbo-bb', 'vmbo-kb', 'vmbo-gl', 'vmbo-tl', 'havo', 'vwo']
# rubrieken op examenblad.nl; vakken buiten de exacte vakken staan los van de site (zie onderzoek/andere-vakken)
CATEGORIEEN = ['exacte-vakken', 'maatschappijvakken', 'talen', 'kunstvakken-lo']
# varianten die we bewust overslaan: Caribische versies en de elementaire taalexamens
OVERSLAAN = re.compile(r'-cariben|-elementair')
KOP = {'User-Agent': 'Mozilla/5.0 (Oefenlab examenanalyse; contact via examenblad-pagina)'}

# documentsoort uit de laatste letters van de code, bijv. ha-1024-a-24-1-c-a1
SOORT = {'o': 'opgaven', 'c': 'correctievoorschrift', 'u': 'uitwerkbijlage', 'b': 'bijlage', 'q': 'opgaven-extra', 'o-e': 'opgaven-erratum'}


def haal(url, binair=False, pogingen=3):
    for i in range(pogingen):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=KOP), timeout=60) as r:
                data = r.read()
                return (data, r.geturl()) if binair else data.decode('utf-8', 'replace')
        except Exception as e:  # netwerkfout: even wachten en opnieuw
            if i == pogingen - 1:
                print('  mislukt:', url, e, file=sys.stderr)
                return (None, None) if binair else ''
            time.sleep(2 + 3 * i)


def soort(code):
    m = re.search(r'-\d\d-[12]-(.+)$', code)
    staart = m.group(1) if m else ''
    if staart.startswith('c-a'):
        return 'correctievoorschrift-aanvulling'
    return SOORT.get(staart, staart or 'onbekend')


def main():
    args = sys.argv[1:]
    niveaus = NIVEAUS
    if '--niveau' in args:
        i = args.index('--niveau')
        niveaus, args = args[i + 1:], args[:i]
    global HIER
    if '--doel' in args:              # andere map dan bronnen/, zodat de site-pijplijn er niets van ziet
        i = args.index('--doel')
        HIER, args = Path(args[i + 1]).resolve(), args[:i] + args[i + 2:]
    jaren = JAREN
    lijst_pad = HIER / 'documenten.json'
    if '--jaar' in args:              # één examenjaar, met een eigen lijst; zo kunnen jaren parallel worden opgehaald
        i = args.index('--jaar')
        jaren, args = [int(args[i + 1])], args[:i] + args[i + 2:]
        lijst_pad = HIER / f'documenten-{jaren[0]}.json'
    vakpatroon = '|'.join(args or ['wiskunde'])
    lijst = json.loads(lijst_pad.read_text()) if lijst_pad.exists() else []
    if lijst_pad.name != 'documenten.json' and (HIER / 'documenten.json').exists():
        lijst += [d for d in json.loads((HIER / 'documenten.json').read_text())
                  if d['jaar'] in jaren and d['code'] not in {x['code'] for x in lijst}]
    gezien = {d['code'] for d in lijst}
    for jaar in jaren:
        for niveau in niveaus:
            vakken = []
            for cat in CATEGORIEEN:
                html = haal(f'{BASIS}/{jaar}/{niveau}/vakken/{cat}')
                vakken += [(cat, v) for v in sorted(set(re.findall(rf'/{jaar}/{niveau}/vakken/{cat}/((?:{vakpatroon})[a-z0-9-]*)', html)))
                           if not OVERSLAAN.search(v)]
            for cat, vak in vakken:
                vhtml = haal(f'{BASIS}/{jaar}/{niveau}/vakken/{cat}/{vak}')
                docs = sorted(set(re.findall(rf'/{jaar}/{niveau}/documenten/(cse-[12])/([a-z]{{2}}-\d{{4}}-[a-z]-\d\d-[12][a-z0-9-]*)', vhtml)))
                for tijdvak, code in docs:
                    if code in gezien:
                        continue
                    map_ = HIER / 'pdf' / niveau / vak
                    map_.mkdir(parents=True, exist_ok=True)
                    pdf = map_ / f'{code}.pdf'
                    data, echt = haal(f'{BASIS}/{jaar}/{niveau}/documenten/{tijdvak}/{code}', binair=True)
                    if not data or not data.startswith(b'%PDF'):
                        print('  geen pdf:', jaar, niveau, code, file=sys.stderr)
                        continue
                    pdf.write_bytes(data)
                    txt = HIER / 'tekst' / niveau / vak / f'{code}.txt'
                    txt.parent.mkdir(parents=True, exist_ok=True)
                    subprocess.run(['pdftotext', '-layout', str(pdf), str(txt)], check=False)
                    lijst.append({'code': code, 'jaar': jaar, 'niveau': niveau, 'vak': vak, 'categorie': cat, 'tijdvak': int(tijdvak[-1]),
                                  'soort': soort(code), 'url': echt, 'pdf': str(pdf.relative_to(HIER)), 'tekst': str(txt.relative_to(HIER))})
                    gezien.add(code)
                    print(f'{jaar} {niveau:8} {vak:22} {code}', flush=True)
                    time.sleep(0.4)
            lijst.sort(key=lambda d: (d['niveau'], d['vak'], d['jaar'], d['tijdvak'], d['code']))
            lijst_pad.write_text(json.dumps(lijst, ensure_ascii=False, indent=1))  # tussentijds opslaan
    print(f'\n{len(lijst)} documenten in documenten.json')


if __name__ == '__main__':
    main()
