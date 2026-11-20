# -*- coding: utf-8 -*-
# Drave Visual Buddy - lezer.py: leest het venster dat voorop staat, zoals een schermlezer.
# Gebruikt Windows UI Automation (alleen lezen: Buddy klikt niets en typt niets).
# Dravenlock (Roger & Claudio), 18-11-2026.
import time

MAX_KNOPEN = 4000          # niet eindeloos zoeken in grote pagina's
MAX_TIJD = 4.0             # seconden
BROWSER_KNOPPEN = {"Minimaliseren", "Maximaliseren", "Herstellen", "Sluiten", "Terug", "Vooruit", "Opnieuw laden",
                   "Chrome", "Adres- en zoekbalk", "Nieuw tabblad", "Extensies", "Bladwijzer toevoegen aan dit tabblad",
                   "Minimize", "Maximize", "Restore", "Close", "Back", "Forward", "Reload", "Address and search bar",
                   "New Tab", "Extensions", "Bookmark this tab", "Zijpaneel weergeven", "Tabbladen zoeken", "Search tabs"}


def _schoon(t):
    return " ".join((t or "").split()).strip()


def _titel(naam):
    n = _schoon(naam)
    for staart in (" - Google Chrome", " - Microsoft Edge", " - Mozilla Firefox", " - Opera"):
        if n.endswith(staart):
            n = n[: -len(staart)]
    return n


def lees(hwnd):
    """Geeft een dict terug: titel, koppen, knoppen, velden, links (alleen wat op het scherm staat)."""
    import uiautomation as auto
    uit = {"titel": "", "koppen": [], "knoppen": [], "velden": [], "links": 0, "linknamen": [], "teksten": [], "fout": ""}
    with auto.UIAutomationInitializerInThread():
        try:
            win = auto.ControlFromHandle(hwnd)
            uit["titel"] = _titel(win.Name)
        except Exception as ex:
            uit["fout"] = str(ex)
            return uit
        heel = False
        for poging in (1, 2, 3):                    # Chrome zet de leesboom soms pas later aan
            koppen, knoppen, velden, links, linknamen, teksten = [], [], [], 0, [], []
            # 0.1.2: in een browser alleen de ZICHTBARE pagina lezen (Chrome heeft voor elk tabblad een pagina)
            wortel = win
            try:
                if heel:
                    raise StopIteration
                beste, score = None, (0, 0, 0)
                for c, _d in auto.WalkControl(win, includeTop=False, maxDepth=25):
                    if c.ControlTypeName == "DocumentControl":
                        try:
                            if c.IsOffscreen:
                                continue
                            r = c.BoundingRectangle
                            a = max(0, r.width()) * max(0, r.height())
                            heeft_naam = 1 if _schoon(c.Name) else 0
                        except Exception:
                            continue
                        if a <= 0:
                            continue
                        sc = (heeft_naam, a, _d)                 # 0.1.3: echte pagina heeft een naam (lege buitenpagina niet)
                        if sc > score:
                            beste, score = c, sc
                if beste is not None:
                    wortel = beste
                    if not uit["titel"] or uit["titel"] == "Google Chrome":
                        uit["titel"] = _titel(beste.Name) or uit["titel"]
            except (Exception, StopIteration):
                wortel = win
            gezien = set()
            t0 = time.time()
            kader = None                                     # 0.1.4: zichtbaar deel van de pagina
            if wortel is not win:
                try:
                    kr = wortel.BoundingRectangle
                    kader = (kr.left, kr.top, kr.right, kr.bottom)
                except Exception:
                    kader = None
            n = 0
            try:
                for c, _d in auto.WalkControl(wortel, includeTop=False, maxDepth=60):
                    n += 1
                    if n > MAX_KNOPEN or time.time() - t0 > MAX_TIJD:
                        break
                    try:
                        if kader:                            # Chrome's 'IsOffscreen' klopt niet: zelf kijken
                            r = c.BoundingRectangle
                            if r.width() <= 0 or r.height() <= 0 or r.bottom <= kader[1] or r.top >= kader[3] \
                                    or r.right <= kader[0] or r.left >= kader[2]:
                                continue
                        elif c.IsOffscreen:
                            continue
                        soort = c.ControlTypeName
                        naam = _schoon(c.Name)
                    except Exception:
                        continue
                    if not naam or len(naam) > 120:
                        continue
                    rol = ""
                    try:
                        rol = (c.AriaRole or "").lower()
                    except Exception:
                        pass
                    if wortel is win and naam in BROWSER_KNOPPEN:
                        continue                             # knoppen van de browser zelf niet noemen
                    if soort == "TextControl" or rol == "heading":      # 0.2: alle zichtbare tekst, op volgorde
                        teksten.append(naam)                             # 0.2.2: dubbele tekst NIET weggooien (W 2, 9 °C ...)
                    sleutel = (soort, naam)
                    if sleutel in gezien:
                        continue
                    gezien.add(sleutel)
                    if rol == "heading":
                        koppen.append(naam)
                    elif soort == "ButtonControl" or rol == "button":
                        knoppen.append(naam)
                    elif soort in ("EditControl", "ComboBoxControl") or rol in ("textbox", "combobox", "searchbox"):
                        velden.append(naam)
                    elif soort == "HyperlinkControl" or rol == "link":
                        links += 1
                        if len(naam) <= 40:
                            linknamen.append(naam)
            except Exception as ex:
                uit["fout"] = str(ex)
            if koppen or knoppen or velden or linknamen or teksten or poging == 3:
                break
            if wortel is not win:
                heel = True                              # pagina gaf niets -> volgende poging het hele venster
            if not heel:
                time.sleep(0.8)
        uit.update(koppen=koppen, knoppen=knoppen, velden=velden, links=links, linknamen=linknamen, teksten=teksten)
    return uit


