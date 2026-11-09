"""
Maakt per vak een oefenboek op A5 (pdf), zoals een examenbundel:

    voorwerk      titelpagina, colofon, inhoud, uitleg, het examen en je cijfer, tips, formulekaart (als het vak er een heeft)
    deel 1        alle opgaven uit eerdere examens, per domein en onderwerp van de syllabus
    deel 2        een paar complete, recente examens
    uitwerkingen  het correctievoorschrift van het CvTE bij elke vraag, met aanvullingen en errata
    nawerk        overzicht per examen, bronvermelding

De vragen, figuren en antwoorden komen als vectoruitsnede rechtstreeks uit de originele pdf's van
examenblad.nl (scherp in print, precies zoals in het examen). De snijlijnen per vraag zijn dezelfde als
voor de site (tools/snij.py, functie posities). Alles eromheen zetten we zelf met LuaLaTeX.

Draaien (vanuit de map eindexamen-oefenen, met de Python waarin Pillow, numpy en pikepdf zitten):
    python tools/bouw_bundel.py natuurkunde-havo          # bouwt het boek (elk vak uit bouw_site.VAKKEN kan)
    python tools/bouw_bundel.py natuurkunde-havo --opnieuw  # examenkeuze opnieuw bepalen vanaf alle examens
    python tools/bouw_bundel.py --proef [vak ...]          # droogtest zonder LaTeX, standaard voor alle vakken
    python tools/bouw_bundel.py --publiceer                # alle bundels naar docs/bundels/ en docs/data/bundels.json (site)

Instellingen: STANDAARD < FAMILIES[<familie>] < BOEKEN[<vak>]. Per familie horen er bij (optioneel)
tools/bundel/tips-<familie>.tex en tools/bundel/omslag/<familie>.tex; anders de algemene versies.

Uitvoer: bundels/<vak>.pdf; de LaTeX-bron en tussenbestanden staan in bundels/bouw/<vak>/. Na elke bouw
staat daar controle.txt (wat een mens moet nakijken) en controle/vel-NN.png (alle pagina's in het klein).
Nodig: LuaLaTeX (TinyTeX) met o.a. tikz, fancyhdr, titlesec, sourceserif en sourcesans; poppler (pdftotext, pdftoppm).
"""
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter, OrderedDict
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import snij  # noqa: E402
from bouw_site import VAKKEN  # noqa: E402

ROOT = Path(__file__).parent.parent
BRON = ROOT / 'bronnen'
UIT = ROOT / 'bundels'

# ---------- instellingen per boek ----------
# Instellingen: STANDAARD, dan per vakfamilie (wiskunde, natuurkunde, ...), dan per boek. Een vak dat nergens
# genoemd wordt, krijgt gewoon de standaard; zo kan elk vak uit bouw_site.VAKKEN gebouwd worden.
STANDAARD = {
    'examens_deel2': 3,           # zoveel recente examens komen compleet in deel 2
    'max_paginas': 280,
    'hulpmiddelen': 'Rekenmachine.',
    'duur': None,                 # None: uit de voorpagina's van de examens ('13.30 - 16.30 uur')
    'tips': None,                 # None: tools/bundel/tips-<familie>.tex, anders tips-algemeen.tex
    'formulekaart': 'auto',       # 'auto': opnemen als het examen een pagina 'Formules' heeft
    'vakwoord': 'inhoudelijk',    # '... is ook goed als die <vakwoord> klopt'
    'nterm': '$N$ verschilt per examen en ligt meestal rond de 1',
    'omslag': None,               # None: tools/bundel/omslag/<familie>.tex, anders algemeen.tex
}
FAMILIES = {
    'wiskunde': {
        'hulpmiddelen': 'Grafische rekenmachine (in examenstand), passer en geodriehoek.',
        'vakwoord': 'wiskundig',
        'nterm': 'bij wiskunde ligt $N$ meestal rond de 1',
    },
    'natuurkunde': {
        'hulpmiddelen': 'Rekenmachine (grafisch, in examenstand), geodriehoek en een informatieboek: Binas of ScienceData.',
        'formulekaart': False,
        'vakwoord': 'natuurkundig',
    },
    'scheikunde': {
        'hulpmiddelen': 'Rekenmachine en een informatieboek: Binas of ScienceData.',
        'formulekaart': False,
        'vakwoord': 'scheikundig',
    },
    'biologie': {
        'hulpmiddelen': 'Rekenmachine en een informatieboek: Binas of ScienceData.',
        'formulekaart': False,
        'vakwoord': 'biologisch',
    },
}
BOEKEN = {
    'wiskunde-a-havo': {
        'hulpmiddelen': 'Grafische rekenmachine (in examenstand), geodriehoek en het formuleblad voorin het examen.',
        'tips': 'wiskunde-a',
    },
    'wiskunde-a-vwo': {
        'hulpmiddelen': 'Grafische rekenmachine (in examenstand), geodriehoek en het formuleoverzicht voorin het examen.',
        'tips': 'wiskunde-ac-vwo',
    },
    'wiskunde-c-vwo': {
        'hulpmiddelen': 'Grafische rekenmachine (in examenstand) en geodriehoek.',
        'tips': 'wiskunde-ac-vwo',
    },
    'wiskunde-b-havo': {
        'hulpmiddelen': 'Grafische rekenmachine (in examenstand), passer en geodriehoek.',
    },
    'wiskunde-b-vwo': {
        'hulpmiddelen': 'Grafische rekenmachine (in examenstand), passer, geodriehoek en de formules voorin het examen.',
    },
}


def familie(vak):
    """'wiskunde-b-vwo' -> 'wiskunde', 'natuurkunde-havo' -> 'natuurkunde'."""
    return vak.split('-')[0]


def instellingen(vak):
    cfg = {**STANDAARD, **FAMILIES.get(familie(vak), {}), **BOEKEN.get(vak, {})}
    if not cfg['tips']:
        f = familie(vak)
        cfg['tips'] = f if (Path(__file__).parent / 'bundel' / f'tips-{f}.tex').exists() else 'algemeen'
    return cfg


def examenduur(examens):
    """Meest voorkomende duur volgens de voorpagina's, bv. '3 uur' of '2,5 uur'."""
    tel = Counter()
    for ex in examens.values():
        t = subprocess.run(['pdftotext', '-l', '1', str(BRON / ex['opgaven']['pdf']), '-'],
                           capture_output=True, text=True).stdout
        m = re.search(r'(\d{1,2})[.:](\d\d)\s*[-–]+\s*(\d{1,2})[.:](\d\d)\s*uur', t)
        if m:
            a, b, c, d = map(int, m.groups())
            tel[(c * 60 + d) - (a * 60 + b)] += 1
    if not tel:
        return '3 uur'
    minuten = tel.most_common(1)[0][0]
    uren = minuten / 60
    return f'{uren:g} uur'.replace('.', ',')


SAMENSTELLER = 'Eindexamen Oefenen'
WEBADRES = 'jessejagerstutoring.github.io/eindexamen-oefenen'   # waar de site staat (en waar je fouten meldt)

# ---------- maten (in bp, 1/72 inch) ----------
MM = 72 / 25.4
PAPIER_B, PAPIER_H = 148 * MM, 210 * MM
BINNEN, BUITEN, BOVEN, ONDER = 13.5 * MM, 10.5 * MM, 17 * MM, 17 * MM
TEKSTB = PAPIER_B - BINNEN - BUITEN            # ca. 351 bp
TEKSTH = PAPIER_H - BOVEN - ONDER              # ca. 499 bp
FIG_ANTW = 0.85       # schaal van grafieken in de uitwerkingen t.o.v. de gewone tekst
PAS_ANTW, PAS_VRAAG = 0.7, 0.85   # zover mag een figuur extra krimpen om nog op de pagina te passen
LINKS = 100.0          # linkerkant van de uitsnede: rechts van punten en vraagnummers
RECHTS = 520.0         # rechterkant als er niets verder uitsteekt
SCHAAL = TEKSTB / (RECHTS - LINKS)             # 12 pt Arial wordt zo ca. 10 pt
DPI = 144
PX = DPI / 72
INKT = 236             # grijswaarde waaronder een pixel als inkt telt
ROMEINS = {1: 'I', 2: 'II', 3: 'III'}


def esc(s):
    """Tekst veilig in LaTeX."""
    rep = {'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#', '_': r'\_',
           '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}',
           # super- en subscripten die Source Serif niet heeft (bijv. [H⁺] in een onderwerpbeschrijving)
           '⁺': r'\textsuperscript{+}', '⁻': r'\textsuperscript{\textminus}', '⁰': r'\textsuperscript{0}',
           '⁴': r'\textsuperscript{4}', '⁵': r'\textsuperscript{5}', '⁶': r'\textsuperscript{6}',
           '⁷': r'\textsuperscript{7}', '⁸': r'\textsuperscript{8}', '⁹': r'\textsuperscript{9}',
           '₀': r'\textsubscript{0}', '₁': r'\textsubscript{1}', '₂': r'\textsubscript{2}', '₃': r'\textsubscript{3}',
           '₄': r'\textsubscript{4}', '₅': r'\textsubscript{5}', '₆': r'\textsubscript{6}'}
    return ''.join(rep.get(c, c) for c in s)


def examen_sleutel(code):
    m = re.search(r'-(\d\d)-(\d)$', code)
    return (2000 + int(m.group(1)), int(m.group(2)))


def examen_naam(code, kort=False):
    jaar, tv = examen_sleutel(code)
    return f'{jaar}-{ROMEINS[tv]}' if kort else f'{jaar} tijdvak {tv}'


# ---------- pagina's bekijken: tekstregels en inkt ----------
class Pdf:
    """Eén originele pdf: tekstregels (pdftotext) en gerenderde pagina's (pdftoppm), met cache."""

    def __init__(self, pad, tmp):
        self.pad, self.tmp = Path(pad), tmp
        self.pags = snij.regels(self.pad)
        self.cache = OrderedDict()

    def maat(self, p):
        return self.pags[p - 1][1], self.pags[p - 1][2]

    def lijnen(self, p):
        return self.pags[p - 1][3]

    def beeld(self, p):
        if p not in self.cache:
            uit = Path(self.tmp) / f'{self.pad.stem}-{p}'
            subprocess.run(['pdftoppm', '-r', str(DPI), '-f', str(p), '-l', str(p), '-gray', '-png', '-singlefile',
                            str(self.pad), str(uit)], check=True)
            img = np.asarray(Image.open(f'{uit}.png').convert('L'))
            # inkt die niet onder een tekstregel valt, is tekening (figuur, breukstreep, lijn)
            tekst = np.zeros(img.shape, bool)
            for x0, y0, x1, y1, t in self.lijnen(p):
                if len(t.replace(' ', '')) <= 3:
                    continue          # losse letters in een figuur (x, y, O, P) horen bij de tekening
                tekst[max(0, int((y0 - 1) * PX)):int((y1 + 1) * PX) + 1, max(0, int((x0 - 1) * PX)):int((x1 + 1) * PX) + 1] = True
            inkt = img < INKT
            self.cache[p] = (inkt, inkt & ~tekst)
            if len(self.cache) > 3:
                self.cache.popitem(last=False)
        return self.cache[p]


