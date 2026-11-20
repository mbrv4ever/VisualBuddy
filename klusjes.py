# -*- coding: utf-8 -*-
"""DraveHanden - klusjes 0.2: Windows-instellingen vinden, uitleggen en (na JA) voor je doen.

Voor iedereen die instellingen niet kan vinden (Microsoft verstopt ze diep) of het niet durft.
Elk klusje heeft:
  - zoek         -> "muis groter", "pijltje te klein" vindt het juiste klusje
  - pagina       -> de Windows-instellingenpagina die we kunnen openen (ms-settings:)
  - stappen      -> wat je daar zelf moet doen, in gewone taal (om voor te lezen)
  - huidig()     -> hoe het nu is (alleen lezen)
  - acties()     -> knoppen die het Maatje zelf kan doen, elk met een JA-vraag
  - herstel()    -> zet het terug zoals het was (Terugzetten)

Regels:
  - doe_actie() en terugzetten() doen NIETS zonder bevestigd=True (de gebruiker drukte op JA).
  - Alleen gebruikersinstellingen (geen beheerdersrechten, niets van het systeem).
  - Beveiliging (firewall, virusscanner, UAC) NOOIT zelf: alleen de pagina openen en uitleggen.
  - Voor elke verandering onthouden we de ALLEREERSTE stand (handen_terug.json), zodat Terugzetten altijd kan.
  - Alles in handen_logboek.txt.
"""
from __future__ import annotations

import difflib
import json
import os
import re
import subprocess
import sys
import time

VERSIE = "0.2"
NO_WIN = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _hier():
    return os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))


def _t(nl, en, taal):
    return nl if taal == "nl" else en


def _logboek(regel):
    try:
        with open(os.path.join(_hier(), "handen_logboek.txt"), "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + regel + "\n")
    except Exception:
        pass


TERUG_JSON = "handen_terug.json"


def _terug_lees():
    try:
        with open(os.path.join(_hier(), TERUG_JSON), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _terug_schrijf(d):
    try:
        with open(os.path.join(_hier(), TERUG_JSON), "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
    except Exception:
        pass


def _bewaar_oud(klus_id, waarde):
    """Bewaar alleen de ALLEREERSTE stand: Terugzetten gaat altijd naar hoe het was vóór het Maatje."""
    t = _terug_lees()
    if klus_id not in t:
        t[klus_id] = {"oud": waarde, "datum": time.strftime("%Y-%m-%d %H:%M")}
        _terug_schrijf(t)


def _ps(cmd, timeout=30):
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
                           capture_output=True, text=True, timeout=timeout, creationflags=NO_WIN)
        return r.returncode, (r.stdout or "").strip()
    except Exception as ex:
        return 1, str(ex)


def _klaar(uitleg, gedaan=True):
    return {"gedaan": gedaan, "uitleg": uitleg}


def open_pagina(uri):
    """Opent een Windows-instellingenpagina. Verandert zelf niets."""
    try:
        os.startfile(uri)
        return True
    except Exception:
        return False


def _draait(exe):
    try:
        r = subprocess.run(["tasklist", "/fi", "imagename eq %s" % exe, "/nh"], capture_output=True, text=True,
                           timeout=15, creationflags=NO_WIN)
        return exe.lower() in (r.stdout or "").lower()
    except Exception:
        return False


# =====================================================================  muispijl
_REG_CURSORS = r"Control Panel\Cursors"
_REG_TOEGANG = r"Software\Microsoft\Accessibility"


def _muis_lees():
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_TOEGANG) as k:
            return int(winreg.QueryValueEx(k, "CursorSize")[0])
    except Exception:
        pass
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_CURSORS) as k:
            basis = int(winreg.QueryValueEx(k, "CursorBaseSize")[0])
        return max(1, min(15, (basis - 16) // 16))
    except Exception:
        return 1


def _muis_zet(stand):
    import ctypes
    import winreg
    stand = max(1, min(15, int(stand)))
    basis = 16 + 16 * stand                                            # stand 1 = 32 pixels, stand 15 = 256
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, _REG_TOEGANG) as k:
        winreg.SetValueEx(k, "CursorSize", 0, winreg.REG_DWORD, stand)
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, _REG_CURSORS) as k:
        winreg.SetValueEx(k, "CursorBaseSize", 0, winreg.REG_DWORD, basis)
    spi = ctypes.windll.user32.SystemParametersInfoW
    spi(0x2029, 0, basis, 0x01 | 0x02)
    spi(0x0057, 0, None, 0x01 | 0x02)
    return stand


def _muis_woord(stand, taal):
    if stand <= 1:
        return _t("normaal", "normal", taal)
    if stand <= 4:
        return _t("een beetje groter", "a bit bigger", taal)
    if stand <= 8:
        return _t("groot", "big", taal)
    return _t("heel groot", "very big", taal)


def muis_huidig(taal="nl"):
    s = _muis_lees()
    return _t("Je muispijl is nu %s (stand %d van 15)." % (_muis_woord(s, taal), s),
              "Your mouse pointer is now %s (step %d of 15)." % (_muis_woord(s, taal), s), taal)


