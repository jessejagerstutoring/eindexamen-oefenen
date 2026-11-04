"""
Snijdt elke examenvraag uit de originele pdf's, zodat de site de vraag precies zo toont als in het examen.

Per opgave wordt de tekst opgedeeld in stukken: stuk k loopt van het einde van vraag k-1 (of de titel
van de opgave) tot en met vraag k. Zo bevat stuk k de inleiding, figuren en tabellen die bij vraag k
horen. Uit het correctievoorschrift komt per vraag het antwoordmodel als apart beeld.

Draaien (vanuit de map eindexamen-oefenen, met een Python waarin Pillow zit):
    python3 tools/snij.py [vakcode ...]          bijv. python3 tools/snij.py wiskunde-a-havo

Uitvoer:
    docs/img/<examencode>/s<nr>.webp     stuk van de opgaven dat eindigt met vraag <nr>
    docs/img/<examencode>/a<nr>.webp     antwoordmodel van vraag <nr>
    bronnen/snij.json                    per vraag de beelden, hoogtes en eventuele meldingen
"""
import html as htmllib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).parent.parent
BRON = ROOT / 'bronnen'
UIT = ROOT / 'docs' / 'img'
DPI = 144                      # 2 px per pt: scherp op een telefoon en niet te zwaar
SCH = DPI / 72
VAKKEN = ['wiskunde-a-havo', 'wiskunde-b-havo', 'wiskunde-a-vwo', 'wiskunde-b-vwo', 'wiskunde-c-vwo']


def regels(pdf):
    """[(pagina, breedte, hoogte, [(x0, y0, x1, y1, tekst)])] uit pdftotext -bbox-layout."""
    html = subprocess.run(['pdftotext', '-bbox-layout', str(pdf), '-'], capture_output=True, text=True).stdout
    uit = []
    for i, pg in enumerate(re.findall(r'<page width="([\d.]+)" height="([\d.]+)">(.*?)</page>', html, re.S)):
        lijst = []
        for m in re.finditer(r'<line xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</line>', pg[2], re.S):
            tekst = htmllib.unescape(' '.join(re.findall(r'>([^<]*)</word>', m.group(5)))).strip()
            lijst.append((float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4)), tekst))
        lijst.sort(key=lambda r: (round(r[1]), r[0]))
        uit.append((i + 1, float(pg[0]), float(pg[1]), lijst))
    return uit


def voet(pagina):
    """y waar de voettekst begint (code, paginanummer, 'lees verder')."""
    _, _, h, lijst = pagina
    ys = [r[1] for r in lijst if r[1] > h - 90 and re.search(r'[A-Z]{2}-\d{4}-[a-z]-\d\d|lees verder|►|^\d+ / \d+$|einde', r[4], re.I)]
    return min(ys) - 6 if ys else h - 55


def norm(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())


def vragen_opgaven(pags):
    """{nr: (pagina, y_boven, y_onder)} van elke vraag in de opgaven."""
    uit = {}
    for p, _, h, lijst in pags:
        for r in lijst:
            if re.fullmatch(r'\d{1,2}p', r[4]) and r[0] < 90:
                nr = [s for s in lijst if re.fullmatch(r'\d{1,2}', s[4]) and r[2] < s[0] + 20 and s[0] > r[0] and s[0] < 110 and abs(s[1] - r[1]) < 6]
                if not nr:
                    continue
                n = int(nr[0][4])
                # de vraagtekst: regels rechts van het nummer die zonder witregel op elkaar volgen
                tekst = [s for s in lijst if s[0] >= 95 and s[1] < r[3] + 2 and s[3] > r[1] - 2]
                if not tekst:
                    continue
                onder, x = max(s[3] for s in tekst), min(s[0] for s in tekst)
                verder = True
                while verder:
                    verder = False
                    for s in lijst:
                        if abs(s[0] - x) < 4 and onder - 1 < s[1] < onder + 6 and s[3] > onder:
                            onder, verder = s[3], True
                if n not in uit:
                    uit[n] = (p, min(r[1], min(s[1] for s in tekst)), onder)
    # een vraag loopt nooit door tot voorbij het begin van de volgende vraag op dezelfde pagina
    for n, (p, y0, y1) in list(uit.items()):
        na = [b[1] for m, b in uit.items() if m > n and b[0] == p and b[1] > y0]
        if na and y1 > min(na) - 2:
            uit[n] = (p, y0, min(na) - 4)
    return uit


def zoek_titel(pags, titel, na):
    """(pagina, y) van de titel van een opgave, op of na positie na=(pagina, y)."""
    doel = norm(titel)[:18]
    if len(doel) < 3:
        return None
    for p, _, _, lijst in pags:
        if p < na[0]:
            continue
        for r in lijst:
            if (p, r[1]) <= na:
                continue
            # de titel staat op een eigen, korte regel (soms iets verder ingesprongen)
            n = norm(r[4])
            if r[0] < 110 and n and (n.startswith(doel) and len(n) <= len(norm(titel)) + 3 or doel.startswith(n) and len(n) >= 6):
                return (p, r[1] - 4)
    return None