TROEP = re.compile(r'^(ga verder op de volgende pagina|lees verder|let op: de laatste vra|vergeet niet deze uitwerkbijlage)', re.I)


SCHRIJFREGEL = re.compile(r'(?:[A-Za-z]+\s?:\s*)?[.…_\s]{8,}')


def blokken(pdf, p, y0, y1, links=LINKS, soort='o'):
    """Deelt het stuk (p, y0..y1) van een pagina op in blokken die niet over een pagina mogen breken.

    Tussen twee blokken mag het boek een nieuwe pagina beginnen: alleen op een witte strook tussen
    gewone tekstregels, nooit midden in een figuur. Geeft [{'a', 'b', 'gat', 'r'}] in pt van het origineel
    (a/b = boven/onder, gat = witruimte erboven, r = rechterkant van de inkt)."""
    breedte, hoogte = pdf.maat(p)
    lijnen = pdf.lijnen(p)
    binnen = sorted([r for r in lijnen if r[3] > y0 + 1 and r[1] < y1 - 1], key=lambda r: r[1])
    # titel van een opgave (staat links van de uitsnede) en kopregel van het correctievoorschrift weglaten
    if soort == 'o':
        while binnen and binnen[0][0] < links - 5 and not re.fullmatch(r'\d{1,2}p?', binnen[0][4]):
            y0 = max(y0, binnen[0][3] + 1.5)
            binnen = [r for r in binnen if r[1] > y0 - 1]
    if soort == 'c':
        kop = [r for r in binnen if r[4] in ('Vraag', 'Antwoord', 'Scores') and r[1] < y0 + 45]
        if kop:
            y0 = max(y0, max(r[3] for r in kop) + 2)
    for r in binnen:
        if TROEP.match(r[4]):
            if r[1] - y0 < 25:
                y0 = max(y0, r[3] + 1)
            else:
                y1 = min(y1, r[1] - 1)
    inkt, teken = pdf.beeld(p)
    rij0, rij1 = max(0, int(y0 * PX)), min(inkt.shape[0], int(y1 * PX))
    k0, k1 = int(links * PX), int((breedte - 18) * PX)
    if rij1 <= rij0:
        return []
    vlak, tvlak = inkt[rij0:rij1, k0:k1], teken[rij0:rij1, k0:k1]
    if soort == 'u':
        # schrijfregels ('Antwoord: ......', '..........') op de uitwerkbijlage weglaten: in het boek schrijf
        # je op een los vel. Alleen als er naast de regel niets anders staat, zodat figuren heel blijven.
        vlak, tvlak = vlak.copy(), tvlak.copy()
        for r in binnen:
            if not SCHRIJFREGEL.fullmatch(r[4].strip()):
                continue
            a_, b_ = max(0, int((r[1] - 1.5) * PX) - rij0), min(vlak.shape[0], int((r[3] + 1.5) * PX) - rij0 + 1)
            c_, d_ = max(0, int((r[0] - 2) * PX) - k0), max(0, int((r[2] + 2) * PX) - k0)
            if a_ >= b_:
                continue
            band = vlak[a_:b_]
            if band[:, :c_].any() or band[:, d_:].any():
                continue
            vlak[a_:b_] = False
            tvlak[a_:b_] = False
    heeft, tekening = vlak.any(axis=1), tvlak.any(axis=1)
    rijen = np.nonzero(heeft)[0]
    if not len(rijen):
        return []
    # stroken met inkt
    stroken, start = [], rijen[0]
    for i in range(1, len(rijen)):
        if rijen[i] != rijen[i - 1] + 1:
            stroken.append([start, rijen[i - 1]])
            start = rijen[i]
    stroken.append([start, rijen[-1]])
    # een dunne lijn bovenaan (de streep onder de titel van een opgave) hoort er niet bij
    def streep(st):
        rij = vlak[st[0]:st[1] + 1]
        return (st[1] - st[0] < 8 * PX and tekening[st[0]:st[1] + 1].all()
                and rij.any(axis=0).sum() > 0.6 * rij.shape[1])
    while len(stroken) > 1 and streep(stroken[0]):
        stroken.pop(0)
    while len(stroken) > 1 and streep(stroken[-1]):
        stroken.pop()
    # samenvoegen waar je niet mag breken: boven of onder het witte gat zit een tekening
    uit = []
    for s in stroken:
        if uit:
            vorige = uit[-1]
            gat = s[0] - vorige['b'] - 1
            # een dunne strook (vectorpijltjes, accenten boven een regel) hoort bij de regel eronder
            dun = vorige['b'] - vorige['a'] < 5 * PX or s[1] - s[0] < 2.5 * PX
            breekbaar = not tekening[vorige['b']] and not tekening[s[0]] and gat >= 1.5 * PX and not dun
            if soort == 'f':
                # formuleblad: breukstrepen en symbolen tellen als tekening, maar het zijn geen figuren
                breekbaar = gat >= 4 * PX and not dun
            if not breekbaar:
                vorige['b'] = s[1]
                continue
            uit.append({'a': s[0], 'b': s[1], 'gat': gat})
        else:
            uit.append({'a': s[0], 'b': s[1], 'gat': 0})
    res = []
    for blok in uit:
        kolommen = np.nonzero(vlak[blok['a']:blok['b'] + 1].any(axis=0))[0]
        a, b = (rij0 + blok['a']) / PX - 1.2, (rij0 + blok['b'] + 1) / PX + 1.2
        regels_hier = [r[4] for r in binnen if a <= (r[1] + r[3]) / 2 <= b and r[0] >= links - 2]
        # een onderschrift ('figuur 2', 'tabel') in dit blok hoort bij wat eronder staat
        # (pdftotext plakt een onderschrift soms achter de tekstregel ernaast: '... weergegeven. figuur 1')
        vast = any(re.fullmatch(r'(figuur|tabel|foto|grafiek|afbeelding|kaart)\b.{0,25}|maximumscore \d+', t.strip(), re.I)
                   or re.search(r'\s(figuur|tabel|foto|grafiek)( \d+)?$', t.strip(), re.I)
                   for t in regels_hier)
        vast = vast and b - a < 30      # alleen een losse regel; een groot blok mag gewoon breken
        # aandeel tekening (lijnen, foto's) in de inkt: hoog bij een grafiek, laag bij tekst, formules en tabellen
        stuk = vlak[blok['a']:blok['b'] + 1]
        fig = float(tvlak[blok['a']:blok['b'] + 1].sum()) / max(1, int(stuk.sum()))
        res.append({'a': a, 'b': b, 'gat': blok['gat'] / PX, 'r': (k0 + kolommen[-1] + 1) / PX, 'vast': vast,
                    'fig': fig})
    return res


# ---------- LaTeX-stukjes ----------
def blok_tex(pdfpad, p, blok, links, gat, straf, labels='', passend=False, maxschaal=SCHAAL, maxh=TEKSTH - 14,
             meld=False, pas=None, inspring=0.0):
    """Eén blok als uitsnede. gat en straf: witruimte en breekstraf erboven.

    Elke pagina van een origineel komt maar één keer in de pdf (\\DefPag); een blok toont er een
    geknipt stuk van. Alle maten gaan al geschaald (in bp) naar LaTeX."""
    breedte, hoogte = PDFS_MAAT[pdfpad][p]
    naam = PAGINAS.setdefault((pdfpad, p), f'p{len(PAGINAS) + 1}')
    rechts = max(RECHTS if not passend else links, blok['r'] + 2)
    w, h = rechts - links, blok['b'] - blok['a']
    s = min(maxschaal, TEKSTB / w, maxh / h)
    if meld and s < 0.9 * maxschaal and blok.get('fig', 0) < 0.6:
        MELDINGEN.append(f'tekst verkleind tot ca. {12 * s:.1f} pt: {Path(pdfpad).name} blz. {p}, y {blok["a"]:.0f}')
    geo = '/'.join(f'{x * s:.2f}' for x in (links, blok['a'], w, h, breedte, hoogte, inspring))
    if pas:
        return f'\\BlokPas{{{gat:.1f}}}{{{straf}}}{{{naam}}}{{{geo}}}{{{labels}}}{{{pas}}}\n', s
    return f'\\Blok{{{gat:.1f}}}{{{straf}}}{{{naam}}}{{{geo}}}{{{labels}}}\n', s


AFGESNEDEN = []              # uitsneden waar inkt net buiten de snijlijn valt (voor het controleverslag)
LABEL = re.compile(r'^(\d{1,2}p?|\d{1,2}p\s+\d{1,2}|[A-F]|\d{1,2}\s*[a-f]?)$')


def linkse_inkt(pdf, p, blok, links, tot=20):
    """Masker van de inkt links van de snijlijn in de rijen van dit blok, zonder de labels in de kantlijn
    (punten, vraagnummer, meerkeuzeletter). Geeft (strook, k0)."""
    inkt, _ = pdf.beeld(p)
    a, b = int(blok['a'] * PX), int(blok['b'] * PX)
    k0, k1 = max(0, int(tot * PX)), int((links - 0.5) * PX)
    strook = inkt[a:b, k0:k1].copy()
    for x0, y0, x1, y1, t in pdf.lijnen(p):
        if x0 < links and LABEL.match(t.strip()):
            strook[max(0, int((y0 - 1) * PX) - a):max(0, int((y1 + 1) * PX) - a),
                   max(0, int((x0 - 1) * PX) - k0):max(0, int((x1 + 1) * PX) - k0)] = False
    return strook, k0


def blok_links(pdf, p, blok, links):
    """Snijlijn links voor dit blok: de vaste lijn, of verder naar links als een figuur, tabel of foto daar
    overheen loopt (anders valt er een stuk weg)."""
    if blok['b'] - blok['a'] < 2:
        return links
    strook, k0 = linkse_inkt(pdf, p, blok, links)
    if strook.shape[1] < 4 or int(strook[:, -int(3 * PX):].sum()) <= 6:
        return links
    # het aaneengesloten stuk inkt vanaf de snijlijn naar links volgen (kolommen met inkt, kleine gaten mag)
    kol = strook.any(axis=0)
    x, gat = len(kol) - 1, 0
    links_x = x
    while x >= 0:
        if kol[x]:
            links_x, gat = x, 0
        else:
            gat += 1
            if gat > 6 * PX:        # 6 pt wit: daar houdt het op
                break
        x -= 1
    return min(links, (k0 + links_x) / PX - 2)


DOORLOPEND = set()          # (document, pagina, y) waar twee stukken naadloos op elkaar aansluiten


