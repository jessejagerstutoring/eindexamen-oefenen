"""
Analyse van de centrale examens buiten wiskunde en de bètavakken: werkt de methode van de site en de bundels
(vragen en antwoorden per vraag uit de originele pdf's halen) ook voor deze vakken?

Per examen meet dit script met dezelfde code als de site (tools/snij.py en tools/bouw_databank.py):
  - welke documenten er zijn (opgaven, correctievoorschrift, bijlage/tekstboekje, uitwerkbijlage, aanvullingen)
  - hoeveel vragen en punten, hoeveel meerkeuze, en of vragen en antwoordmodellen een-op-een te koppelen zijn
  - of de vragen ook in de pdf (met positie) te vinden zijn, zodat ze uit te snijden zijn
  - hoe vaak een vraag verwijst naar een tekst, bron of bijlage (dan is de vraag niet los te tonen)

Draaien (vanuit de map eindexamen-oefenen):
    ~/env/bin/python onderzoek/andere-vakken/analyse.py

Uitvoer: onderzoek/andere-vakken/data/examens.json (per examen) en data/vakken.json (per vak samengevat).
Raakt niets van de site (docs/) of van bronnen/.
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HIER = Path(__file__).parent
ROOT = HIER.parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import snij  # noqa: E402
from bouw_databank import lees_correctie, lees_opgaven  # noqa: E402

BRON = HIER / 'bronnen'
UIT = HIER / 'data'
VERWIJZING = re.compile(r'\b(tekst|bron|fragment|bijlage|tekstboekje|alinea|regel|afbeelding|kaart|atlas|figuur|tabel|grafiek|document)\s*\d', re.I)
TEKSTKOP = re.compile(r'^\s*(Tekst|Text|Texte|Texto)\s+(\d{1,2})\b')


def alle_documenten():
    """documenten.json plus de lijsten per jaar (documenten-2024.json) van haal_op.py --jaar, zonder dubbele."""
    uit = {}
    for f in sorted(BRON.glob('documenten*.json')):
        for d in json.loads(f.read_text()):
            if (BRON / d['pdf']).exists():
                uit[d['code']] = d
    return list(uit.values())


def pagina_aantal(pdf):
    try:
        import pikepdf
        with pikepdf.open(pdf) as p:
            return len(p.pages)
    except Exception:
        return None


def examen(ex, docs):
    """Meetgegevens voor één examen; docs = {soort: document}."""
    uit = {'examen': ex, 'documenten': sorted(docs)}
    o, c = docs.get('opgaven'), docs.get('correctievoorschrift')
    for soort, d in docs.items():
        uit.setdefault('paginas', {})[soort] = pagina_aantal(BRON / d['pdf'])
    if not o or not c:
        uit['probleem'] = 'geen opgaven of geen correctievoorschrift'
        return uit
    opg = lees_opgaven(BRON / o['tekst'])
    cor = lees_correctie(BRON / c['tekst'])
    uit['vragen'] = len(opg)
    uit['punten'] = sum(p for p, _, _ in opg.values())
    uit['antwoorden'] = len(cor)
    uit['meerkeuze'] = sum(1 for v in cor if v['punten'] is None)
    nrs_o, nrs_c = set(opg), {v['nr'] for v in cor}
    uit['koppeling'] = len(nrs_o & nrs_c)
    uit['doorlopend'] = bool(opg) and sorted(opg) == list(range(1, max(opg) + 1))
    # verwijzingen naar teksten of bronnen in de vraag zelf
    uit['verwijst'] = sum(1 for _, t, _ in opg.values() if VERWIJZING.search(t))
    # positie in de pdf: kan de vraag worden uitgesneden?
    try:
        pags = snij.regels(BRON / o['pdf'])
        uit['gevonden_pdf'] = len(snij.vragen_opgaven(pags))
        uit['antwoorden_pdf'] = len(snij.antwoorden(snij.regels(BRON / c['pdf'])))
    except Exception as e:  # noqa: BLE001
        uit['gevonden_pdf'], uit['fout'] = 0, str(e)[:200]
    # teksten (talen): koppen 'Tekst 3' in het tekstboekje of de opgaven
    teksten = set()
    for soort in ('bijlage', 'opgaven'):
        d = docs.get(soort)
        if d and (BRON / d['tekst']).exists():
            for r in (BRON / d['tekst']).read_text(errors='replace').split('\n'):
                m = TEKSTKOP.match(r)
                if m:
                    teksten.add(int(m.group(2)))
    uit['teksten'] = len(teksten)
    # in de opgaven staan dan vaak vragen per tekst ('Tekst 2 ... 3p 5 ...')
    uit['woorden_opgaven'] = len((BRON / o['tekst']).read_text(errors='replace').split())
    uit['tekstloos'] = uit['woorden_opgaven'] < 300      # opgaven als plaatje (bijv. kunst): niet te snijden zonder OCR
    return uit


def main():
    docs = alle_documenten()
    per = defaultdict(dict)
    for d in docs:
        ex = re.sub(r'-(o|c|u|b|q|a|c-a\d?|o-e)$', '', d['code'])
        soort = 'antwoordblad' if d['soort'] == 'a' else d['soort']
        per[(d['vak'], ex)].setdefault(soort, d)
    UIT.mkdir(exist_ok=True)
    examens = []
    for (vak, ex), dd in sorted(per.items()):
        e = examen(ex, dd)
        e['vak'] = vak
        e['jaar'] = next(iter(dd.values()))['jaar']
        e['tijdvak'] = next(iter(dd.values()))['tijdvak']
        e['categorie'] = next(iter(dd.values())).get('categorie')
        examens.append(e)
        print(f"{vak:34} {ex:18} v={e.get('vragen', '-'):>3} a={e.get('antwoorden', '-'):>3} "
              f"pdf={e.get('gevonden_pdf', '-'):>3} mk={e.get('meerkeuze', '-'):>3} tekst={e.get('teksten', '-'):>2} "
              f"{e.get('probleem', '')}", flush=True)
    (UIT / 'examens.json').write_text(json.dumps(examens, ensure_ascii=False, indent=1))

    vakken = {}
    for vak in sorted({e['vak'] for e in examens}):
        lijst = [e for e in examens if e['vak'] == vak]
        goed = [e for e in lijst if 'vragen' in e]
        som = lambda k: sum(e.get(k, 0) or 0 for e in goed)  # noqa: E731
        n = som('vragen')
        vakken[vak] = {
            'categorie': lijst[0]['categorie'],
            'examens': len(lijst),
            'jaren': f"{min(e['jaar'] for e in lijst)}–{max(e['jaar'] for e in lijst)}",
            'bruikbaar': len(goed),
            'vragen': n,
            'punten': som('punten'),
            'meerkeuze_pct': round(100 * som('meerkeuze') / max(1, som('antwoorden'))),
            'gekoppeld_pct': round(100 * som('koppeling') / max(1, n)),
            'in_pdf_pct': round(100 * som('gevonden_pdf') / max(1, n)),
            'antwoord_pdf_pct': round(100 * som('antwoorden_pdf') / max(1, som('antwoorden'))),
            'verwijst_pct': round(100 * som('verwijst') / max(1, n)),
            'teksten_per_examen': round(som('teksten') / max(1, len(goed)), 1),
            'documenten': dict(Counter(s for e in lijst for s in e['documenten'])),
            'paginas_opgaven': round(sum((e.get('paginas') or {}).get('opgaven') or 0 for e in lijst) / max(1, len(lijst))),
            'tekstloos': sum(1 for e in goed if e.get('tekstloos')),
            'paginas_bijlage': round(sum((e.get('paginas') or {}).get('bijlage') or 0 for e in lijst) / max(1, len(lijst))),
        }
    (UIT / 'vakken.json').write_text(json.dumps(vakken, ensure_ascii=False, indent=1))
    print(f'\n{len(examens)} examens, {len(vakken)} vakken -> {UIT}')


if __name__ == '__main__':
    main()
