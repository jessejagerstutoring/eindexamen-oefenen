# Prompt: examenbundel maken voor een nieuw vak

Kopieer het blok hieronder naar Claude en vul `<VAK>` in (een sleutel uit `bouw_site.VAKKEN`, bijv. `scheikunde-havo`,
`biologie-vwo`, `wiskunde-a-havo`).

---

Maak een gratis examenbundel (A5-pdf) voor **<VAK>** met het bestaande systeem in `eindexamen-oefenen`
(`tools/bouw_bundel.py`, opmaak in `tools/bundel/`). Natuurkunde havo is het voorbeeldboek: het nieuwe boek moet er
precies zo uitzien en aan dezelfde eisen voldoen. Lees eerst de README (sectie "Oefenboek als pdf") en de docstring
bovenin het script.

**Vaste eisen aan het boek**
- A5, hooguit 280 pagina's, tekst ca. 10 pt (nooit onder 10 pt voor gewone examentekst).
- Deel 1: opgaven per domein en onderwerp; vraagnummers beginnen bij elk onderwerp opnieuw bij 1 en kloppen met de
  uitwerkingen. Deel 2: de 3 nieuwste examens compleet, met de originele nummers. Daarna de uitwerkingen (het
  correctievoorschrift van het CvTE, met aanvullingen en errata), overzicht per examen, bronvermelding.
- Vragen en antwoorden blijven exacte vectoruitsneden uit de originele pdf's: niets hertypen, het lettertype van het
  CvTE niet vervangen.
- Uitwerkbijlagen zonder schrijfregels; uitwerkingen compact; alle tekst lijnt uit op de linkermarge.
- Hooguit één kleine tipspagina, geen grote extra uitleg. Omslag met een lijntekening die bij het vak past, geen foto's.
- Het boek blijft binnen het paginabudget door de oudste examens weg te laten.

**Werkwijze**
1. Droogtest: `~/env/bin/python tools/bouw_bundel.py --proef <VAK>`. Alle vragen geplaatst, niets ontbreekt? Lees de
   meldingen in `bundels/bouw/proef.txt`; los fouten in het snijden op in de code (robuust, voor alle vakken), niet
   met uitzonderingen voor één examen.
2. Instellingen: controleer `FAMILIES` en `BOEKEN` bovenin het script (hulpmiddelen, formulekaart, vakwoord). Maak zo
   nodig `tools/bundel/tips-<familie>.tex` (10 korte, inhoudelijk juiste tips; volg de nakijkregels van het CvTE) en
   `tools/bundel/omslag/<familie>.tex` (lijntekening in kleur1–4, binnen x −8..118, y −8..58 mm, niet over de titel).
   Test een nieuw omslagmotief eerst los.
3. Bouwen: `~/env/bin/python tools/bouw_bundel.py <VAK>` (duurt ca. 5–10 min per ronde; draai op de achtergrond).
4. Controleren: lees `bundels/bouw/<VAK>/controle.txt` (moet 0 punten geven) en bekijk **alle** contactvellen in
   `bundels/bouw/<VAK>/controle/vel-*.png`. Let op: losse titels of inleidingsregels onderaan een pagina, half lege
   pagina's, figuren die over een pagina breken, verkeerde of ontbrekende uitwerkbijlagen, inhoudsopgave op meer dan
   één pagina, rare tekens (bronvermelding), uitlijning (render een paar pagina's op 80–150 dpi met de marge als
   hulplijn), omslag en titelpagina.
5. Fouten verbeteren in de code of de opmaak zodat ze voor elk vak opgelost zijn, opnieuw bouwen en opnieuw alles
   nalopen tot het boek klopt. Controleer daarna met `--proef` dat de andere vakken niet stuk zijn gegaan.
6. Werk de README bij als de werkwijze verandert. Niet committen zonder te vragen.

**Verslag aan mij (in het Nederlands, kort)**: waar de pdf staat, aantal pagina's en MB, welke examens in deel 1 en 2
staan (en welke vielen af door het budget), wat je hebt aangepast in het systeem, en wat ik zelf nog moet nakijken of
beslissen.