def einde_na(pags, p, y1):
    """Onderkant van het stuk met een vraag: tot de eerstvolgende tekst in de linkerkolom, zodat een
    figuur naast de vraag die lager doorloopt er helemaal bij komt."""
    pag = pags[p - 1]
    grens = voet(pag)
    volgende = [r[1] for r in pag[3] if r[1] > y1 + 2 and r[1] < grens and (r[0] < 300 or re.match(r'(figuur|tabel|foto)\s*\d', r[4], re.I))]
    return min(volgende) - 4 if volgende else grens


def stukken(pags, van, tot, boven=34):
    """Stukjes (pagina, y0, y1) van positie van=(p, y) tot tot=(p, y), over pagina's heen."""
    (pa, ya), (pb, yb) = van, tot
    uit = []
    for p in range(pa, pb + 1):
        pag = pags[p - 1]
        y0 = ya if p == pa else boven
        y1 = yb if p == pb else voet(pag)
        inhoud = [r for r in pag[3] if y0 <= r[1] < y1 and not re.search(r'ga verder op de volgende pagina', r[4], re.I)]
        if p != pa and p != pb and not inhoud:
            continue
        if y1 - y0 > 8:
            uit.append((p, y0, y1))
    return uit


class Beelden:
    """Rendert pagina's één keer en snijdt daar stukken uit."""

    def __init__(self, pdf, tmp):
        self.pdf, self.tmp, self.cache = pdf, tmp, {}

    def pagina(self, p):
        if p not in self.cache:
            uit = Path(self.tmp) / f'{self.pdf.stem}-{p}'
            subprocess.run(['pdftoppm', '-r', str(DPI), '-f', str(p), '-l', str(p), '-gray', '-png', '-singlefile', str(self.pdf), str(uit)], check=True)
            self.cache = {p: Image.open(f'{uit}.png').convert('L')}  # alleen de laatste pagina bewaren
        return self.cache[p]

    def snij(self, delen, links, rechts, pad):
        stukjes = []
        for p, y0, y1 in delen:
            img = self.pagina(p)
            st = img.crop((int(links * SCH), int(y0 * SCH), int(rechts * SCH), int(y1 * SCH)))
            st = bijsnijden(st)
            if st is not None:
                stukjes.append(st)
        if not stukjes:
            return None
        w = max(s.width for s in stukjes)
        h = sum(s.height for s in stukjes) + 28 * (len(stukjes) - 1)
        doek = Image.new('L', (w, h), 255)
        y = 0
        for s in stukjes:
            doek.paste(s, (0, y))
            y += s.height + 28
        pad.parent.mkdir(parents=True, exist_ok=True)
        doek.save(pad, 'WEBP', quality=72, method=6)
        return [doek.width, doek.height]