def _muis_stap(d, taal):
    oud = _muis_lees() or 1
    nieuw_doel = max(1, min(15, oud + d))
    if nieuw_doel == oud:
        return _klaar(_t("Verder kan niet: je muispijl is al %s." % _muis_woord(oud, taal), "Can't go further.", taal), False)
    _bewaar_oud("muispijl", oud)
    nieuw = _muis_zet(nieuw_doel)
    _logboek("MUISPIJL: stand %d -> %d" % (oud, nieuw))
    return _klaar(_t("Klaar! Je muispijl is nu %s. Vind je het niks? Druk dan op Terugzetten." % _muis_woord(nieuw, taal),
                     "Done! Your pointer is now %s. Don't like it? Press Undo." % _muis_woord(nieuw, taal), taal))


def muis_acties(taal="nl"):
    return [{"id": "groter", "label": _t("Maak hem groter", "Make it bigger", taal),
             "vraag": _t("Zal ik je muispijl groter maken?", "Shall I make your pointer bigger?", taal),
             "doe": lambda tl: _muis_stap(2, tl)},
            {"id": "kleiner", "label": _t("Maak hem kleiner", "Make it smaller", taal),
             "vraag": _t("Zal ik je muispijl kleiner maken?", "Shall I make your pointer smaller?", taal),
             "doe": lambda tl: _muis_stap(-2, tl)}]


def muis_herstel(oud, taal="nl"):
    _muis_zet(int(oud))
    return _t("Je muispijl is weer zoals eerst: %s." % _muis_woord(int(oud), taal), "Your pointer is back as before.", taal)


# =====================================================================  geluid
def _toets(vk, keer=1):
    import ctypes
    kb = ctypes.windll.user32.keybd_event
    for _ in range(keer):
        kb(vk, 0, 0, 0)
        kb(vk, 0, 2, 0)
        time.sleep(0.03)


def geluid_huidig(taal="nl"):
    return _t("Ik kan het geluid harder of zachter zetten, een stukje per keer. Of helemaal uit, en weer aan.",
              "I can make the sound louder or softer, a bit at a time. Or mute it, and unmute.", taal)


def geluid_acties(taal="nl"):
    def harder(tl):
        _toets(0xAF, 5); _logboek("GELUID: harder")
        return _klaar(_t("Het geluid staat een stukje harder. Nog harder? Druk nog een keer.", "Louder now. Press again for more.", tl))

    def zachter(tl):
        _toets(0xAE, 5); _logboek("GELUID: zachter")
        return _klaar(_t("Het geluid staat een stukje zachter.", "Softer now.", tl))

    def stil(tl):
        _toets(0xAD, 1); _logboek("GELUID: stil/aan")
        return _klaar(_t("Het geluid is uit, of weer aan als het uit stond.", "Sound muted, or unmuted if it was muted.", tl))
    return [{"id": "harder", "label": _t("Harder", "Louder", taal), "vraag": _t("Zal ik het geluid harder zetten?", "Make it louder?", taal), "doe": harder},
            {"id": "zachter", "label": _t("Zachter", "Softer", taal), "vraag": _t("Zal ik het geluid zachter zetten?", "Make it softer?", taal), "doe": zachter},
            {"id": "stil", "label": _t("Geluid uit / aan", "Mute / unmute", taal), "vraag": _t("Zal ik het geluid uit (of weer aan) zetten?", "Mute or unmute?", taal), "doe": stil}]


# =====================================================================  vergrootglas en Verteller
def _programma_klusje(exe, naam_nl, naam_en, tip_nl, tip_en):
    def huidig(taal="nl"):
        aan = _draait(exe)
        return _t("%s staat nu %s. %s" % (naam_nl, "AAN" if aan else "uit", tip_nl),
                  "%s is now %s. %s" % (naam_en, "ON" if aan else "off", tip_en), taal)

    def aan_(tl):
        if _draait(exe):
            return _klaar(_t("%s staat al aan." % naam_nl, "%s is already on." % naam_en, tl), False)
        subprocess.Popen([exe], creationflags=NO_WIN)
        _logboek("%s: aan" % exe)
        return _klaar(_t("%s staat nu aan." % naam_nl, "%s is now on." % naam_en, tl))

    def uit_(tl):
        if not _draait(exe):
            return _klaar(_t("%s staat al uit." % naam_nl, "%s is already off." % naam_en, tl), False)
        subprocess.run(["taskkill", "/im", exe], capture_output=True, timeout=15, creationflags=NO_WIN)
        _logboek("%s: uit" % exe)
        return _klaar(_t("%s staat nu uit." % naam_nl, "%s is now off." % naam_en, tl))

    def acties(taal="nl"):
        return [{"id": "aan", "label": _t("Zet aan", "Turn on", taal), "vraag": _t("Zal ik %s aanzetten?" % naam_nl, "Turn on %s?" % naam_en, taal), "doe": aan_},
                {"id": "uit", "label": _t("Zet uit", "Turn off", taal), "vraag": _t("Zal ik %s uitzetten?" % naam_nl, "Turn off %s?" % naam_en, taal), "doe": uit_}]
    return huidig, acties