def maak_tekst(r, nl=True):
    """Van het leesresultaat een korte, duidelijke tekst maken om voor te lezen."""
    zinnen = []
    if r.get("titel"):
        zinnen.append(("Je bent in: %s." if nl else "You are in: %s.") % r["titel"])
    k = r.get("koppen", [])[:6]
    if k:
        zinnen.append(("Koppen: " if nl else "Headings: ") + " ".join(x if x[-1:] in ".?!" else x + "." for x in k))
    b = r.get("knoppen", [])[:8]
    if b:
        zinnen.append(("Knoppen: " if nl else "Buttons: ") + ", ".join(b) + ".")
    v = r.get("velden", [])[:5]
    if v:
        zinnen.append(("Invulvakjes: " if nl else "Fields: ") + ", ".join(v) + ".")
    ln = r.get("linknamen", [])[:6]
    if ln:
        zinnen.append(("Links: " if nl else "Links: ") + ", ".join(ln) + "." +
                      ((" En nog %d meer." if nl else " And %d more.") % (r["links"] - len(ln)) if r["links"] > len(ln) else ""))
    elif r.get("links"):
        zinnen.append(("Er staan %d links." if nl else "There are %d links.") % r["links"])
    if not k and not b and not v and not ln:
        zinnen.append("Ik kan in dit venster nog niets lezen." if nl else "I can't read anything in this window yet.")
    return zinnen


import re as _re
_EENHEID = _re.compile(r"^(mm/u|mm/h|mm|cm|km/u|km/h|km|°C|°F|°|%|graden|kg|g|l|ml|uur|min)$", _re.I)
_RICHTING = {"N": "noord", "NO": "noordoost", "NE": "noordoost", "O": "oost", "E": "oost", "ZO": "zuidoost", "SE": "zuidoost",
             "Z": "zuid", "S": "zuid", "ZW": "zuidwest", "SW": "zuidwest", "W": "west", "NW": "noordwest"}


def plak_stukjes(stukjes, nl=True):
    """0.2.1: Chrome knipt tekst in losse stukjes ('9', '°C' / 'W', '2'). Hier weer aan elkaar."""
    uit = []
    for t in stukjes:
        if uit and _EENHEID.match(t) and _re.search(r"\d$", uit[-1]):
            uit[-1] = uit[-1] + ("" if t.startswith("°") or t == "%" else " ") + t      # 9 + °C -> 9°C
        elif uit and _re.match(r"^\d+$", t) and uit[-1].startswith("wind ") and not _re.search(r"\d", uit[-1]):
            uit[-1] = uit[-1] + " " + t                                          # wind west + 2 -> wind west 2
        elif uit and _re.match(r"^\d+([.,]\d+)?$", t) and uit[-1].upper() in _RICHTING:
            uit[-1] = ("wind %s %s" if nl else "wind %s %s") % (_RICHTING[uit[-1].upper()] if nl else uit[-1], t)
        elif _re.match(r"^([NOZW]{1,2})(\d+)$", t) and nl:                             # W2 -> wind west 2
            m = _re.match(r"^([NOZW]{1,2})(\d+)$", t)
            uit.append("wind %s %s" % (_RICHTING.get(m.group(1), m.group(1)), m.group(2)))
        elif nl and t.upper() in _RICHTING and t.isupper():
            uit.append("wind " + _RICHTING[t.upper()])                      # losse 'ZW' -> wind zuidwest
        else:
            uit.append(t)
    return uit