def loopt_door(pdf, p, y, links=LINKS):
    """Loopt er een tekening (figuur naast de tekst) door over de grens y tussen twee stukken?"""
    _, teken = pdf.beeld(p)
    r0, r1 = int((y - 1.5) * PX), int((y + 1.5) * PX)
    if r0 < 0 or r1 >= teken.shape[0]:
        return False
    k0 = int(links * PX)
    # een schuine lijn verschuift een paar pixels tussen de twee rijen: daarom met wat speling
    onder = teken[r1, k0:]
    breed = onder.copy()
    for d in range(1, int(3 * PX) + 1):
        breed[d:] |= onder[:-d]
        breed[:-d] |= onder[d:]
    return int((teken[r0, k0:] & breed).sum()) > 3


def blok_rekken(pdf, p, blok, lb_x, links, y0, y1):
    """Na het verbreden naar links: loopt de inkt in de nieuwe strook (bv. een gedraaid aslabel) boven of onder het
    blok door, dan groeit het blok mee, binnen het stuk (y0..y1)."""
    inkt, _ = pdf.beeld(p)
    k0, k1 = int(lb_x * PX), int(links * PX)
    labels = [(x0, a, x1, b) for x0, a, x1, b, t in pdf.lijnen(p) if x0 < links and LABEL.match(t.strip())]

    def rij_inkt(r):
        if r < 0 or r >= inkt.shape[0]:
            return False
        y = r / PX
        rij = inkt[r, k0:k1].copy()
        for x0, a, x1, b in labels:
            if a - 1 <= y <= b + 1:
                rij[max(0, int((x0 - 1) * PX) - k0):max(0, int((x1 + 1) * PX) - k0)] = False
        return rij.any()
    a, b = int(blok['a'] * PX), int(blok['b'] * PX)
    while b / PX < y1 - 1 and rij_inkt(b + 1):
        b += 1
    while a / PX > y0 + 1 and rij_inkt(a - 1):
        a -= 1
    blok['a'], blok['b'] = min(blok['a'], a / PX - 1.2 if a < int(blok['a'] * PX) else blok['a']), \
        max(blok['b'], b / PX + 1.2 if b > int(blok['b'] * PX) else blok['b'])


def snijcontrole(pdf, rel, p, blok, links):
    """Staat er inkt net buiten de uitsnede die erbij hoort? Links: alles tussen de kantlijn met punten en
    vraagnummers en de snijlijn, behalve die labels zelf. Boven en onder: een tekening die over de rand doorloopt."""
    inkt, teken = pdf.beeld(p)
    a, b = int(blok['a'] * PX), int(blok['b'] * PX)
    if b - a < 4:
        return
    strook, _ = linkse_inkt(pdf, p, blok, links)
    rand = strook[:, -int(3 * PX):]
    n = int(rand.sum())
    if n > 6:
        AFGESNEDEN.append(f'{Path(rel).name} blz. {p}, y {blok["a"]:.0f}-{blok["b"]:.0f}: inkt links over de snijlijn ({n} px)')
    br = int((PDFS_MAAT_BREED.get(rel, 595) - 18) * PX)
    for rij, buiten in ((a, a - 2), (b - 1, b + 1)):
        if any(d[0] == rel and d[1] == p and abs(d[2] - rij / PX) < 4 for d in DOORLOPEND):
            continue
        if 0 <= buiten < inkt.shape[0]:
            # met een paar pixels speling, zodat ook een schuine lijn telt
            ander = teken[buiten, int(links * PX):br]
            breed = ander.copy()
            for d in range(1, int(2 * PX) + 1):
                breed[d:] |= ander[:-d]
                breed[:-d] |= ander[d:]
            door = teken[rij, int(links * PX):br] & breed
            if door.sum() > 3:
                AFGESNEDEN.append(f'{Path(rel).name} blz. {p}, y {rij / PX:.0f}: tekening loopt door over de {"bovenrand" if rij == a else "onderrand"}')


PDFS_MAAT_BREED = {}
PDFS_MAAT = {}
MELDINGEN = []               # voor het controleverslag: alles wat een mens even moet nakijken
PAGINAS = OrderedDict()      # (pdf, pagina) -> naam van de opgeslagen pagina


def paginas_tex():
    return ''.join(f'\\DefPag{{{naam}}}{{{pad}}}{{{p}}}\n' for (pad, p), naam in PAGINAS.items())


class Bouwer:
    def __init__(self, vak, tmp, bouwmap):
        self.vak, self.tmp, self.bouwmap = vak, tmp, bouwmap
        self.pdfs = {}
        self.keten = self.keten_eerste = 0.0
        self.begin = {}
        self.vorige = False       # eindigde het laatst geplaatste blok met een onderschrift?

    def pdf(self, rel):
        if rel not in self.pdfs:
            self.pdfs[rel] = Pdf(BRON / rel, self.tmp)
            pad = os.path.relpath(BRON / rel, self.bouwmap)
            PDFS_MAAT[pad] = {i + 1: (w, h) for i, (_, w, h, _) in enumerate(self.pdfs[rel].pags)}
            PDFS_MAAT_BREED[rel] = self.pdfs[rel].pags[0][1]
        return self.pdfs[rel], os.path.relpath(BRON / rel, self.bouwmap)

    def tekstbegin(self, rel, links):
        """Waar de tekstregels in dit document beginnen (rechts van links). Die plek komt in het boek precies op de
        linkermarge, zodat de tekst van alle soorten uitsneden onder de kopjes uitlijnt. Niet de meest voorkomende
        plek (dat kan een opsomming of een tabelkolom zijn), maar de meest linkse plek die vaak voorkomt."""
        sleutel = (rel, links)
        if sleutel not in self.begin:
            pdf, _ = self.pdf(rel)
            tel = Counter(round(r[0]) for p, *_ in pdf.pags for r in pdf.lijnen(p)
                          if links - 1 <= r[0] <= links + 30 and len(r[4].strip()) > 3)
            self.begin[sleutel] = linkse_vaak(tel, links)
        return self.begin[sleutel]

    def meet_tekstbegin(self, rel, links, delen):
        """Zet het tekstbegin van een document vast op basis van alleen de stukken die in het boek komen
        (zo telt bv. de lange lijst algemene regels voorin een correctievoorschrift niet mee)."""
        pdf, _ = self.pdf(rel)
        regels = [r for q, y0, y1 in delen for r in pdf.lijnen(q)
                  if y0 <= r[1] and r[3] <= y1 + 1 and links - 1 <= r[0] <= links + 30 and len(r[4].strip()) > 3]
        # in een correctievoorschrift staat 'maximumscore' op de plek die op de marge hoort (de uitleg eronder
        # springt bij sommige vakken in)
        anker = Counter(round(r[0]) for r in regels if r[4].strip().lower().startswith('maximumscore'))
        if anker:
            self.begin[(rel, links)] = anker.most_common(1)[0][0]
        elif regels:
            self.begin[(rel, links)] = linkse_vaak(Counter(round(r[0]) for r in regels), links)

    def stukken_tex(self, rel, delen, soort, labels=None, links=LINKS, eerste_gat=0, passend=False, eerste_straf=10000):
        """Uitsneden van een reeks stukken (p, y0, y1) onder elkaar.

        labels: [(p, y, tex)] om in de marge te zetten, ter hoogte van y op pagina p."""
        pdf, pad = self.pdf(rel)
        uit, labels = [], list(labels or [])
        # waar de tekst begint: liefst gemeten in deze stukken zelf, anders in het hele document
        tel = Counter(round(r[0]) for q, y0, y1 in delen for r in pdf.lijnen(q)
                      if y0 <= r[1] and r[3] <= y1 + 1 and r[0] >= links - 1 and len(r[4].strip()) > 3)
        begin = self.tekstbegin(rel, links)
        vaak = [x for x, n in tel.items() if n >= 3 and 0 <= x - links <= 30]
        # alleen voor losse stukken (regels, aanvullingen): in een vraag kan een tabel verder links beginnen
        if soort in ('x', 'f') and vaak and min(vaak) < begin - 1:
            begin = min(vaak)         # dit stuk begint duidelijk verder naar links (bv. de nakijkregels)
        inspring = max(0, begin - links)     # in pt van het origineel
        if soort == 'u' and inspring > 12:
            inspring = 0      # op een uitwerkbijlage is dat eerder een ingesprongen opdracht dan de kantlijn
        eerste, vorige = True, self.vorige
        # aan het begin van een opgave (of vraag) blijven de eerste regels bij wat volgt: geen losse
        # inleidingsregel onderaan een pagina met het figuur pas op de volgende
        kop = 0.0 if eerste_straf >= 10000 else None
        keten, in_keten = 0.0, eerste_straf >= 10000   # hoogte van het onbreekbare begin (voor \\Needspace)
        for p, y0, y1 in delen:
            bl = blokken(pdf, p, y0, y1, links, soort)
            for i, blok in enumerate(bl):
                if eerste:
                    gat, straf = eerste_gat, eerste_straf
                elif i == 0:
                    gat, straf = 9, 0               # nieuw stuk of volgende pagina van het origineel
                else:
                    # in de uitwerkingen gaat de witruimte van het origineel ongeveer half mee
                    gat = min(blok['gat'], 16) if soort != 'c' else min(blok['gat'] * 0.5, 6)
                    straf = 0 if blok['gat'] >= 9 else 150
                # een los onderschrift ('figuur 2', 'tabel') blijft bij wat eronder staat
                if vorige or (kop is not None and not eerste and kop < 40):
                    straf = 10000
                hier = [lb for lb in labels if lb[0] == p and blok['a'] - 4 <= lb[1] < blok['b']]
                for lb in hier:
                    labels.remove(lb)
                # de schaal is pas bekend na blok_tex: eerst bepalen, dan de labels erin zetten
                # het eerste blok na een opgavetitel moet samen met die titel op een pagina passen
                maxh = TEKSTH - 14 - (60 if eerste and eerste_straf >= 10000 else 0)
                maxschaal, pas = SCHAAL, None
                if blok.get('fig', 0) > 0.6 and blok['b'] - blok['a'] > 50:
                    # een figuur mag iets krimpen om nog op de pagina te passen (\\BlokPas); in een uitwerking
                    # is hij sowieso wat kleiner
                    pas = PAS_ANTW if soort == 'c' else PAS_VRAAG
                    if soort == 'c':
                        maxschaal, maxh = SCHAAL * FIG_ANTW, min(maxh, 0.5 * TEKSTH)
                lb_x, insp = blok_links(pdf, p, blok, links), inspring
                if lb_x < links:
                    blok_rekken(pdf, p, blok, lb_x, links, y0, y1)
                _, s = blok_tex(pad, p, blok, lb_x, 0, 0, passend=passend, maxh=maxh, maxschaal=maxschaal)
                if lb_x < links:
                    # het blok begint verder links: het mag tot 6 mm in de marge hangen, de rest schuift naar rechts
                    insp = min((links + inspring - lb_x) * s, 6 * MM) / s
                snijcontrole(pdf, rel, p, blok, lb_x)
                lab = ''.join(f'\\Lbl{{{max(0.0, (y - blok["a"])) * s:.1f}}}{{{tex}}}' for _, y, tex in hier)
                if lb_x < links:
                    # de oorspronkelijke punten en vraagnummers die nu in de uitsnede vallen, wit afdekken
                    # (het boek zet zijn eigen nummer in de marge)
                    for x0, y0_, x1, y1_, t in pdf.lijnen(p):
                        if x1 < links + 1 and x1 > lb_x and LABEL.match(t.strip()) and y1_ > blok['a'] and y0_ < blok['b']:
                            lab = (f'\\fill[white] ({(max(x0, lb_x) - lb_x - 0.5) * s:.2f},{-(y0_ - blok["a"] - 0.5) * s:.2f}) '
                                   f'rectangle ({(x1 - lb_x + 0.5) * s:.2f},{-(y1_ - blok["a"] + 0.5) * s:.2f});') + lab
                regel, _ = blok_tex(pad, p, blok, lb_x, gat * s, straf, lab, passend=passend, maxh=maxh,
                                    maxschaal=maxschaal, meld=True, pas=pas, inspring=insp)
                uit.append(regel)
                if in_keten and (eerste or straf >= 10000):
                    keten += (gat + blok['b'] - blok['a']) * s
                else:
                    in_keten = False
                if kop is not None:
                    kop += (blok['b'] - blok['a']) * s
                eerste, vorige = False, blok['vast']
        self.vorige = vorige
        self.keten = keten
        return ''.join(uit)