verg_huidig, verg_acties = _programma_klusje(
    "magnify.exe", "Het vergrootglas", "The magnifier",
    "Zelf kan ook: Windows-toets en plus (+) = aan en groter, Windows-toets en Esc = uit.",
    "Shortcut: Windows key + plus = on, Windows key + Esc = off.")
vert_huidig, vert_acties = _programma_klusje(
    "narrator.exe", "De Verteller (voorleesstem van Windows)", "Narrator",
    "Zelf kan ook: Ctrl, Windows-toets en Enter tegelijk = aan of uit.", "Shortcut: Ctrl + Windows key + Enter.")


# =====================================================================  donker of licht scherm
_REG_THEMA = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"


def _thema_lees():
    import winreg
    uit = {}
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_THEMA) as k:
        for n in ("AppsUseLightTheme", "SystemUsesLightTheme"):
            try:
                uit[n] = int(winreg.QueryValueEx(k, n)[0])
            except OSError:
                uit[n] = 1
    return uit


def _thema_zet(waarden):
    import ctypes
    import winreg
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, _REG_THEMA) as k:
        for n, v in waarden.items():
            winreg.SetValueEx(k, n, 0, winreg.REG_DWORD, int(v))
    res = ctypes.c_ulong()
    ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001A, 0, "ImmersiveColorSet", 0x0002, 3000, ctypes.byref(res))


def thema_huidig(taal="nl"):
    try:
        d = _thema_lees()
        donker = d.get("AppsUseLightTheme", 1) == 0
        return _t("Je scherm staat nu op %s." % ("DONKER" if donker else "LICHT"), "Your screen is now %s." % ("DARK" if donker else "LIGHT"), taal)
    except Exception:
        return _t("Ik kon niet lezen of je scherm donker of licht is.", "I couldn't read the theme.", taal)


def thema_acties(taal="nl"):
    def zet(licht, tl):
        _bewaar_oud("thema", _thema_lees())
        _thema_zet({"AppsUseLightTheme": licht, "SystemUsesLightTheme": licht})
        _logboek("THEMA: %s" % ("licht" if licht else "donker"))
        return _klaar(_t("Klaar! Je scherm is nu %s. Sommige programma's veranderen pas als je ze opnieuw opent." % ("licht" if licht else "donker"),
                         "Done! Some programs change after reopening.", tl))
    return [{"id": "donker", "label": _t("Maak donker", "Make dark", taal), "vraag": _t("Zal ik je scherm donker maken?", "Make your screen dark?", taal),
             "doe": lambda tl: zet(0, tl)},
            {"id": "licht", "label": _t("Maak licht", "Make light", taal), "vraag": _t("Zal ik je scherm licht maken?", "Make your screen light?", taal),
             "doe": lambda tl: zet(1, tl)}]


def thema_herstel(oud, taal="nl"):
    _thema_zet(oud)
    return _t("Je scherm is weer zoals eerst.", "Your screen is back as before.", taal)


# =====================================================================  dubbelklikken
def _dk_lees():
    import ctypes
    return int(ctypes.windll.user32.GetDoubleClickTime())


def _dk_zet(ms):
    import ctypes
    ms = max(200, min(900, int(ms)))
    ctypes.windll.user32.SystemParametersInfoW(0x0020, ms, None, 0x01 | 0x02)   # SPI_SETDOUBLECLICKTIME
    return ms


def dk_huidig(taal="nl"):
    try:
        ms = _dk_lees()
    except Exception:
        return _t("Ik kon de dubbelklik-snelheid niet lezen.", "I couldn't read the double-click speed.", taal)
    woord = _t("snel" if ms < 450 else ("normaal" if ms <= 550 else "rustig"), "fast" if ms < 450 else ("normal" if ms <= 550 else "slow"), taal)
    return _t("Je moet nu binnen %.1f seconde twee keer klikken (%s). Lukt dubbelklikken vaak niet? Maak het dan trager." % (ms / 1000.0, woord),
              "You now have %.1f seconds to double-click (%s)." % (ms / 1000.0, woord), taal).replace(".", ",", 1)


def dk_acties(taal="nl"):
    def stap(d, tl):
        oud = _dk_lees()
        _bewaar_oud("dubbelklik", oud)
        nieuw = _dk_zet(oud + d)
        _logboek("DUBBELKLIK: %d -> %d ms" % (oud, nieuw))
        return _klaar(_t("Klaar! Je hebt nu %.1f seconde voor een dubbelklik." % (nieuw / 1000.0), "Done! You now have %.1f s." % (nieuw / 1000.0), tl).replace(".", ",", 1))
    return [{"id": "trager", "label": _t("Maak het rustiger (trager)", "Make it slower", taal),
             "vraag": _t("Zal ik dubbelklikken rustiger maken? Dan heb je meer tijd tussen de twee klikken.", "Make double-clicking slower?", taal),
             "doe": lambda tl: stap(150, tl)},
            {"id": "sneller", "label": _t("Maak het sneller", "Make it faster", taal),
             "vraag": _t("Zal ik dubbelklikken sneller maken?", "Make double-clicking faster?", taal), "doe": lambda tl: stap(-150, tl)}]


