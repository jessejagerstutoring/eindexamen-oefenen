"""
Haalt de centrale examens (standaard wiskunde) van examenblad.nl op (examenjaren 2018 t/m nu).

Per examenjaar en niveau zoekt het script de vakpagina's van wiskunde, leest daar de
documenten van tijdvak 1 en 2 (opgaven, correctievoorschrift, aanvullingen, uitwerkbijlage)
en zet ze in pdf/<niveau>/<vak>/. Van elke pdf komt ook een tekstversie in tekst/ (pdftotext -layout).

Draaien (vanuit de map eindexamen-oefenen):
    python3 tools/haal_op.py                                   alle wiskundevakken, alle niveaus
    python3 tools/haal_op.py natuurkunde scheikunde --niveau havo vwo

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
    vakpatroon = '|'.join(args or ['wiskunde'])
    lijst_pad = HIER / 'documenten.json'
    lijst = json.loads(lijst_pad.read_text()) if lijst_pad.exists() else []
    gezien = {d['code'] for d in lijst}
    for jaar in JAREN:
        for niveau in niveaus:
            html = haal(f'{BASIS}/{jaar}/{niveau}/vakken/exacte-vakken')
            vakken = sorted(set(re.findall(rf'/{jaar}/{niveau}/vakken/exacte-vakken/((?:{vakpatroon})[a-z0-9-]*)', html)))
            for vak in vakken:
                vhtml = haal(f'{BASIS}/{jaar}/{niveau}/vakken/exacte-vakken/{vak}')
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
                    lijst.append({'code': code, 'jaar': jaar, 'niveau': niveau, 'vak': vak, 'tijdvak': int(tijdvak[-1]),
                                  'soort': soort(code), 'url': echt, 'pdf': str(pdf.relative_to(HIER)), 'tekst': str(txt.relative_to(HIER))})
                    gezien.add(code)
                    print(f'{jaar} {niveau:8} {vak:22} {code}', flush=True)
                    time.sleep(0.4)
            lijst.sort(key=lambda d: (d['niveau'], d['vak'], d['jaar'], d['tijdvak'], d['code']))
            lijst_pad.write_text(json.dumps(lijst, ensure_ascii=False, indent=1))  # tussentijds opslaan
    print(f'\n{len(lijst)} documenten in documenten.json')


if __name__ == '__main__':
    main()