def nodig(keten):
    """Ruimte die een opgavetitel onderaan de pagina nodig heeft: minstens 28% van de pagina, en meer als het begin
    van de opgave (inleiding plus figuur) niet gebroken mag worden."""
    return f'\\def\\OpgNodig{{{max(0.28 * TEKSTH, min(keten + 40, TEKSTH - 20)):.0f}bp}}%\n'


def linkerrand(pdf, p, y0, y1, standaard=78):
    """Snijlijn links voor een los stuk (aanvulling): standaard, of verder naar links als daar nog inkt staat."""
    inkt, _ = pdf.beeld(p)
    kol = np.nonzero(inkt[int(y0 * PX):int(y1 * PX), :int(standaard * PX)].any(axis=0))[0]
    return standaard if not len(kol) else max(20.0, kol[0] / PX - 2)


def linkse_vaak(tel, standaard, aandeel=0.15):
    """Kleinste x die in minstens `aandeel` van de regels voorkomt (x telt samen met x+1); anders standaard."""
    totaal = sum(tel.values())
    if not totaal:
        return standaard
    for x in sorted(tel):
        if tel[x] + tel.get(x + 1, 0) >= max(3, aandeel * totaal):
            return x
    return standaard


def zonder_overlap(pos):
    """Op de site mag het stuk van een vraag een stukje overlappen met het volgende (een figuurlabel naast
    de laatste regel); in het boek staan ze onder elkaar, dus daar knippen we precies tussen de twee."""
    nrs = sorted(n for n in pos if 'stuk' in pos[n] and pos[n]['stuk'])
    for a, b in zip(nrs, nrs[1:]):
        pa, ya0, ya1 = pos[a]['stuk'][-1]
        pb, yb0, yb1 = pos[b]['stuk'][0]
        if pa == pb and yb0 < ya1:
            grens = max(yb0, pos[a]['vraag'][2] + 1) if pos[a]['vraag'][0] == pa else yb0
            pos[a]['stuk'][-1] = (pa, ya0, grens)
            pos[b]['stuk'][0] = (pb, grens, yb1)


def grenzen_langs_formules(pos, pdf):
    """Een grens tussen twee vragen mag niet tussen een exponent of teller en zijn regel door lopen
    (e^(-1/x): de 1 erboven hoort bij de regel eronder). Een kort tekstje (hooguit 3 tekens) vlak boven de grens
    dat boven de eerstvolgende regel staat, gaat mee naar beneden; een subscript vlak onder de grens mee naar boven."""
    nrs = sorted(n for n in pos if pos[n].get('stuk'))
    for a, b in zip(nrs, nrs[1:]):
        pa, ya0, ya1 = pos[a]['stuk'][-1]
        pb, yb0, yb1 = pos[b]['stuk'][0]
        if pa != pb or abs(ya1 - yb0) > 0.5:
            continue
        g = yb0
        lijnen = [r for r in pdf.lijnen(pb) if r[0] >= LINKS - 5]
        onder = sorted([r for r in lijnen if g - 1 <= r[1] <= g + 14 and len(r[4].strip()) > 3], key=lambda r: r[1])
        boven = sorted([r for r in lijnen if g - 14 <= r[3] <= g + 1 and len(r[4].strip()) > 3], key=lambda r: -r[3])
        nieuw = g
        if onder:
            o = onder[0]
            klein = [r for r in lijnen if len(r[4].strip()) <= 3 and g - 9 <= r[1] < g
                     and r[0] < o[2] and r[2] > o[0] and r[1] > pos[a]['vraag'][2] - 0.5]
            if klein:
                nieuw = min(r[1] for r in klein) - 1
        if nieuw == g and boven:
            o = boven[0]
            klein = [r for r in lijnen if len(r[4].strip()) <= 3 and g < r[3] <= g + 9
                     and r[0] < o[2] and r[2] > o[0]]
            if klein:
                nieuw = max(r[3] for r in klein) + 1
        if nieuw != g and ya0 < nieuw < yb1:
            pos[a]['stuk'][-1] = (pa, ya0, nieuw)
            pos[b]['stuk'][0] = (pb, nieuw, yb1)


def witte_antwoordgrenzen(pos, pdf):
    """De grens tussen twee antwoorden ligt vlak boven 'maximumscore'. Snijdt die door iets van het vorige antwoord
    (het aslabel van een grafiek), dan schuift hij naar de dichtstbijzijnde helemaal witte regel."""
    nrs = sorted(n for n in pos if pos[n].get('antwoord'))
    for a, b in zip(nrs, nrs[1:]):
        pa, ya0, ya1 = pos[a]['antwoord'][-1]
        pb, yb0, yb1 = pos[b]['antwoord'][0]
        if pa != pb or abs(ya1 - yb0) > 0.5:
            continue
        inkt, _ = pdf.beeld(pb)
        k0, k1 = int(LINKS * PX), int((pdf.maat(pb)[0] - 18) * PX)
        leeg = lambda y: not inkt[int(y * PX), k0:k1].any()   # noqa: E731
        if leeg(yb0):
            continue
        # eerst omlaag (tot vlak boven de regel met 'maximumscore'), dan omhoog
        kandidaten = [yb0 + d / 4 for d in range(1, 15)] + [yb0 - d / 4 for d in range(1, 41)]
        for y in kandidaten:
            if leeg(y):
                pos[a]['antwoord'][-1] = (pa, ya0, y)
                pos[b]['antwoord'][0] = (pb, y, yb1)
                break


# ---------- onderdelen uit de pdf's van het CvTE ----------
def bijlage_delen(pdf):
    """{vraagnummer: [(p, y0, y1)]} uit een uitwerkbijlage."""
    uit, laatste = {}, 0
    for p, _, h, lijst in pdf.pags:
        grens = snij.voet(pdf.pags[p - 1])
        kand = sorted([r for r in lijst if r[0] < 100 and re.fullmatch(r'\d{1,2}', r[4]) and r[1] > (140 if p == 1 else 30)],
                      key=lambda r: r[1])
        # vraagnummers lopen op; een '1' of '2' in een tabel ('1e kandidaat') is geen vraagnummer
        nrs = []
        for r in kand:
            if int(r[4]) > laatste:
                nrs.append(r)
                laatste = int(r[4])
        stop = [r[1] - 4 for r in lijst if re.match(r'vergeet niet', r[4], re.I)]
        for i, r in enumerate(nrs):
            eind = nrs[i + 1][1] - 4 if i + 1 < len(nrs) else min(stop + [grens])
            uit.setdefault(int(r[4]), []).append((p, r[1] - 3, eind))
    return uit


def aanvullingen(pdf):
    """[(vraagnummer, p, y0, y1)] uit een aanvulling op het correctievoorschrift of een erratumblad."""
    uit = []
    for p, _, h, lijst in pdf.pags:
        lijst = sorted(lijst, key=lambda r: r[1])
        starts = [i for i, r in enumerate(lijst) if re.match(r'(Op|In) pagina', r[4])]
        einde = [r[1] for r in lijst if re.match(r'(Ik verzoek|Namens het College)', r[4])]
        for k, i in enumerate(starts):
            stop = lijst[starts[k + 1]][1] if k + 1 < len(starts) else min(einde + [snij.voet(pdf.pags[p - 1])])
            # een losse regel 'en' tussen twee aanvullingen hoort er niet bij
            losse = [r[1] for r in lijst if r[4].strip() == 'en' and lijst[i][1] < r[1] < stop]
            if losse:
                stop = min(losse)
            kop = ' '.join(r[4] for r in lijst[i:i + 3])
            m = re.search(r'(?:bij|boven) vraag (\d+)', kop)
            if m:
                uit.append((int(m.group(1)), p, lijst[i][1] - 3, stop - 3))
    return uit


def zoek_regel(pdf, patroon, na=(0, 0), laatste=False):
    """(pagina, regel) van de eerste (of laatste) regel die past, na positie na."""
    gevonden = [(p, r) for p, _, _, lijst in pdf.pags for r in sorted(lijst, key=lambda r: r[1])
                if (p, r[1]) > na and re.search(patroon, r[4])]
    if not gevonden:
        return None
    return gevonden[-1] if laatste else gevonden[0]


def bronvermelding(pdf):
    """Regels van de bronvermelding achter in het correctievoorschrift."""
    gev = zoek_regel(pdf, r'^\d?\s*Bronvermelding', laatste=True)
    if not gev:
        return []
    p, kop = gev
    rijen = {}
    for q in range(p, len(pdf.pags) + 1):
        grens = snij.voet(pdf.pags[q - 1])
        klaar = False
        for r in sorted(pdf.lijnen(q), key=lambda r: r[1]):
            if (q == p and r[1] <= kop[1] + 2) or r[1] >= grens:
                continue
            # soms zit er achter het correctievoorschrift nog een ander document (een aanvulling): daar stoppen
            if re.match(r'(?i)\s*(aanvulling op het correctievoorschrift|aan de secretarissen|erratum)', r[4]):
                klaar = True
                break
            rijen.setdefault((q, round(r[1] / 3)), []).append(r)
        voet = ' '.join(r[4] for r in pdf.lijnen(q) if r[1] >= grens - 2)
        if klaar or re.search(r'einde', voet, re.I):
            break
    uit = []
    for k in sorted(rijen):
        delen = [schoon(r[4]) for r in sorted(rijen[k], key=lambda r: r[0])]
        delen = [d for d in delen if d]
        if delen:
            uit.append(delen)
    return uit