def dk_herstel(oud, taal="nl"):
    _dk_zet(int(oud))
    return _t("Dubbelklikken is weer zoals eerst.", "Double-click speed is back as before.", taal)


# =====================================================================  standaard printer
_NIET_PRINTER = ("fax", "onenote", "xps")


def _printers():
    code, uit = _ps("Get-CimInstance Win32_Printer | Select-Object Name, Default | ConvertTo-Json -Compress")
    try:
        d = json.loads(uit or "[]")
        d = d if isinstance(d, list) else [d]
        return [(p["Name"], bool(p.get("Default"))) for p in d if not any(w in p["Name"].lower() for w in _NIET_PRINTER)]
    except Exception:
        return []


def _legacy_lees():
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows NT\CurrentVersion\Windows") as k:
            return int(winreg.QueryValueEx(k, "LegacyDefaultPrinterMode")[0])
    except Exception:
        return 0


def _legacy_zet(v):
    import winreg
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows NT\CurrentVersion\Windows") as k:
        winreg.SetValueEx(k, "LegacyDefaultPrinterMode", 0, winreg.REG_DWORD, int(v))


def _printer_zet(naam):
    veilig = naam.replace("'", "''")
    return _ps("Get-CimInstance Win32_Printer -Filter \"Name='%s'\" | Invoke-CimMethod -MethodName SetDefaultPrinter | Out-Null"
               % veilig.replace("\\", "\\\\"))[0] == 0


def _spooler_aan():
    try:
        r = subprocess.run(["sc", "query", "spooler"], capture_output=True, text=True, timeout=10, creationflags=NO_WIN)
        return "RUNNING" in (r.stdout or "").upper()
    except Exception:
        return True


def printer_huidig(taal="nl"):
    if not _spooler_aan():
        return _t("De printerdienst van Windows (Afdrukwachtrij) staat uit. Daarom zie ik geen printers. Print je niet? Dan is dat juist veilig. "
                  "Wil je wel printen? Vraag dan iemand die je vertrouwt om de Afdrukwachtrij aan te zetten. Dat is een systeeminstelling: die verander ik niet zelf.",
                  "The Windows print service (Print Spooler) is off, so I see no printers. Ask someone you trust to turn it on.", taal)
    ps = _printers()
    std = [n for n, d in ps if d]
    if not ps:
        return _t("Ik vind geen printers op je pc.", "I find no printers.", taal)
    return _t("Je standaard printer is nu: %s. Je hebt %d printer(s)." % (std[0] if std else "geen", len(ps)),
              "Your default printer is: %s." % (std[0] if std else "none"), taal)


def printer_acties(taal="nl"):
    uit = []
    if not _spooler_aan():
        return uit
    for naam, std in _printers():
        if std:
            continue

        def doe(tl, n=naam):
            oud = [x for x, d in _printers() if d]
            _bewaar_oud("printer", {"printer": oud[0] if oud else "", "legacy": _legacy_lees()})
            _legacy_zet(1)                                             # anders kiest Windows zelf weer een andere
            ok = _printer_zet(n)
            _logboek("PRINTER: standaard -> %s (%s)" % (n, "ok" if ok else "mislukt"))
            return _klaar(_t("Klaar! %s is nu je standaard printer." % n if ok else "Dat lukte niet.", "Done! %s is now your default printer." % n, tl), ok)
        uit.append({"id": "p_" + naam, "label": _t("Maak %s de standaard" % naam, "Make %s the default" % naam, taal),
                    "vraag": _t("Zal ik %s je standaard printer maken? Ik zet ook uit dat Windows zelf steeds een andere kiest." % naam,
                                "Make %s your default printer?" % naam, taal), "doe": doe})
    return uit


def printer_herstel(oud, taal="nl"):
    if oud.get("printer"):
        _printer_zet(oud["printer"])
    _legacy_zet(oud.get("legacy", 0))
    return _t("Je standaard printer is weer zoals eerst.", "Your default printer is back as before.", taal)


# =====================================================================  meestarters (alleen die van jou: geen beheerder nodig)
_RUN = r"Software\Microsoft\Windows\CurrentVersion\Run"
_GOED_RUN = r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"
_GOED_MAP = r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\StartupFolder"
_NOOIT_UIT = ("security", "defender", "antivirus", "virus", "firewall", "drave")


def _opstartmap():
    return os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs", "Startup")


def _goedkeuring_lees(sleutel, naam):
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sleutel) as k:
            v = winreg.QueryValueEx(k, naam)[0]
            return bytes(v)[0] in (2, 6) if v else True                # 02/06 = aan, 03/07 = uit
    except OSError:
        return True                                                    # niets ingesteld = aan


def _goedkeuring_zet(sleutel, naam, aan):
    import winreg
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, sleutel) as k:
        winreg.SetValueEx(k, naam, 0, winreg.REG_BINARY, bytes([2 if aan else 3]) + bytes(11))