def maak_voorleestekst(r, nl=True, max_stukjes=80):
    """0.2: de zichtbare tekst van boven naar beneden, in korte zinnen."""
    uit = []
    if r.get("titel"):
        uit.append(("Je bent in: %s." if nl else "You are in: %s.") % r["titel"])
    ruw = []
    for t in [t for t in r.get("teksten", []) if t][:max_stukjes]:
        if ruw:
            v = ruw[-1]
            if t == v or (len(t) > 15 and t in v) or v.endswith(" " + t) or v.startswith(t + " "):
                continue                                                      # 0.2.4: niet dubbel ("Maurice de Hond Hond")
            if t.startswith(v + " ") or t.endswith(" " + v):
                ruw[-1] = t                                                   # eerst een stukje, dan het geheel -> alleen het geheel
                continue
        ruw.append(t)
    stukjes = plak_stukjes(ruw, nl)
    regel = ""
    for t in stukjes:                                  # korte stukjes samenvoegen tot een zin
        regel = (regel + ". " + t) if regel else t      # punt = korte pauze tussen de stukjes
        if len(regel) > 100 or t[-1:] in ".!?":
            uit.append(regel if regel[-1:] in ".!?" else regel + ".")
            regel = ""
    if regel:
        uit.append(regel + ".")
    if len(uit) <= 1:
        uit.append("Ik zie hier geen tekst om voor te lezen." if nl else "I see no text to read here.")
    return uit


def lees_selectie(hwnd):
    """0.3: de tekst die je met de muis geselecteerd hebt (via Windows UI Automation). Leeg = niets gevonden."""
    import uiautomation as auto
    with auto.UIAutomationInitializerInThread():
        try:
            win = auto.ControlFromHandle(hwnd)
        except Exception:
            return ""
        kandidaten = []
        try:
            f = auto.GetFocusedControl()
            if f:
                kandidaten.append(f)
        except Exception:
            pass
        try:
            for c, _d in auto.WalkControl(win, includeTop=True, maxDepth=25):
                if c.ControlTypeName in ("DocumentControl", "EditControl"):
                    kandidaten.append(c)
                if len(kandidaten) > 12:
                    break
        except Exception:
            pass
        for c in kandidaten:
            try:
                tp = c.GetTextPattern()
                if not tp:
                    continue
                stukken = [r.GetText(20000) for r in (tp.GetSelection() or [])]
                tekst = " ".join(s for s in stukken if s and s.strip())
                if tekst.strip():
                    return tekst.strip()
            except Exception:
                continue
    return ""


def klembord_tekst():
    import uiautomation as auto
    try:
        return (auto.GetClipboardText() or "").strip()
    except Exception:
        return ""


def in_zinnen(tekst, max_lengte=220):
    """Lange tekst in nette stukjes voor de stem."""
    import re
    tekst = tekst.replace("\ufffc", " ").replace("\u200b", "").replace("\u00ad", "")   # 0.3.1: [OBJ]-blokjes (plaatjes) eruit
    tekst = re.sub(r"[ \t]+", " ", tekst.replace("\r", ""))
    stukken = []
    for alinea in [a.strip() for a in tekst.split("\n") if a.strip()]:
        for zin in re.split(r"(?<=[.!?])\s+", alinea):
            while len(zin) > max_lengte:
                knip = zin.rfind(" ", 0, max_lengte)
                knip = knip if knip > 40 else max_lengte
                stukken.append(zin[:knip].strip()); zin = zin[knip:]
            if zin.strip() and re.search(r"\w", zin):
                stukken.append(zin.strip())
    return stukken