def met_breekpunten(t):
    """Tekst voor LaTeX waarin lange webadressen na / . - _ = & ? mogen breken."""
    uit = []
    # ook adressen zonder https:// of www. (een domein met een pad) en andere lange woorden zonder spatie
    adres = r'(?:https?://|www\.)\S+|\S*[a-z0-9]\.[a-z]{2,6}/\S+|\S{32,}'
    for stuk in re.split(f'({adres})', t):
        if re.fullmatch(adres, stuk):
            uit.append(re.sub(r'([/.\-_=&?])', lambda m: m.group(1) + '\x00', stuk))
        else:
            uit.append(stuk)
    return esc(''.join(uit)).replace('\x00', '\\allowbreak{}')


def schoon(t):
    """Tekst uit een pdf zonder tekens die als hokje of vraagteken in het boek komen (symboolfonts, privégebied)."""
    import unicodedata
    t = unicodedata.normalize('NFKC', t)        # ligaturen als 'ﬁ' worden gewone letters
    t = t.translate(str.maketrans({'\u2010': '-', '\u2011': '-', '\u2032': "'", '\u2033': '"', '\u00ad': ''}))
    t = ''.join(c for c in t if not ('\ue000' <= c <= '\uf8ff' or c in '\ufffd\u25a1\u25ba\u25c4' or ord(c) < 32))
    return re.sub(r'\s+', ' ', t).strip()


def scoretabel(vragen, per_regel=10):
    """Tabel met per vraag het maximum en een leeg vak voor je eigen score."""
    uit = []
    for i in range(0, len(vragen), per_regel):
        deel = vragen[i:i + per_regel]
        kol = '@{}>{\\bfseries}l' + '>{\\centering\\arraybackslash}p{7.6mm}' * len(deel) + '@{}'
        uit.append(f'\\begin{{tabular}}{{{kol}}}\n'
                   + 'vraag\\hspace{2mm} & ' + ' & '.join(f'\\textbf{{{v["vraag"]}}}' for v in deel) + ' \\\\ \\hline\n'
                   + 'max & ' + ' & '.join(str(v['punten'] or '') for v in deel) + ' \\\\ \\hline\n'
                   + 'jij & ' + ' & '.join('' for v in deel) + ' \\\\ \\hline\n'
                   + '\\end{tabular}\\par\\vskip 6pt\n')
    return ''.join(uit)


def inhoud(hs, deel2, formulekaart=True):
    """Inhoudsopgave met paginanummers via \\pageref."""
    r = []
    r.append('\\InhDeel{Voorwerk}{uitleg}')
    voor = [('Zo werk je met dit boek', 'uitleg'), ('Het examen en je cijfer', 'cijfer'), ('Tips voor het examen', 'tips')]
    if formulekaart:
        voor.append(('Formulekaart', 'formulekaart'))
    for naam, lab in voor:
        r.append(f'\\InhRegel{{3mm}}{{{naam}}}{{{lab}}}')
    r.append('\\InhDeel{Deel 1 \\enspace Oefenen per onderwerp}{deel1}')
    for i, (dnaam, ond) in enumerate(hs, 1):
        r.append(f'\\InhRegel{{3mm}}{{\\textbf{{{i}}}\\enspace {esc(dnaam)}}}{{hs:{i}}}')
        for s, n, *_ in ond:
            r.append(f'\\InhRegel{{8mm}}{{\\footnotesize {esc(n)}}}{{ond:{s}}}')
    r.append('\\InhDeel{Deel 2 \\enspace Complete examens}{deel2}')
    for k, code in enumerate(deel2, 1):
        r.append(f'\\InhRegel{{3mm}}{{Examen {k}: {examen_naam(code)}}}{{ex:{code}}}')
    r.append('\\InhDeel{Uitwerkingen}{deel3}')
    r.append('\\InhRegel{3mm}{Zo wordt er nagekeken}{nakijken}')
    for i, (dnaam, _) in enumerate(hs, 1):
        r.append(f'\\InhRegel{{3mm}}{{Hoofdstuk {i}: {esc(dnaam)}}}{{ahs:{i}}}')
    for k, code in enumerate(deel2, 1):
        r.append(f'\\InhRegel{{3mm}}{{Examen {k}: {examen_naam(code)}}}{{aex:{code}}}')
    r.append('\\InhDeel{Overzicht per examen}{register}')
    r.append('\\InhDeel{Bronvermelding}{bronnen}')
    return '\n'.join(r) + '\n'


# ---------- het boek ----------
def laad(vak):
    docs = json.loads((BRON / 'documenten.json').read_text())
    bank = [v for v in json.loads((BRON / 'databank.json').read_text()) if v['vak'] == vak]
    indeling = json.loads((ROOT / 'indeling' / f'{vak}.json').read_text())
    examens = {}
    for d in docs:
        if d['vak'] != vak:
            continue
        m = re.match(r'(.*-\d\d-\d)-([a-z])(?:-(\w+))?$', d['code'])
        if not m:
            continue
        code, letter, extra = m.groups()
        ex = examens.setdefault(code, {'aanvullingen': []})
        if letter == 'o' and not extra:
            ex['opgaven'] = d
        elif letter == 'c' and not extra:
            ex['correctievoorschrift'] = d
        elif letter == 'u':
            ex['bijlage'] = d
        elif letter in ('c', 'o') and extra:
            ex['aanvullingen'].append(d)
    vragen = {}
    for v in bank:
        code = v['id'].split(':')[0]
        vragen.setdefault(code, []).append(dict(v, onderwerp=indeling.get(v['id'], v.get('onderwerp'))))
    for lijst in vragen.values():
        lijst.sort(key=lambda v: v['vraag'])
    examens = {c: e for c, e in examens.items() if 'opgaven' in e and 'correctievoorschrift' in e and c in vragen}
    return examens, vragen


def opgaven_van(vragen):
    """Vragen gegroepeerd per opgave (opeenvolgende vragen met dezelfde titel)."""
    uit = []
    for v in vragen:
        if uit and uit[-1]['titel'] == v['opgave']:
            uit[-1]['vragen'].append(v)
        else:
            uit.append({'titel': v['opgave'], 'vragen': [v]})
    for o in uit:
        tel = Counter()
        for v in o['vragen']:
            tel[v['onderwerp']] += v['punten'] or 1
        o['onderwerp'] = max(tel, key=lambda k: (tel[k], -[v['onderwerp'] for v in o['vragen']].index(k)))
        o['punten'] = sum(v['punten'] or 0 for v in o['vragen'])
    return uit