def meestarters():
    """[(naam, sleutel, aan)] - alleen die van de gebruiker zelf."""
    uit = []
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN) as k:
            for i in range(winreg.QueryInfoKey(k)[1]):
                naam = winreg.EnumValue(k, i)[0]
                uit.append((naam, _GOED_RUN, _goedkeuring_lees(_GOED_RUN, naam)))
    except Exception:
        pass
    m = _opstartmap()
    if os.path.isdir(m):
        for f in os.listdir(m):
            if f.lower() != "desktop.ini":
                uit.append((f, _GOED_MAP, _goedkeuring_lees(_GOED_MAP, f)))
    return [x for x in uit if not any(w in x[0].lower() for w in _NOOIT_UIT)]


def opstart_huidig(taal="nl"):
    lijst = meestarters()
    aan = [n for n, _s, a in lijst if a]
    if not lijst:
        return _t("Er starten geen programma's van jou mee. Mooi zo!", "No programs of yours start with Windows.", taal)
    return _t("Er starten %d programma's van jou mee met Windows: %s. Minder meestarters = sneller opstarten. "
              "Programma's van het systeem en je beveiliging laat ik met rust." % (len(aan), ", ".join(os.path.splitext(n)[0] for n in aan) or "geen"),
              "%d of your programs start with Windows." % len(aan), taal)


def opstart_acties(taal="nl"):
    uit = []
    for naam, sleutel, aan in meestarters():
        kort = os.path.splitext(naam)[0]

        def doe(tl, n=naam, s=sleutel, nu_aan=aan, k=kort):
            t = _terug_lees().get("opstart", {}).get("oud", {})
            if n not in t:                                             # per programma de eerste stand onthouden
                alles = _terug_lees()
                alles.setdefault("opstart", {"oud": {}, "datum": time.strftime("%Y-%m-%d %H:%M")})["oud"][n] = [s, nu_aan]
                _terug_schrijf(alles)
            _goedkeuring_zet(s, n, not nu_aan)
            _logboek("MEESTARTER: %s -> %s" % (n, "aan" if not nu_aan else "uit"))
            return _klaar(_t("Klaar! %s start %s mee met Windows. Je merkt het de volgende keer dat je de pc aanzet."
                             % (k, "weer" if not nu_aan else "niet meer"), "Done! %s now %s with Windows." % (k, "starts" if not nu_aan else "no longer starts"), tl))
        uit.append({"id": "o_" + naam, "label": _t(("Zet %s uit" if aan else "Zet %s weer aan") % kort, ("Disable %s" if aan else "Enable %s") % kort, taal),
                    "vraag": _t(("Zal ik %s niet meer laten meestarten? Het programma blijft gewoon op je pc staan." if aan
                                 else "Zal ik %s weer laten meestarten?") % kort, "Change startup for %s?" % kort, taal), "doe": doe})
    return uit


def opstart_herstel(oud, taal="nl"):
    for naam, (sleutel, aan) in oud.items():
        try:
            _goedkeuring_zet(sleutel, naam, aan)
        except Exception:
            pass
    return _t("De meestarters zijn weer zoals eerst.", "Startup programs are back as before.", taal)


# =====================================================================  Windows Update
def update_huidig(taal="nl"):
    return _t("Ik kan Windows laten zoeken naar updates. Dan opent de pagina Windows Update en zoekt hij vanzelf.",
              "I can make Windows look for updates.", taal)


def update_acties(taal="nl"):
    def zoek_(tl):
        open_pagina("ms-settings:windowsupdate-action")
        _logboek("UPDATE: zoeken gestart")
        return _klaar(_t("Windows zoekt nu naar updates. Laat het venster open staan. Vraagt hij om opnieuw op te starten? Sla eerst je werk op.",
                         "Windows is looking for updates now.", tl))
    return [{"id": "zoek", "label": _t("Zoek nu naar updates", "Check for updates now", taal),
             "vraag": _t("Zal ik Windows laten zoeken naar updates?", "Make Windows check for updates?", taal), "doe": zoek_}]


# =====================================================================  de lijst met klusjes
def K(id_, titel, zoek, pagina, stappen_nl, stappen_en, huidig=None, acties=None, herstel=None):
    return {"id": id_, "titel": titel, "zoek": zoek, "pagina": pagina, "stappen": (stappen_nl, stappen_en),
            "huidig": huidig, "acties": acties, "herstel": herstel}