def bijsnijden(img, marge=10):
    """Witte randen boven en onder weghalen; lange witte stukken inkorten tot 40 px."""
    px = img.load()
    w, h = img.size
    stap = max(1, w // 400)
    leeg = [all(px[x, y] > 245 for x in range(0, w, stap)) for y in range(h)]
    if all(leeg):
        return None
    boven = leeg.index(False)
    onder = h - leeg[::-1].index(False)
    rijen, wit = [], 0
    for y in range(max(0, boven - marge), min(h, onder + marge)):
        wit = wit + 1 if leeg[y] else 0
        if wit <= 40:
            rijen.append(y)
    if len(rijen) == onder - boven + 2 * marge or len(rijen) == len(range(max(0, boven - marge), min(h, onder + marge))):
        return img.crop((0, max(0, boven - marge), w, min(h, onder + marge)))
    uit = Image.new('L', (w, len(rijen)), 255)
    for i, y in enumerate(rijen):
        uit.paste(img.crop((0, y, w, y + 1)), (0, i))
    return uit


def antwoorden(pags):
    """{nr: (start=(p, y), eind=(p, y))} voor elk antwoordmodel in het correctievoorschrift."""
    starts, titels, stop = [], [], None
    for p, _, _, lijst in pags:
        for r in lijst:
            if 'maximumscore' in r[4].lower() or re.fullmatch(r'[A-F]', r[4]):
                nr = [s for s in lijst if re.fullmatch(r'\d{1,2}', s[4]) and s[0] < 100 and abs(s[1] - r[1]) < 5 and s[2] <= r[0] + 2]
                if nr and r[0] < 140:
                    starts.append((int(nr[0][4]), (p, min(r[1], nr[0][1]) - 4)))
            if stop is None and starts and re.match(r'^\d?\s*(Aanleveren|Inzenden|Bronvermelding)', r[4]):
                stop = (p, r[1] - 4)
    # alleen een oplopende reeks 1, 2, 3, ... (de algemene regels bevatten soms ook getallen)
    reeks, verwacht = [], 1
    for n, pos in sorted(starts, key=lambda s: s[1]):
        if n == verwacht:
            reeks.append((n, pos))
            verwacht += 1
    uit = {}
    for i, (n, pos) in enumerate(reeks):
        eind = reeks[i + 1][1] if i + 1 < len(reeks) else (stop or (pos[0], 9999))
        uit[n] = (pos, eind)
    return uit


def titel_boven(pags, pos, eind, titels):
    """Kapt een antwoordstuk af boven de titel van de volgende opgave."""
    for p, _, _, lijst in pags:
        if not (pos[0] <= p <= eind[0]):
            continue
        for r in lijst:
            if pos < (p, r[1]) < eind and r[0] < 110 and norm(r[4]) in titels:
                return (p, r[1] - 4)
    return eind


def main():
    vakken = [a for a in sys.argv[1:] if a.startswith('wiskunde')] or VAKKEN
    alleen = [a for a in sys.argv[1:] if not a.startswith('wiskunde')]  # losse examencodes, om te testen
    docs = json.loads((BRON / 'documenten.json').read_text())
    bank = json.loads((BRON / 'databank.json').read_text())
    uitvoer_pad = BRON / 'snij.json'
    resultaat = json.loads(uitvoer_pad.read_text()) if uitvoer_pad.exists() else {}
    per = {}
    for d in docs:
        if d['vak'] in vakken and d['soort'] in ('opgaven', 'correctievoorschrift'):
            per.setdefault(re.sub(r'-[oc]$', '', d['code']), {})[d['soort']] = d
    with tempfile.TemporaryDirectory() as tmp:
        for code, ex in sorted(per.items()):
            vragen = [v for v in bank if v['id'].startswith(code + ':')]
            if not vragen or 'opgaven' not in ex or (alleen and code not in alleen):
                continue
            meld = []
            # ---------- opgaven ----------
            pdf = BRON / ex['opgaven']['pdf']
            pags = regels(pdf)
            breedte = pags[0][1]
            pos = vragen_opgaven(pags)
            beeld = Beelden(pdf, tmp)
            vorige_titel, vorige_eind, laatste = None, None, (1, 0)
            for v in vragen:
                n = v['vraag']
                if n not in pos:
                    meld.append(f'vraag {n} niet gevonden in de opgaven')
                    continue
                p, y0, y1 = pos[n]
                nieuw = v['opgave'] != vorige_titel
                if nieuw:
                    t = zoek_titel(pags, v['opgave'], laatste)
                    if t and t <= (p, y0):
                        begin = t
                    else:
                        meld.append(f'titel van opgave "{v["opgave"]}" niet gevonden (vraag {n})')
                        begin = vorige_eind or (p, 34)
                else:
                    begin = vorige_eind
                eind = (p, einde_na(pags, p, y1))
                delen = stukken(pags, begin, eind)
                maat = beeld.snij(delen, 40, breedte - 30, UIT / code / f's{n}.webp')
                resultaat.setdefault(code, {})[str(n)] = {'stuk': f'img/{code}/s{n}.webp', 'maat': maat, 'nieuweOpgave': nieuw}
                # een figuurlabel naast de laatste regel van de vraag hoort bij het volgende stuk
                labels = [r[1] for r in pags[p - 1][3] if y0 < r[1] < eind[1] and r[0] >= 300 and re.match(r'(figuur|tabel|foto)\s*\d', r[4], re.I)]
                vorige_titel, vorige_eind, laatste = v['opgave'], (p, min([eind[1]] + labels) - 4), (p, y1)
            # ---------- correctievoorschrift ----------
            if 'correctievoorschrift' in ex:
                pdf = BRON / ex['correctievoorschrift']['pdf']
                cpags = regels(pdf)
                ab = antwoorden(cpags)
                titels = {norm(v['opgave']) for v in vragen if v['opgave']}
                cbeeld = Beelden(pdf, tmp)
                for v in vragen:
                    n = v['vraag']
                    if n not in ab:
                        meld.append(f'antwoord {n} niet gevonden')
                        continue
                    start, eind = ab[n]
                    eind = titel_boven(cpags, start, eind, titels)
                    if eind[1] == 9999:
                        eind = (start[0], voet(cpags[start[0] - 1]))
                    delen = stukken(cpags, start, eind, boven=64)
                    maat = cbeeld.snij(delen, 40, cpags[0][1] - 30, UIT / code / f'a{n}.webp')
                    resultaat.setdefault(code, {}).setdefault(str(n), {}).update({'antwoord': f'img/{code}/a{n}.webp', 'antwoordMaat': maat})
            resultaat.setdefault(code, {})['_meldingen'] = meld
            print(code, len(vragen), 'vragen', ('· ' + '; '.join(meld)) if meld else '', flush=True)
            uitvoer_pad.write_text(json.dumps(resultaat, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