class Boek:
    def __init__(self, vak, deel1_codes, deel2_codes, examens, vragen, bouwer):
        self.vak, self.cfg = vak, instellingen(vak)
        self.info = VAKKEN[vak]
        self.examens, self.vragen, self.b = examens, vragen, bouwer
        self.deel1, self.deel2 = deel1_codes, deel2_codes
        self.pos, self.bijlagen, self.aanv = {}, {}, {}
        self.nummer = {}      # (examen, vraag) -> nummer in het boek; in deel 1 lopen de nummers door
        for code in deel1_codes + deel2_codes:
            ex = examens[code]
            pos, meld, _, _ = snij.posities(ex, vragen[code], bouwer.tmp)
            if meld:
                print('  ', code, '; '.join(meld))
                MELDINGEN.extend(f'{examen_naam(code)}: {m}' for m in meld)
            self.pos[code] = pos
            zonder_overlap(pos)
            witte_antwoordgrenzen(pos, bouwer.pdf(ex['correctievoorschrift']['pdf'])[0])
            grenzen_langs_formules(pos, bouwer.pdf(ex['opgaven']['pdf'])[0])
            bouwer.meet_tekstbegin(ex['opgaven']['pdf'], LINKS, [d for v in pos.values() for d in v.get('stuk', [])])
            bouwer.meet_tekstbegin(ex['correctievoorschrift']['pdf'], LINKS,
                                   [d for v in pos.values() for d in v.get('antwoord', [])])
            if 'bijlage' in ex:
                self.bijlagen[code] = bijlage_delen(bouwer.pdf(ex['bijlage']['pdf'])[0])
                bouwer.meet_tekstbegin(ex['bijlage']['pdf'], 95, [d for v in self.bijlagen[code].values() for d in v])
            self.aanv[code] = []
            for d in ex['aanvullingen']:
                for n, p, y0, y1 in aanvullingen(bouwer.pdf(d['pdf'])[0]):
                    self.aanv[code].append((n, d, p, y0, y1))

    # ----- vragen en antwoorden -----
    def vraag_tex(self, code, v, eerste=True):
        n = v['vraag']
        pos = self.pos[code].get(n, {})
        ex = self.examens[code]
        if 'stuk' not in pos:
            return f'\\Ontbreekt{{vraag {n}}}\n'
        p, y, _ = pos['vraag']
        nr = self.nummer.get((code, n), n)
        lab = f'\\VraagNr{{{nr}}}{{{v["punten"] or ""}}}{{v:{code}:{n}}}'
        gat0, straf0 = (0, 10000) if eerste else (14, 0)
        if not eerste:
            # loopt een figuur naast de tekst door over de grens met de vorige vraag, dan sluiten de stukken
            # zonder witruimte op elkaar aan en breekt er geen pagina tussen
            q, y0, _ = pos['stuk'][0]
            vorige = self.pos[code].get(n - 1, {}).get('stuk')
            pdf = self.b.pdf(ex['opgaven']['pdf'])[0]
            if vorige and vorige[-1][0] == q and abs(vorige[-1][2] - y0) < 0.5 and loopt_door(pdf, q, y0):
                gat0, straf0 = 0, 10000
                DOORLOPEND.add((ex['opgaven']['pdf'], q, y0))
                naam = Path(ex['opgaven']['pdf']).name
                AFGESNEDEN[:] = [m for m in AFGESNEDEN if not (m.startswith(f'{naam} blz. {q}, y ') and 'loopt door' in m
                                 and abs(float(m.split(', y ')[1].split(':')[0]) - y0) < 4)]
        tex = self.b.stukken_tex(ex['opgaven']['pdf'], pos['stuk'], 'o', [(p, y, lab)],
                                 eerste_gat=gat0, eerste_straf=straf0)
        if eerste:
            self.b.keten_eerste = self.b.keten
        if n in self.bijlagen.get(code, {}):
            bij = self.b.stukken_tex(ex['bijlage']['pdf'], self.bijlagen[code][n], 'u', links=95, passend=True)
            if bij:       # alleen schrijfregels? dan geen bijlage
                tex += f'\\BijlageKop{{{nr}}}\n' + bij
        for m, d, p2, y0, y1 in self.aanv[code]:
            if m == n and re.search(r'-o-', d['code']):
                tex += '\\AanvullingKop{Erratum van het CvTE bij deze vraag}\n'
                tex += self.b.stukken_tex(d['pdf'], [(p2, y0, y1)], 'x', passend=True,
                                          links=linkerrand(self.b.pdf(d['pdf'])[0], p2, y0, y1))
        return tex

    def antwoord_tex(self, code, v, eerste=True):
        n = v['vraag']
        pos = self.pos[code].get(n, {})
        ex = self.examens[code]
        if 'antwoord' not in pos:
            return f'\\Ontbreekt{{antwoord {n}}}\n'
        p, y0, _ = pos['antwoord'][0]
        lab = f'\\AntwNr{{{self.nummer.get((code, n), n)}}}{{a:{code}:{n}}}'
        tex = self.b.stukken_tex(ex['correctievoorschrift']['pdf'], pos['antwoord'], 'c', [(p, y0 + 4, lab)],
                                 eerste_gat=0 if eerste else 9, eerste_straf=10000 if eerste else 0)
        for m, d, p2, y1, y2 in self.aanv[code]:
            if m == n and re.search(r'-c-', d['code']):
                tex += '\\AanvullingKop{Aanvulling van het CvTE op dit antwoord}\n'
                tex += self.b.stukken_tex(d['pdf'], [(p2, y1, y2)], 'x', passend=True,
                                          links=linkerrand(self.b.pdf(d['pdf'])[0], p2, y1, y2))
        return tex

    # ----- delen van het boek -----
    def hoofdstukken(self):
        """[(domeinnaam, [(sleutel, naam, code, omschrijving, [opgaven])])] voor deel 1."""
        per = {}
        for code in sorted(self.deel1, key=examen_sleutel, reverse=True):
            for o in opgaven_van(self.vragen[code]):
                per.setdefault(o['onderwerp'], []).append(dict(o, code=code))
        uit = []
        for dnaam, lijst in self.info['domeinen']:
            ond = [(s, n, c, om, per.get(s, [])) for s, n, c, om in lijst if per.get(s)]
            if ond:
                uit.append((dnaam, ond))
        bekend = {s for _, lijst in self.info['domeinen'] for s, *_ in lijst}
        weg = [s for s in per if s not in bekend]
        if weg:
            print('  onderwerpen zonder domein:', weg)
            MELDINGEN.append(f'onderwerpen zonder domein (opgaven vallen weg uit deel 1!): {weg}')
        return uit

    def deel1_tex(self, hs):
        t = []
        nr_opg = 0
        for i, (dnaam, ond) in enumerate(hs, 1):
            aantal = sum(len(o) for *_, o in ond)
            rijen = ''.join(f'\\HsOnderwerp{{{esc(n)}}}{{{esc(c)}}}{{{len(o)}}}{{{sum(len(x["vragen"]) for x in o)}}}{{ond:{s}}}\n' for s, n, c, om, o in ond)
            t.append(f'\\Hoofdstuk{{{i}}}{{{esc(dnaam)}}}{{{aantal}}}{{%\n{rijen}}}\n')
            nr_opg = 0
            for s, n, c, om, opg in ond:
                t.append(f'\\Onderwerp{{{esc(n)}}}{{{esc(c)}}}{{{esc(om)}}}{{ond:{s}}}\n')
                nr_vraag = 0          # de vraagnummers beginnen bij elk onderwerp weer bij 1
                for o in opg:
                    nr_opg += 1
                    code = o['code']
                    eerste = o['vragen'][0]['vraag']
                    o['nr'] = f'{i}.{nr_opg}'
                    for v in o['vragen']:
                        nr_vraag += 1
                        self.nummer[(code, v['vraag'])] = nr_vraag
                    vr = [self.vraag_tex(code, v, k == 0) for k, v in enumerate(o['vragen'])]
                    t.append(nodig(self.b.keten_eerste))
                    t.append(f'\\Opgave{{{o["nr"]}}}{{{esc(o["titel"])}}}{{{examen_naam(code)}}}{{o:{code}:{eerste}}}{{{o["punten"]}}}\n')
                    t.extend(vr)
                    t.append(f'\\NaarUitwerking{{ao:{code}:{eerste}}}\n')
        return ''.join(t)

    def deel1_antw_tex(self, hs):
        t = []
        for i, (dnaam, ond) in enumerate(hs, 1):
            t.append(f'\\AntwHoofdstuk{{{i}}}{{{esc(dnaam)}}}\n')
            for s, n, c, om, opg in ond:
                # zelfde indeling als in deel 1: de nummers horen bij dit onderwerp
                t.append(f'\\AntwOnderwerp{{{esc(n)}}}{{ond:{s}}}\n')
                for o in opg:
                    code, eerste = o['code'], o['vragen'][0]['vraag']
                    t.append(f'\\AntwOpgave{{{o["nr"]}}}{{{esc(o["titel"])}}}{{{examen_naam(code)}}}{{ao:{code}:{eerste}}}{{o:{code}:{eerste}}}\n')
                    for k, v in enumerate(o['vragen']):
                        t.append(self.antwoord_tex(code, v, k == 0))
        return ''.join(t)

    def deel2_tex(self):
        t = []
        for k, code in enumerate(self.deel2, 1):
            vr = self.vragen[code]
            punten = sum(v['punten'] or 0 for v in vr)
            jaar, tv = examen_sleutel(code)
            t.append(f'\\Examen{{{k}}}{{{jaar}}}{{{tv}}}{{{len(vr)}}}{{{punten}}}{{ex:{code}}}{{aex:{code}}}\n')
            for o in opgaven_van(vr):
                eerste = o['vragen'][0]['vraag']
                vr = [self.vraag_tex(code, v, k == 0) for k, v in enumerate(o['vragen'])]
                t.append(nodig(self.b.keten_eerste))
                t.append(f'\\ExOpgave{{{esc(o["titel"])}}}{{o:{code}:{eerste}}}\n')
                t.extend(vr)
            t.append(f'\\EindeExamen{{aex:{code}}}\n')
        return ''.join(t)

    def deel2_antw_tex(self):
        t = []
        for k, code in enumerate(self.deel2, 1):
            vr = self.vragen[code]
            jaar, tv = examen_sleutel(code)
            t.append(f'\\AntwExamen{{{k}}}{{{jaar}}}{{{tv}}}{{aex:{code}}}{{ex:{code}}}\n')
            for o in opgaven_van(vr):
                eerste = o['vragen'][0]['vraag']
                t.append(f'\\AntwExOpgave{{{esc(o["titel"])}}}{{ao:{code}:{eerste}}}\n')
                for k, v in enumerate(o['vragen']):
                    t.append(self.antwoord_tex(code, v, k == 0))
            punten = sum(v['punten'] or 0 for v in vr)
            t.append(f'\\Scoretabel{{{punten}}}{{{scoretabel(vr)}}}\n')
        return ''.join(t)

    # ----- voorwerk en nawerk -----
    def formulekaart_tex(self):
        nieuwste = sorted(self.examens, key=examen_sleutel)[-1]
        rel = self.examens[nieuwste]['opgaven']['pdf']
        pdf, _ = self.b.pdf(rel)
        gev = zoek_regel(pdf, r'(?i)^(formules|formuleblad|overzicht formules)$')
        if not gev:
            return ''
        p, r = gev
        # een formuleblad kan over meer pagina's lopen (wiskunde A): door tot de pagina waar de eerste opgave begint
        eind = p
        stukken = [v['stuk'][0] for v in self.pos.get(nieuwste, {}).values() if v.get('stuk')]
        if stukken:
            eerste = min(stukken)[0]
            eind = max(p, min(eerste - 1, p + 2))
        delen = [(q, r[3] + 2 if q == p else 40, snij.voet(pdf.pags[q - 1])) for q in range(p, eind + 1)]
        return self.b.stukken_tex(rel, delen, 'f', links=LINKS, passend=True)

    def regels_tex(self):
        nieuwste = sorted(self.examens, key=examen_sleutel)[-1]
        rel = self.examens[nieuwste]['correctievoorschrift']['pdf']
        pdf, _ = self.b.pdf(rel)
        a = zoek_regel(pdf, r'^\d?\s*Vakspecifieke regels', laatste=True)
        if not a:
            return ''
        b = zoek_regel(pdf, r'^\d?\s*Beoordelingsmodel', (a[0], a[1][1]))
        eind = (b[0], b[1][1] - 3) if b else (a[0], snij.voet(pdf.pags[a[0] - 1]))
        delen = snij.stukken(pdf.pags, (a[0], a[1][3] + 2), eind, boven=64)
        return self.b.stukken_tex(rel, delen, 'x', links=78, passend=True)

    def bronnen_tex(self):
        t = []
        for code in sorted(self.deel1 + self.deel2, key=examen_sleutel):
            ex = self.examens[code]
            rijen = bronvermelding(self.b.pdf(ex['correctievoorschrift']['pdf'])[0])
            tekst = '; '.join(' — '.join(met_breekpunten(x) for x in r) for r in rijen) or 'geen aparte bronvermelding'
            t.append(f'\\BronRij{{{examen_naam(code)}}}{{{tekst}}}{{{ex["opgaven"]["url"]}}}{{{ex["correctievoorschrift"]["url"]}}}\n')
        return ''.join(t)

    def register_tex(self, hs):
        per = {}
        for dnaam, ond in hs:
            for s, n, c, om, opg in ond:
                for o in opg:
                    per.setdefault(o['code'], []).append((o['vragen'][0]['vraag'], o))
        t = []
        for code in sorted(self.deel1 + self.deel2, key=examen_sleutel, reverse=True):
            jaar, tv = examen_sleutel(code)
            if code in self.deel2:
                t.append(f'\\RegExamen{{{jaar} tijdvak {tv}}}{{compleet in deel 2}}{{ex:{code}}}\n')
                continue
            regels = ''.join(f'\\RegOpgave{{{esc(o["titel"])}}}{{{o["nr"]}}}{{o:{code}:{e}}}{{{o["vragen"][0]["vraag"]}--{o["vragen"][-1]["vraag"]}}}'
                             for e, o in sorted(per.get(code, []), key=lambda x: x[0]))
            t.append(f'\\RegExamen{{{jaar} tijdvak {tv}}}{{{regels}}}{{}}\n')
        return ''.join(t)

    def tex(self):
        hs = self.hoofdstukken()
        jaren = sorted({examen_sleutel(c)[0] for c in self.deel1 + self.deel2})
        n_opg = sum(len(o) for _, ond in hs for *_, o in ond)
        n_vr = sum(len(x['vragen']) for _, ond in hs for *_, o in ond for x in o)
        # formulekaart: 'auto' = alleen als het nieuwste examen een pagina 'Formules' heeft
        formulekaart = self.formulekaart_tex() if self.cfg['formulekaart'] else ''
        if self.cfg['formulekaart'] is True and not formulekaart:
            MELDINGEN.append('formulekaart ingesteld, maar geen pagina "Formules" gevonden')
        duur = self.cfg['duur'] or examenduur(self.examens)
        minuten = float(duur.split()[0].replace(',', '.')) * 60
        gempt = round(sum(sum(v['punten'] or 0 for v in self.vragen[c]) for c in self.examens) / len(self.examens))
        mpp = minuten / gempt
        per_punt = ('ruim ' if mpp - int(mpp) < .5 else 'bijna ') + str(int(mpp) + (mpp - int(mpp) >= .5))
        waarden = {
            'VAK': esc(self.info['naam']), 'VAKKLEIN': esc(self.info['naam'][:1].lower() + self.info['naam'][1:]), 'NIVEAU': esc(self.info['niveau']),
            'JAREN': f'{jaren[0]}–{jaren[-1]}', 'NOPG': str(n_opg), 'NVR': str(n_vr),
            'NEX': str(len(self.deel2)), 'NEXAMENS': str(len(self.deel1)),
            'VAKWOORD': self.cfg['vakwoord'], 'NTERM': self.cfg['nterm'],
            'FORMULEKAART': 'true' if formulekaart else 'false',
            'DUUR': duur, 'HULP': esc(self.cfg['hulpmiddelen']), 'HULPKLEIN': esc(self.cfg['hulpmiddelen'][:1].lower() + self.cfg['hulpmiddelen'][1:]),
            'MINPUNT': per_punt, 'MIN4': str(round(4 * minuten / gempt)),
            'SAMENSTELLER': esc(SAMENSTELLER), 'WEBADRES': esc(WEBADRES), 'MAANDJAAR': ['januari', 'februari', 'maart', 'april', 'mei', 'juni', 'juli', 'augustus', 'september', 'oktober', 'november', 'december'][datetime.date.today().month - 1] + f' {datetime.date.today().year}', 'DATUM': datetime.date.today().strftime('%-d-%-m-%Y'),
            'HOOFDSTUKLIJST': ''.join(f'\\item {esc(d)}\n' for d, _ in hs),
            'OMSLAGTABS': ','.join([f'{i}/kleur{i}' for i in range(1, len(hs) + 1)] + [f'{len(hs) + 1}/kleurex']),
            'EXAMENTAB': str(len(hs) + 1),
            'GEMVR': str(round(sum(len(self.vragen[c]) for c in self.examens) / len(self.examens))),
            'GEMPT': str(round(sum(sum(v['punten'] or 0 for v in self.vragen[c]) for c in self.examens) / len(self.examens))),
        }
        delen = {
            'formulekaart.tex': formulekaart,
            'regels.tex': self.regels_tex(),
            'deel1.tex': self.deel1_tex(hs),
            'deel2.tex': self.deel2_tex(),
            'antw1.tex': self.deel1_antw_tex(hs),
            'antw2.tex': self.deel2_antw_tex(),
            'bronnen.tex': self.bronnen_tex(),
            'register.tex': self.register_tex(hs),
            'inhoud.tex': inhoud(hs, self.deel2, bool(formulekaart)),
            'tips.tex': (Path(__file__).parent / 'bundel' / f'tips-{self.cfg["tips"]}.tex').read_text(),
            'omslag.tex': omslag_motief(self.vak, self.cfg),
        }
        return waarden, delen