KLUSJES = [
    # ---- het Maatje kan het zelf (na JA)
    K("muispijl", ("Muispijl groter", "Bigger mouse pointer"),
      ["muispijl", "muis", "pijl", "pijltje", "aanwijzer", "cursor", "pointer", "ik zie mijn muis niet", "muis kwijt", "mouse"],
      "ms-settings:easeofaccess-mousepointer",
      ["Ik open de pagina Muisaanwijzer.", "Bij Grootte zie je een schuifbalkje.", "Schuif het balkje naar rechts. Hoe verder, hoe groter de pijl.",
       "Je ziet het meteen. Klaar? Sluit de pagina gewoon."],
      ["I'll open the Mouse pointer page.", "Under Size there's a slider.", "Move it to the right for a bigger pointer.", "Done? Close the page."],
      muis_huidig, muis_acties, muis_herstel),
    K("geluid", ("Geluid harder of zachter", "Sound louder or softer"),
      ["geluid", "volume", "harder", "zachter", "hoor niets", "hoor ik niet", "te zacht", "te hard", "speaker", "luidspreker", "sound", "mute"],
      "ms-settings:sound",
      ["Ik open de pagina Geluid.", "Bij Volume zie je een schuifbalkje.", "Schuif naar rechts voor harder, naar links voor zachter.",
       "Hoor je nog steeds niets? Kijk bij Uitvoer of het goede apparaat gekozen is, bijvoorbeeld je luidsprekers."],
      ["I'll open the Sound page.", "Use the Volume slider.", "Right = louder, left = softer.", "Still nothing? Check the Output device."],
      geluid_huidig, geluid_acties),
    K("vergrootglas", ("Vergrootglas", "Magnifier"),
      ["vergrootglas", "vergroot", "inzoomen", "zoom", "groter zien", "loep", "magnifier", "slecht zien"],
      "ms-settings:easeofaccess-magnifier",
      ["Ik open de pagina Vergrootglas.", "Zet de schakelaar bij Vergrootglas op Aan.", "Met plus en min zoom je in en uit.",
       "Sneller: Windows-toets en plus = aan, Windows-toets en Esc = uit."],
      ["I'll open the Magnifier page.", "Turn the Magnifier switch On.", "Use plus and minus to zoom.", "Windows+plus = on, Windows+Esc = off."],
      verg_huidig, verg_acties),
    K("verteller", ("Voorleesstem van Windows (Verteller)", "Windows read-aloud voice (Narrator)"),
      ["verteller", "voorlezen", "voorlees", "narrator", "stem", "lees voor", "blind"],
      "ms-settings:easeofaccess-narrator",
      ["Ik open de pagina Verteller.", "Zet de schakelaar bij Verteller op Aan.", "Uitzetten kan met Ctrl, Windows-toets en Enter tegelijk."],
      ["I'll open the Narrator page.", "Turn Narrator On.", "Ctrl+Windows+Enter turns it off."],
      vert_huidig, vert_acties),
    K("thema", ("Donker of licht scherm", "Dark or light screen"),
      ["donker", "licht", "donkere modus", "dark mode", "wit scherm", "te fel", "zwart", "thema", "kleur", "dark", "light"],
      "ms-settings:colors",
      ["Ik open de pagina Kleuren.", "Bij Je modus kiezen kies je Donker of Licht.", "Je ziet het meteen."],
      ["I'll open the Colors page.", "Under Choose your mode, pick Dark or Light."],
      thema_huidig, thema_acties, thema_herstel),
    K("dubbelklik", ("Dubbelklikken trager", "Slower double-click"),
      ["dubbelklik", "dubbel klik", "klikken lukt niet", "dubbelklikken", "klik", "double click", "openen lukt niet"],
      "ms-settings:mousetouchpad",
      ["Ik open de pagina Muis.", "Klik helemaal onderaan op Aanvullende muisinstellingen.", "Bij Dubbelkliksnelheid schuif je het balkje naar links voor trager.",
       "Probeer het uit op het mapje ernaast, en klik op OK."],
      ["I'll open the Mouse page.", "Click Additional mouse settings.", "Move the double-click slider left for slower.", "Click OK."],
      dk_huidig, dk_acties, dk_herstel),
    K("printer", ("Standaard printer kiezen", "Choose default printer"),
      ["printer", "printen", "afdrukken", "print", "standaard printer", "verkeerde printer"],
      "ms-settings:printers",
      ["Ik open de pagina Printers en scanners.", "Klik op je printer, en dan op Als standaard instellen.",
       "Zie je die knop niet? Zet dan eerst Windows mijn standaardprinter laten beheren uit."],
      ["I'll open Printers & scanners.", "Click your printer, then Set as default."],
      printer_huidig, printer_acties, printer_herstel),
    K("opstart", ("Programma's niet laten meestarten", "Stop programs starting with Windows"),
      ["meestarten", "opstarten", "traag", "langzaam", "start langzaam", "opstart", "startup", "pc is traag", "sneller"],
      "ms-settings:startupapps",
      ["Ik open de pagina Opstarten.", "Je ziet een lijst met programma's en schakelaars.",
       "Zet de schakelaar uit bij programma's die je niet meteen nodig hebt. Laat je beveiliging altijd aan."],
      ["I'll open Startup apps.", "Turn off programs you don't need right away. Keep security on."],
      opstart_huidig, opstart_acties, opstart_herstel),
    K("update", ("Windows bijwerken (updates)", "Windows updates"),
      ["update", "updates", "bijwerken", "windows update", "nieuwste versie"],
      "ms-settings:windowsupdate",
      ["Ik open de pagina Windows Update.", "Klik op Naar updates zoeken.", "Staat er Nu opnieuw opstarten? Sla eerst je werk op."],
      ["I'll open Windows Update.", "Click Check for updates.", "Restart now? Save your work first."],
      update_huidig, update_acties),
    # ---- het Maatje opent de pagina en legt uit
    K("letters", ("Letters groter", "Bigger text"),
      ["letters", "tekst groter", "lettergrootte", "kan niet lezen", "te klein", "grotere letters", "text size", "bigger text"],
      "ms-settings:easeofaccess-display",
      ["Ik open de pagina Tekstgrootte.", "Schuif het balkje bij Tekstgrootte naar rechts. Bovenin zie je een voorbeeld.",
       "Klik daarna op Toepassen. Het scherm wordt even blauw, dat is normaal."],
      ["I'll open Text size.", "Move the slider right.", "Click Apply."]),
    K("wifi", ("Wifi en internet", "Wi-Fi and internet"),
      ["wifi", "wi-fi", "internet", "geen internet", "draadloos", "netwerk", "verbinding", "router"],
      "ms-settings:network-wifi",
      ["Ik open de pagina Wifi.", "Kijk of de schakelaar bij Wifi op Aan staat.", "Klik op Beschikbare netwerken weergeven en kies je eigen netwerk.",
       "Werkt het niet? Zet je modem en router 30 seconden uit, en weer aan."],
      ["I'll open Wi-Fi.", "Make sure Wi-Fi is On.", "Show available networks and pick yours.", "Still not? Restart your router."]),
    K("bluetooth", ("Bluetooth (koptelefoon, speaker)", "Bluetooth"),
      ["bluetooth", "koptelefoon", "oortjes", "headset", "draadloze", "speaker koppelen", "koppelen"],
      "ms-settings:bluetooth",
      ["Ik open de pagina Bluetooth.", "Zet Bluetooth op Aan.", "Zet je koptelefoon of speaker in koppel-stand (zie het boekje).",
       "Klik op Apparaat toevoegen, dan Bluetooth, en kies je apparaat."],
      ["I'll open Bluetooth.", "Turn it On.", "Put your device in pairing mode.", "Add device, Bluetooth, pick it."]),
    K("verwijderen", ("Programma verwijderen", "Uninstall a program"),
      ["verwijderen", "weghalen", "programma weg", "app verwijderen", "uninstall", "deinstalleren"],
      "ms-settings:appsfeatures",
      ["Ik open de pagina Geinstalleerde apps.", "Zoek het programma in de lijst.", "Klik op de drie puntjes ernaast, en dan op Verwijderen.",
       "Twijfel je of je het nodig hebt? Laat het dan staan, of vraag het iemand die je vertrouwt."],
      ["I'll open Installed apps.", "Find the program.", "Click the three dots, then Uninstall.", "In doubt? Leave it."]),
    K("helderheid", ("Scherm lichter of donkerder", "Screen brightness"),
      ["helderheid", "scherm lichter", "scherm donkerder", "te donker", "brightness", "fel"],
      "ms-settings:display",
      ["Ik open de pagina Beeldscherm.", "Bij Helderheid schuif je het balkje naar links of rechts.",
       "Staat er geen balkje? Dan heb je een losse monitor: gebruik dan de knopjes op het scherm zelf."],
      ["I'll open Display.", "Use the Brightness slider.", "No slider? Use the buttons on your monitor."]),
    K("nachtlampje", ("Nachtlampje (minder blauw licht)", "Night light"),
      ["nachtlampje", "nachtlicht", "blauw licht", "ogen moe", "avond", "night light"],
      "ms-settings:nightlight",
      ["Ik open de pagina Nachtlampje.", "Zet Nachtlampje op Aan. Het scherm wordt wat warmer van kleur.",
       "Je kunt het ook vanzelf laten aangaan, bijvoorbeeld van zonsondergang tot zonsopgang."],
      ["I'll open Night light.", "Turn it On.", "You can schedule it."]),
    K("slaapstand", ("Scherm gaat te snel uit", "Screen turns off too soon"),
      ["slaapstand", "scherm gaat uit", "gaat op zwart", "energie", "stroom", "sleep", "uit na", "steeds uit", "gaat steeds", "valt uit", "wordt zwart", "slapen"],
      "ms-settings:powersleep",
      ["Ik open de pagina Energie.", "Bij Scherm en slaapstand kies je hoe lang het duurt voordat het scherm uitgaat.",
       "Kies bijvoorbeeld 15 minuten."],
      ["I'll open Power.", "Under Screen and sleep, pick a longer time."]),
    K("meldingen", ("Minder meldingen en pop-ups", "Fewer notifications"),
      ["meldingen", "pop-up", "popup", "berichtjes", "notificaties", "storend", "notifications"],
      "ms-settings:notifications",
      ["Ik open de pagina Meldingen.", "Zet de schakelaar uit bij programma's waarvan je geen meldingen wilt.",
       "Of zet Niet storen aan."],
      ["I'll open Notifications.", "Turn off the ones you don't want.", "Or turn on Do not disturb."]),
    K("browser", ("Standaard internetprogramma kiezen", "Default browser"),
      ["standaard browser", "browser", "internetprogramma", "chrome", "edge", "firefox", "standaard apps"],
      "ms-settings:defaultapps",
      ["Ik open de pagina Standaard-apps.", "Zoek je browser in de lijst, bijvoorbeeld Chrome of Firefox, en klik erop.",
       "Klik bovenaan op Standaard instellen."],
      ["I'll open Default apps.", "Click your browser.", "Click Set default."]),
    K("datum", ("Datum en tijd", "Date and time"),
      ["datum", "tijd", "klok", "verkeerde tijd", "zomertijd", "date", "time"],
      "ms-settings:dateandtime",
      ["Ik open de pagina Datum en tijd.", "Zet Tijd automatisch instellen op Aan.", "Klik op Nu synchroniseren."],
      ["I'll open Date & time.", "Turn on Set time automatically.", "Click Sync now."]),
    K("beveiliging", ("Beveiliging (virusscanner, firewall)", "Security"),
      ["beveiliging", "virusscanner", "virus", "firewall", "defender", "veilig", "security", "antivirus"],
      "windowsdefender:",
      ["Ik open Windows-beveiliging.", "Staat alles op een groen vinkje? Dan is het goed.",
       "Zie je een geel of rood teken? Klik erop en volg de uitleg, of vraag iemand die je vertrouwt.",
       "De beveiliging verander ik nooit zelf. Dat is te belangrijk."],
      ["I'll open Windows Security.", "All green ticks? Good.", "Yellow or red? Click it, or ask someone you trust.",
       "I never change security myself."]),
]


def zoek_klus(klus_id):
    return next((k for k in KLUSJES if k["id"] == klus_id), None)


def titel(k, taal="nl"):
    return k["titel"][0 if taal == "nl" else 1]


def stappen(k, taal="nl"):
    return list(k["stappen"][0 if taal == "nl" else 1])


def huidig(k, taal="nl"):
    try:
        return k["huidig"](taal) if k.get("huidig") else ""
    except Exception as ex:
        return _t("Ik kon dit niet lezen (%s)." % ex, "I couldn't read this.", taal)


def acties(k, taal="nl"):
    try:
        return k["acties"](taal) if k.get("acties") else []
    except Exception:
        return []


def doe_actie(k, actie, bevestigd=False, taal="nl"):
    """Voert één actie uit, ALLEEN als de gebruiker op JA drukte."""
    if bevestigd is not True:
        return _klaar(_t("Dit verandert iets op je pc. Ik moet het je eerst vragen.", "This changes something. I have to ask first.", taal), False)
    try:
        return actie["doe"](taal)
    except Exception as ex:
        _logboek("%s: mislukt (%s)" % (k["id"], ex))
        return _klaar(_t("Het lukte niet: %s" % ex, "It didn't work: %s" % ex, taal), False)


def kan_terug(k):
    return bool(k.get("herstel")) and k["id"] in _terug_lees()