def omslag_motief(vak, cfg):
    """Lijntekening voor de omslag: tools/bundel/omslag/<familie>.tex, anders het algemene motief."""
    map_ = Path(__file__).parent / 'bundel' / 'omslag'
    f = map_ / f'{cfg.get("omslag") or familie(vak)}.tex'
    return (f if f.exists() else map_ / 'algemeen.tex').read_text()


def schrijf(map_, waarden, delen):
    sjabloon = (Path(__file__).parent / 'bundel' / 'boek.tex').read_text()
    for k, v in waarden.items():
        sjabloon = sjabloon.replace(f'<<{k}>>', v)
    (map_ / 'boek.tex').write_text(sjabloon)
    for k in ('stijl.sty',):
        shutil.copy(Path(__file__).parent / 'bundel' / k, map_ / k)
    for naam, inhoud in delen.items():
        (map_ / naam).write_text(inhoud)
    (map_ / 'paginas.tex').write_text(paginas_tex())


def compileer(map_, keer=3):
    env = dict(os.environ)
    tt = sorted(Path.home().glob('Library/TinyTeX/bin/*'))
    if tt:
        env['PATH'] = f'{tt[0]}:{env["PATH"]}'
    for i in range(keer):
        r = subprocess.run(['lualatex', '-interaction=nonstopmode', '-halt-on-error', 'boek.tex'], cwd=map_, env=env,
                           capture_output=True, text=True)
        if r.returncode:
            log = (map_ / 'boek.log').read_text(errors='replace')
            fout = log[log.find('\n!'):][:2500] if '\n!' in log else r.stdout[-2500:]
            raise SystemExit('LaTeX-fout:\n' + fout)
    info = subprocess.run(['pdfinfo', str(map_ / 'boek.pdf')], capture_output=True, text=True).stdout
    return int(re.search(r'Pages:\s+(\d+)', info).group(1))


def verklein(bron, doel):
    """Elk examen-pdf bevat de volledige lettertypes (Arial, Times); in het boek komen die tientallen keren
    voor. Identieke lettertypebestanden voegen we samen (58 MB wordt zo ca. 13 MB)."""
    import hashlib
    import pikepdf
    pdf = pikepdf.open(bron)
    uniek = {}
    for obj in pdf.objects:
        if isinstance(obj, pikepdf.Dictionary) and obj.get('/Type') == '/FontDescriptor':
            for k in ('/FontFile', '/FontFile2', '/FontFile3'):
                if k in obj:
                    ff = obj[k]
                    kenmerk = sorted((str(a), str(b)) for a, b in ff.stream_dict.items() if a != '/Length')
                    h = hashlib.sha1(ff.read_raw_bytes() + repr(kenmerk).encode()).hexdigest()
                    if h in uniek:
                        obj[k] = uniek[h]
                    else:
                        uniek[h] = ff
    fotos_als_jpeg(pdf)
    pdf.save(doel, compress_streams=True, object_stream_mode=pikepdf.ObjectStreamMode.generate)


def fotos_als_jpeg(pdf, min_bytes=150_000, max_zijde=1500, kwaliteit=85):
    """Foto's staan in de examens soms verliesvrij opgeslagen. Grote afbeeldingen worden JPEG (lange zijde hooguit
    1500 px, ruim 300 dpi op de volle tekstbreedte), maar alleen als dat minstens 40% scheelt: lijntekeningen
    worden als JPEG nauwelijks kleiner en blijven dus zoals ze waren."""
    import io
    import pikepdf
    from pikepdf import PdfImage
    for obj in pdf.objects:
        if not (isinstance(obj, pikepdf.Stream) and obj.get('/Subtype') == '/Image'):
            continue
        oud = len(obj.read_raw_bytes())
        if oud < min_bytes or obj.get('/ImageMask') or obj.get('/BitsPerComponent', 8) != 8 or '/Decode' in obj:
            continue
        if str(obj.get('/Filter')) in ('/DCTDecode', '/JPXDecode'):
            continue
        try:
            beeld = PdfImage(obj).as_pil_image()
        except Exception:
            continue
        if beeld.mode not in ('RGB', 'L'):
            continue
        if max(beeld.size) > max_zijde:
            f = max_zijde / max(beeld.size)
            beeld = beeld.resize((round(beeld.width * f), round(beeld.height * f)), Image.LANCZOS)
        buf = io.BytesIO()
        beeld.save(buf, 'JPEG', quality=kwaliteit, optimize=True)
        if buf.tell() > 0.6 * oud:
            continue
        obj.write(buf.getvalue(), filter=pikepdf.Name.DCTDecode)
        obj.Width, obj.Height = beeld.width, beeld.height
        obj.ColorSpace = pikepdf.Name.DeviceRGB if beeld.mode == 'RGB' else pikepdf.Name.DeviceGray
        for k in ('/DecodeParms', '/SMaskInData'):
            if k in obj:
                del obj[k]


def controle(map_, vak, cfg, n, pdf):
    """Controleverslag na de bouw: bundels/bouw/<vak>/controle.txt plus contactvellen (controle/vel-NN.png)
    om alle pagina's in een paar plaatjes na te lopen. Geeft het aantal punten dat aandacht vraagt."""
    import tempfile
    regels, let = [], 0

    def kop(t):
        regels.append(f'\n== {t} ==')

    def punt(t, erg=True):
        nonlocal let
        regels.append(('! ' if erg else '- ') + t)
        let += erg
    regels.append(f'Controle {vak}: {n} pagina\'s (max {cfg["max_paginas"]}), {pdf.stat().st_size / 1e6:.1f} MB')
    kop('volledigheid')
    for f in ('deel1.tex', 'deel2.tex', 'antw1.tex', 'antw2.tex'):
        mis = re.findall(r'\\Ontbreekt\{([^}]*)\}', (map_ / f).read_text())
        if mis:
            punt(f'{f}: ontbreekt {", ".join(mis)}')
    vr = len(re.findall(r'\\VraagNr\{', (map_ / 'deel1.tex').read_text() + (map_ / 'deel2.tex').read_text()))
    an = len(re.findall(r'\\AntwNr\{', (map_ / 'antw1.tex').read_text() + (map_ / 'antw2.tex').read_text()))
    regels.append(f'- {vr} vragen en {an} antwoorden geplaatst')
    if vr != an:
        punt('aantal vragen en antwoorden verschilt')
    if n > cfg['max_paginas']:
        punt(f'te veel pagina\'s: {n} > {cfg["max_paginas"]}')
    kop('meldingen tijdens het snijden')
    for m in dict.fromkeys(MELDINGEN):
        punt(m, erg=not m.startswith('tekst verkleind'))
    if not MELDINGEN:
        regels.append('- geen')
    kop('uitsneden (valt er iets buiten de snijlijn?)')
    for m in dict.fromkeys(AFGESNEDEN):
        punt(m)
    if not AFGESNEDEN:
        regels.append('- niets afgesneden')
    kop('LaTeX')
    log = (map_ / 'boek.log').read_text(errors='replace')
    over = len(re.findall(r'^Overfull \\hbox \((\d+\.\d+)pt', log, re.M))
    groot = [float(x) for x in re.findall(r'^Overfull \\[hv]box \((\d+\.\d+)pt', log, re.M) if float(x) > 3]
    regels.append(f'- {over} overfull hbox (waarvan {len(groot)} meer dan 3pt)')
    if groot:
        punt(f'{len(groot)} regels/blokken steken meer dan 3pt uit (zie boek.log)')
    if 'No hyphenation patterns were preloaded' in log or 'No hyphenation patterns were loaded' in log:
        punt('geen Nederlandse afbreekpatronen (tlmgr install hyphen-dutch)')
    ontbreekt_font = re.findall(r"Font [^\n]* not found|font .* not loadable", log)
    if ontbreekt_font:
        punt(f'lettertype ontbreekt: {ontbreekt_font[0]}')
    glyf = sorted(set(re.findall(r'Missing character: There is no (.+?) in font', log)))
    if glyf:
        punt(f'tekens die het lettertype niet heeft: {", ".join(glyf[:8])}')
    if 'There were undefined references' in log or 'Label(s) may have changed' in log:
        punt('verwijzingen nog niet stabiel (nog een keer compileren)')
    if (label_pagina(map_, 'uitleg') or 0) - (label_pagina(map_, 'inhoud') or 0) > 1:
        punt('inhoudsopgave past niet op een pagina')
    kop('bladspiegel (bijna lege pagina\'s; een hoofdstukeinde of een eind van een examen is normaal)')
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(['pdftoppm', '-r', '24', '-gray', '-png', str(pdf), f'{tmp}/p'], check=True)
        fs = sorted(Path(tmp).glob('p-*.png'))
        aux = (map_ / 'boek.aux').read_text(errors='replace')
        begin = {int(x) for x in re.findall(r'\\newlabel\{(?:deel\d|hs:\d+|ex:[^}]*|ahs:\d+|aex:[^}]*|register|bronnen)\}'
                                             r'\{\{[^}]*\}\{(\d+)\}', aux)}
        kort = []
        for i, f in enumerate(fs, 1):
            a = np.array(Image.open(f))
            romp = a[int(a.shape[0] * .1):int(a.shape[0] * .88), int(a.shape[1] * .08):int(a.shape[1] * .92)]
            rijen = np.nonzero((romp < 200).any(axis=1))[0]
            vol = (rijen[-1] / len(romp)) if len(rijen) else 0
            # verwacht kort: lege pagina's, omslag, openers en de pagina voor een nieuw deel/hoofdstuk/examen
            if 0 < vol < .45 and i not in begin and i + 1 not in begin and 3 < i < len(fs) - 2:
                kort.append(f'{i} ({vol:.0%})')
        regels.append('- ' + (', '.join(kort) if kort else 'geen'))
        # contactvellen
        uit = map_ / 'controle'
        uit.mkdir(exist_ok=True)
        for oud in uit.glob('vel-*.png'):
            oud.unlink()
        ims = [Image.open(f).convert('RGB') for f in fs]
        w, h = ims[0].size
        for k in range(0, len(ims), 40):
            vel = Image.new('RGB', (10 * (w + 6), 4 * (h + 16)), 'white')
            from PIL import ImageDraw
            d = ImageDraw.Draw(vel)
            for j, im in enumerate(ims[k:k + 40]):
                x, y = (j % 10) * (w + 6), (j // 10) * (h + 16)
                vel.paste(im, (x, y + 13))
                d.text((x + 2, y), str(k + j + 1), fill='red')
            vel.save(uit / f'vel-{k // 40 + 1:02d}.png')
    regels.append(f'\ncontactvellen: {map_ / "controle"}')
    (map_ / 'controle.txt').write_text('\n'.join(regels) + '\n')
    return let


def label_pagina(map_, naam):
    aux = (map_ / 'boek.aux').read_text(errors='replace')
    m = re.search(r'\\newlabel\{' + re.escape(naam) + r'\}\{\{[^}]*\}\{(\d+)\}', aux)
    return int(m.group(1)) if m else None


def proef(vakken):
    """Droogtest zonder LaTeX: snijdt alle examens van de vakken en meldt wat ontbreekt of opvalt.
    Zo zie je voor elk vak of het boek gebouwd kan worden voordat je minutenlang compileert."""
    from bouw_site import VAKKEN
    vakken = list(VAKKEN) if vakken == ['alle'] else vakken
    rapport = []
    for vak in vakken:
        cfg = instellingen(vak)
        examens, vragen = laad(vak)
        codes = sorted(examens, key=examen_sleutel)
        deel2, deel1 = codes[-cfg['examens_deel2']:], codes[:-cfg['examens_deel2']]
        PAGINAS.clear()
        MELDINGEN.clear()
        AFGESNEDEN.clear()
        DOORLOPEND.clear()
        with tempfile.TemporaryDirectory() as tmp:
            boek = Boek(vak, deel1, deel2, examens, vragen, Bouwer(vak, tmp, Path(tmp)))
            _, delen = boek.tex()
        mis = sum(len(re.findall(r'\\Ontbreekt', delen[f])) for f in ('deel1.tex', 'deel2.tex', 'antw1.tex', 'antw2.tex'))
        vr = len(re.findall(r'\\VraagNr\{', delen['deel1.tex'] + delen['deel2.tex']))
        totaal = sum(len(vragen[c]) for c in codes)
        verkl = sum(m.startswith('tekst verkleind') for m in MELDINGEN)
        regel = (f'{vak:18} {len(codes):2} examens, {vr}/{totaal} vragen geplaatst, ontbreekt {mis}, '
                 f'meldingen {len(MELDINGEN) - verkl}, verkleinde tekst {verkl}, afgesneden {len(set(AFGESNEDEN))}, tips: {cfg["tips"]}, '
                 f'formulekaart: {"ja" if delen["formulekaart.tex"] else "nee"}, duur {cfg["duur"] or examenduur(examens)}')
        print(regel, flush=True)
        rapport.append(regel)
        rapport.extend(f'    {m}' for m in dict.fromkeys(MELDINGEN))
        rapport.extend(f'    AFGESNEDEN {m}' for m in dict.fromkeys(AFGESNEDEN))
    uit = UIT / 'bouw' / 'proef.txt'
    uit.parent.mkdir(parents=True, exist_ok=True)
    uit.write_text('\n'.join(rapport) + '\n')
    print(f'verslag: {uit}')


def publiceer():
    """Zet alle gebouwde bundels op de site: docs/bundels/<vak>.pdf en docs/data/bundels.json."""
    import pikepdf
    doel = ROOT / 'docs' / 'bundels'
    doel.mkdir(exist_ok=True)
    lijst = []
    for pdf in sorted(UIT.glob('*.pdf')):
        vak = pdf.stem
        keuze = UIT / 'bouw' / vak / 'keuze.json'
        if vak not in VAKKEN or not keuze.exists():
            print(f'overgeslagen: {pdf.name} (geen vak of geen keuze.json)')
            continue
        k = json.loads(keuze.read_text())
        shutil.copy2(pdf, doel / pdf.name)
        # omslag als plaatje voor de downloadpagina
        subprocess.run(['pdftoppm', '-png', '-r', '60', '-f', '1', '-l', '1', '-singlefile', str(pdf),
                        str(doel / vak)], check=True)
        with pikepdf.open(pdf) as p:
            n = len(p.pages)
        lijst.append({'vak': vak, 'bestand': f'bundels/{pdf.name}', 'omslag': f'bundels/{vak}.png', 'paginas': n,
                      'mb': round(pdf.stat().st_size / 1e6, 1),
                      'deel1': [examen_naam(c) for c in k['deel1']],
                      'deel2': [examen_naam(c) for c in k['deel2']],
                      'datum': datetime.date.fromtimestamp(pdf.stat().st_mtime).isoformat()})
        print(f'gepubliceerd: {pdf.name} ({n} pagina\'s)')
    for oud in [*doel.glob('*.pdf'), *doel.glob('*.png')]:   # bundels die niet meer gebouwd worden ook van de site halen
        if oud.stem not in {b['vak'] for b in lijst}:
            oud.unlink()
    (ROOT / 'docs' / 'data' / 'bundels.json').write_text(json.dumps(lijst, ensure_ascii=False, indent=1))
    print(f'{len(lijst)} bundel(s) in docs/data/bundels.json')


def main():
    if '--publiceer' in sys.argv:
        return publiceer()
    if '--proef' in sys.argv:
        return proef([a for a in sys.argv[1:] if not a.startswith('--')] or ['alle'])
    vak = next((a for a in sys.argv[1:] if not a.startswith('--')), 'wiskunde-b-vwo')
    cfg = instellingen(vak)
    examens, vragen = laad(vak)
    codes = sorted(examens, key=examen_sleutel)
    deel2 = codes[-cfg['examens_deel2']:]
    alle = codes[:-cfg['examens_deel2']]          # kandidaten voor deel 1; deel 1 = alle[i:]
    map_ = UIT / 'bouw' / vak
    map_.mkdir(parents=True, exist_ok=True)
    # begin bij het aantal examens dat de vorige keer paste (scheelt proefrondes)
    keuze = map_ / 'keuze.json'
    i = 0
    past, teveel = None, -1        # kleinste i die past, grootste i die te veel pagina's gaf
    if keuze.exists() and '--opnieuw' not in sys.argv:
        vorig = json.loads(keuze.read_text())
        if vorig.get('deel1') and vorig['deel1'][0] in alle:
            i = alle.index(vorig['deel1'][0])
        if vorig.get('te_veel') in alle:
            teveel = alle.index(vorig['te_veel'])
    gebouwd = None
    with tempfile.TemporaryDirectory() as tmp:
        bouwer = Bouwer(vak, tmp, map_)

        def bouw(i):
            deel1 = alle[i:]
            print(f'{vak}: deel 1 uit {len(deel1)} examens ({examen_naam(deel1[0])} t/m {examen_naam(deel1[-1])}), '
                  f'deel 2: {", ".join(examen_naam(c) for c in deel2)}', flush=True)
            PAGINAS.clear()
            MELDINGEN.clear()
            AFGESNEDEN.clear()
            DOORLOPEND.clear()
            boek = Boek(vak, deel1, deel2, examens, vragen, bouwer)
            waarden, delen = boek.tex()
            schrijf(map_, waarden, delen)
            n = compileer(map_, keer=2)
            print(f'  ca. {n} pagina\'s', flush=True)
            # pagina's per examen in deel 1 (opgaven en uitwerkingen samen)
            d1, d2 = label_pagina(map_, 'deel1'), label_pagina(map_, 'deel2')
            a1, a2 = label_pagina(map_, 'ahs:1'), label_pagina(map_, f'aex:{deel2[0]}')
            per = ((d2 - d1) + (a2 - a1)) / len(deel1) if None not in (d1, d2, a1, a2) else 20
            return n, per

        while True:
            n, per = bouw(i)
            gebouwd = i
            if n <= cfg['max_paginas'] - 2:
                past = i
                # ruimte over? dan probeert hij er een (ouder) examen bij, als dat nog niet te veel bleek
                if i - 1 > teveel and cfg['max_paginas'] - 2 - n >= 0.8 * per:
                    i -= 1
                    continue
                break
            teveel = i
            if i >= len(alle) - 1:
                break
            weg = max(1, int((n - cfg['max_paginas'] + 4) / per + 0.999))
            i = min(len(alle) - 1, i + weg)
            if past is not None and i >= past:
                break
        if past is not None:
            i = past
        deel1 = alle[i:]
        if gebouwd != i:
            bouw(i)
        n = compileer(map_, keer=2)
    keuze.write_text(json.dumps({'deel1': deel1, 'deel2': deel2,
                                 'te_veel': alle[teveel] if teveel >= 0 else None}, indent=1))
    verklein(map_ / 'boek.pdf', UIT / f'{vak}.pdf')
    grootte = (UIT / f'{vak}.pdf').stat().st_size / 1e6
    print(f'klaar: {UIT / f"{vak}.pdf"} ({n} pagina\'s, {grootte:.1f} MB)')
    let = controle(map_, vak, cfg, n, UIT / f'{vak}.pdf')
    print(f'controle: {let} punt(en) die aandacht vragen, zie {map_ / "controle.txt"}')


if __name__ == '__main__':
    main()