def terugzetten(k, bevestigd=False, taal="nl"):
    if bevestigd is not True:
        return _klaar(_t("Dit verandert iets op je pc. Ik moet het je eerst vragen.", "This changes something. I have to ask first.", taal), False)
    t = _terug_lees()
    if k["id"] not in t or not k.get("herstel"):
        return _klaar(_t("Er is niets om terug te zetten.", "There is nothing to undo.", taal), False)
    try:
        uitleg = k["herstel"](t[k["id"]]["oud"], taal)
    except Exception as ex:
        return _klaar(_t("Het lukte niet: %s" % ex, "It didn't work: %s" % ex, taal), False)
    del t[k["id"]]
    _terug_schrijf(t)
    _logboek("%s: teruggezet" % k["id"])
    return _klaar(_t("Klaar! ", "Done! ", taal) + uitleg)


STOP = {"niet", "mijn", "het", "een", "doet", "lukt", "gaat", "zijn", "wil", "kan", "ik", "de", "is", "te", "en", "van", "op", "met",
        "voor", "wat", "hoe", "waar", "meer", "geen", "the", "not", "my", "doesn", "work", "werkt", "nou", "nog", "ook", "maar"}


def zoek(tekst):
    """'mijn muis is te klein' -> [klusjes], beste eerst. Geen AI: woorden en lijkt-op (tikfoutjes mogen)."""
    t = re.sub(r"[^a-z0-9 \-]", " ", (tekst or "").lower())
    woorden = [w for w in t.split() if len(w) > 2 and w not in STOP]
    if not woorden:
        return []
    uit = []
    for k in KLUSJES:
        score = 0.0
        for z in k["zoek"] + [titel(k, "nl").lower(), titel(k, "en").lower()]:
            if " " in z and z in t:
                score = max(score, 1.2)                                # hele zin gevonden: sterkst
            elif z in woorden:
                score = max(score, 1.0)
            for w in woorden:
                for zw in z.split():
                    if len(zw) > 3 and len(w) > 3 and zw not in STOP:
                        r = difflib.SequenceMatcher(None, w, zw).ratio()
                        if r >= (0.87 if min(len(w), len(zw)) >= 6 else 0.9):
                            score = max(score, min(r, 0.95))
        if score >= 0.87:
            uit.append((score, k))
    return [k for _s, k in sorted(uit, key=lambda x: -x[0])]


if __name__ == "__main__":                                             # proef: alleen lezen en zoeken, NIETS veranderen
    for z in ("muis groter", "ik hoor niets", "pc is traag", "printer", "geen internet", "letters te klein", "virus", "wifi doet het niet"):
        print(z, "->", [titel(k) for k in zoek(z)][:3])
    for k in KLUSJES:
        if k.get("huidig"):
            print("*", titel(k), ":", huidig(k))
            print("   knoppen:", [a["label"] for a in acties(k)][:6], "| terug:", kan_terug(k))
