# -*- coding: utf-8 -*-
"""DraveHanden 0.1 - de gedeelde "handen" voor Visual Buddy, de ouderen-app en later de AI-agent.

Twee soorten hulpjes:
  1. KIJKEN (alleen lezen, mag altijd): schijf, geheugen, beveiliging, updates, opstart, rommel.
  2. DOEN (verandert iets): ALLEEN met bevestigd=True. Zonder dat doet het hulpje niets en zegt het
     dat het eerst moet vragen. Zo kan geen enkele knop of AI per ongeluk iets weghalen.

Regels (Dravenlock):
  - Opruimen gaat naar de PRULLENBAK waar het kan, dus het is terug te halen.
  - Alleen veilige rommel: tijdelijke bestanden, caches, crash-verslagjes, oude logjes.
    NOOIT documenten, foto's, persoonlijke mappen of het register.
  - Elke verandering komt in handen_logboek.txt naast de app (portable, niet in AppData).
  - Uitleg in gewone, korte taal, zodat Buddy het kan voorlezen.
Gebaseerd op de veilige onderdelen van DraveGuard (cleaner.py, security.py).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time

VERSIE = "0.1.3"
NO_WIN = getattr(subprocess, "CREATE_NO_WINDOW", 0)
GOED, LET_OP, SLECHT, ONBEKEND = "goed", "let_op", "slecht", "onbekend"


def _hier():
    return os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))


def _t(nl, en, taal):
    return nl if taal == "nl" else en


def bevinding(soort, status, titel, uitleg, advies="", wijzigt=False, extra=None):
    """Eén uitkomst. 'uitleg' is kort en gewoon, om voor te lezen."""
    return {"soort": soort, "status": status, "titel": titel, "uitleg": uitleg,
            "advies": advies, "wijzigt": wijzigt, "extra": extra or {}}


def mooi_getal(n):
    """1234567890 -> '1,1 GB' (Nederlandse komma)."""
    for eenheid in ("bytes", "KB", "MB", "GB", "TB"):
        if n < 1024 or eenheid == "TB":
            return ("%d %s" % (n, eenheid)) if eenheid == "bytes" else ("%.1f %s" % (n, eenheid)).replace(".", ",")
        n /= 1024.0


def _ps_json(cmd, timeout=40):
    """PowerShell (alleen lezen) -> dict. Bij fout: {}."""
    try:
        p = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command",
                            cmd + " | ConvertTo-Json -Compress"],
                           capture_output=True, text=True, timeout=timeout, creationflags=NO_WIN)
        return json.loads(p.stdout or "{}") or {}
    except Exception:
        return {}


def dagen_tekst(n):
    """0 -> 'vandaag', 1 -> 'gisteren', 5 -> '5 dagen geleden'."""
    return "vandaag" if n <= 0 else ("gisteren" if n == 1 else "%d dagen geleden" % n)


def logboek(regel):
    try:
        with open(os.path.join(_hier(), "handen_logboek.txt"), "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + regel + "\n")
    except Exception:
        pass


# =====================================================================  1. KIJKEN (alleen lezen)

def schijven():
    """Vaste schijven (geen usb-sticks of netwerk): [(letter, totaal, vrij)]."""
    uit = []
    try:
        import ctypes
        import shutil
        masker = ctypes.windll.kernel32.GetLogicalDrives()
        for i in range(26):
            if masker & (1 << i):
                letter = "%s:\\" % chr(65 + i)
                if ctypes.windll.kernel32.GetDriveTypeW(letter) == 3:      # 3 = vaste schijf
                    try:
                        g = shutil.disk_usage(letter)
                        uit.append((letter[:2], g.total, g.free))
                    except Exception:
                        pass
    except Exception:                                                  # geen Windows (proef)
        import shutil
        g = shutil.disk_usage("/")
        uit.append(("/", g.total, g.free))
    return uit


def kijk_schijven(taal="nl"):
    lijst = []
    for letter, totaal, vrij in schijven():
        vol = 100 - int(round(100.0 * vrij / max(1, totaal)))
        if vol >= 95:
            st, adv = SLECHT, _t("Ruim op of zet grote bestanden ergens anders neer.", "Clean up or move big files.", taal)
        elif vol >= 85:
            st, adv = LET_OP, _t("Bijna vol. Opruimen helpt.", "Almost full. Cleaning up helps.", taal)
        else:
            st, adv = GOED, ""
        naam = letter.rstrip(":")                                       # "C" leest beter voor dan "C:"
        uitleg = _t("Schijf %s is voor %d procent vol. Er is nog %s vrij." % (naam, vol, mooi_getal(vrij)),
                    "Drive %s is %d percent full. %s free." % (naam, vol, mooi_getal(vrij)), taal)
        lijst.append(bevinding("schijf", st, _t("Schijf %s", "Drive %s", taal) % letter.rstrip(":"), uitleg, adv,
                               extra={"vol_procent": vol, "vrij": vrij, "totaal": totaal}))
    return lijst


def kijk_geheugen(taal="nl"):
    try:
        import ctypes

        class MEM(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
        m = MEM()
        m.dwLength = ctypes.sizeof(MEM)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
        last, totaal = int(m.dwMemoryLoad), m.ullTotalPhys
    except Exception:
        return [bevinding("geheugen", ONBEKEND, _t("Werkgeheugen", "Memory", taal),
                          _t("Ik kon het werkgeheugen niet lezen.", "I could not read the memory.", taal))]
    st = SLECHT if last >= 90 else (LET_OP if last >= 80 else GOED)
    adv = _t("Sluit programma's die je niet gebruikt.", "Close programs you don't use.", taal) if st != GOED else ""
    return [bevinding("geheugen", st, _t("Werkgeheugen", "Memory", taal),
                      _t("Het werkgeheugen is voor %d procent in gebruik, van de %s." % (last, mooi_getal(totaal)),
                         "Memory is %d percent in use, of %s." % (last, mooi_getal(totaal)), taal), adv,
                      extra={"procent": last})]


def kijk_beveiliging(taal="nl"):
    """Virusscanner, virus-kennis (definities) en firewall. In één keer (sneller)."""
    d = _ps_json("$m = Get-MpComputerStatus -ErrorAction SilentlyContinue; "
                 "$f = @(Get-NetFirewallProfile -ErrorAction SilentlyContinue | ForEach-Object { $_.Enabled }); "
                 "@{ aan = $m.RealTimeProtectionEnabled; leeftijd = $m.AntivirusSignatureAge; "
                 "firewall = $f }")
    uit = []
    aan = d.get("aan")
    if aan is True:
        uit.append(bevinding("virus", GOED, _t("Virusscanner", "Virus scanner", taal),
                             _t("Je virusscanner staat aan. Goed zo.", "Your virus scanner is on. Good.", taal)))
    elif aan is False:
        uit.append(bevinding("virus", SLECHT, _t("Virusscanner", "Virus scanner", taal),
                             _t("Je virusscanner staat UIT.", "Your virus scanner is OFF.", taal),
                             _t("Zet Windows-beveiliging weer aan, of vraag iemand om hulp.",
                                "Turn Windows Security back on, or ask someone for help.", taal)))
    else:
        uit.append(bevinding("virus", ONBEKEND, _t("Virusscanner", "Virus scanner", taal),
                             _t("Ik kon de virusscanner niet lezen. Misschien gebruik je een andere.",
                                "I could not read the virus scanner. Maybe you use another one.", taal)))
    lf = d.get("leeftijd")
    if isinstance(lf, int):
        st = GOED if lf <= 3 else (LET_OP if lf <= 14 else SLECHT)
        wanneer = _t(dagen_tekst(lf), "%d day(s) ago" % lf, taal)
        uit.append(bevinding("virus_kennis", st, _t("Virus-kennis", "Virus definitions", taal),
                             _t("De virusscanner kreeg %s nieuwe kennis." % wanneer,
                                "The virus scanner was updated %s." % wanneer, taal),
                             "" if st == GOED else _t("Laat Windows Update zijn werk doen.", "Let Windows Update run.", taal)))
    fw = d.get("firewall")
    fw = fw if isinstance(fw, list) else ([fw] if fw is not None else [])
    fw = [x in (True, 1, "True", "1") for x in fw]                    # PowerShell geeft 1 = aan, 0 = uit
    if fw and all(fw):
        uit.append(bevinding("firewall", GOED, "Firewall",
                             _t("Je firewall staat aan. Die houdt indringers buiten.", "Your firewall is on.", taal)))
    elif fw:
        uit.append(bevinding("firewall", SLECHT, "Firewall",
                             _t("Je firewall staat (deels) uit.", "Your firewall is (partly) off.", taal) + "",
                             _t("Vraag iemand om hem weer aan te zetten.", "Ask someone to turn it back on.", taal)))
    return uit


def kijk_updates(taal="nl"):
    d = _ps_json("$h = Get-HotFix -ErrorAction SilentlyContinue | Where-Object InstalledOn | "
                 "Sort-Object InstalledOn -Descending | Select-Object -First 1; "
                 "@{ dagen = if ($h) { [int]((Get-Date) - $h.InstalledOn).TotalDays } else { -1 }; "
                 "herstart = (Test-Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\WindowsUpdate\\Auto Update\\RebootRequired') }")
    uit = []
    dagen = d.get("dagen", -1)
    if isinstance(dagen, int) and dagen >= 0:
        st = GOED if dagen <= 40 else (LET_OP if dagen <= 75 else SLECHT)
        uit.append(bevinding("updates", st, "Windows Update",
                             _t("De laatste Windows-update was %s." % dagen_tekst(dagen),
                                "The last Windows update was %d days ago." % dagen, taal),
                             "" if st == GOED else _t("Kijk bij Instellingen, Windows Update.", "Check Settings, Windows Update.", taal),
                             extra={"dagen": dagen}))
    else:
        uit.append(bevinding("updates", ONBEKEND, "Windows Update",
                             _t("Ik kon niet zien wanneer de laatste update was.", "I could not see the last update.", taal)))
    if d.get("herstart") is True:
        uit.append(bevinding("herstart", LET_OP, _t("Opnieuw opstarten", "Restart", taal),
                             _t("Windows wil opnieuw opstarten om een update af te maken.",
                                "Windows wants to restart to finish an update.", taal),
                             _t("Sla je werk op en start de pc opnieuw op.", "Save your work and restart.", taal)))
    return uit


def opstart_programmas():
    """Programma's die met Windows meestarten (alleen lezen)."""
    namen = []
    for sleutel in (r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
                    r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
                    r"HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run"):
        try:
            p = subprocess.run(["reg", "query", sleutel], capture_output=True, text=True, timeout=8, creationflags=NO_WIN)
        except Exception:
            continue
        for r in (p.stdout or "").splitlines():
            r = r.strip()
            if r and not r.startswith("HKEY") and "REG_" in r:
                namen.append(r.split(None, 1)[0])
    for map_ in (os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "Microsoft", "Windows", "Start Menu", "Programs", "Startup"),
                 os.path.join(os.environ.get("PROGRAMDATA", r"C:\ProgramData"), "Microsoft", "Windows", "Start Menu", "Programs", "StartUp")):
        if os.path.isdir(map_):
            namen += [os.path.splitext(f)[0] for f in os.listdir(map_) if f.lower() != "desktop.ini"]
    return namen


def kijk_opstart(taal="nl"):
    namen = opstart_programmas()
    n = len(namen)
    st = GOED if n <= 8 else (LET_OP if n <= 15 else SLECHT)
    return [bevinding("opstart", st, _t("Opstarten", "Startup", taal),
                      _t("Er starten %d programma's mee als de pc aangaat." % n,
                         "%d programs start with Windows." % n, taal),
                      "" if st == GOED else _t("Minder programma's laten meestarten maakt de pc sneller.",
                                               "Fewer startup programs make the pc faster.", taal),
                      extra={"namen": namen})]


# ---------- rommel: veilige categorieën (geen beheerder nodig)
def _u(*p):
    return os.path.join(os.path.expanduser("~"), *p)


def rommel_soorten():
    """(sleutel, naam_nl, naam_en, mappen, alleen_eindigend_op/beginnend_met, ouder_dan_dagen)."""
    temp = os.environ.get("TEMP", _u("AppData", "Local", "Temp"))
    la = _u("AppData", "Local")
    return [
        ("tijdelijk", "Tijdelijke bestanden", "Temporary files", [temp], (), 2),
        ("miniaturen", "Plaatjes-voorbeeldjes (miniaturen)", "Thumbnail cache",
         [os.path.join(la, "Microsoft", "Windows", "Explorer")], ("thumbcache_", "iconcache_"), 0),
        ("chrome", "Chrome tijdelijk geheugen", "Chrome cache",
         [os.path.join(la, "Google", "Chrome", "User Data", "Default", "Cache")], (), 0),
        ("edge", "Edge tijdelijk geheugen", "Edge cache",
         [os.path.join(la, "Microsoft", "Edge", "User Data", "Default", "Cache")], (), 0),
        ("crash", "Crash-verslagjes", "Crash dumps", [os.path.join(la, "CrashDumps")], (), 0),
        ("logjes", "Oude logjes", "Old log files", [temp], (".log",), 30),
    ]


def _rommel_bestanden(mappen, patronen, ouder_dan):
    grens = time.time() - ouder_dan * 86400
    for basis in mappen:
        if not basis or not os.path.isdir(basis):
            continue
        for map_, _d, bestanden in os.walk(basis):
            for b in bestanden:
                laag = b.lower()
                if patronen and not any(laag.endswith(p) or laag.startswith(p) for p in patronen):
                    continue
                pad = os.path.join(map_, b)
                try:
                    st = os.stat(pad)
                except Exception:
                    continue
                if ouder_dan and st.st_mtime > grens:
                    continue                                           # te nieuw: kan nog in gebruik zijn
                yield pad, st.st_size


def rommel_bekijken(taal="nl", soorten=None):
    """Alleen tellen. Geeft (totaal_bytes, [(sleutel, naam, aantal, bytes)])."""
    soorten = soorten or rommel_soorten()
    totaal, lijst = 0, []
    for sleutel, nl, en, mappen, pat, oud in soorten:
        n = b = 0
        for _p, sz in _rommel_bestanden(mappen, pat, oud):
            n += 1
            b += sz
        totaal += b
        lijst.append((sleutel, nl if taal == "nl" else en, n, b))
    return totaal, lijst


def kijk_rommel(taal="nl"):
    totaal, lijst = rommel_bekijken(taal)
    st = GOED if totaal < 500 * 1024 ** 2 else (LET_OP if totaal < 5 * 1024 ** 3 else SLECHT)
    return [bevinding("rommel", st, _t("Rommel", "Junk", taal),
                      _t("Er staat %s aan rommel die veilig weg mag." % mooi_getal(totaal),
                         "There is %s of junk that can safely go." % mooi_getal(totaal), taal),
                      "" if totaal < 50 * 1024 ** 2 else _t("Ik kan het opruimen. Ik vraag het je eerst.",
                                                           "I can clean it up. I'll ask you first.", taal),
                      extra={"bytes": totaal, "soorten": lijst})]


def pc_nakijken(taal="nl"):
    """Alles bij elkaar (alleen lezen). Geeft (samenvatting, [bevindingen])."""
    alles = []
    for f in (kijk_schijven, kijk_geheugen, kijk_beveiliging, kijk_updates, kijk_opstart, kijk_rommel):
        try:
            alles += f(taal)
        except Exception as ex:
            alles.append(bevinding(f.__name__, ONBEKEND, f.__name__, _t("Dit lukte niet: %s", "This failed: %s", taal) % ex))
    slecht = [b for b in alles if b["status"] == SLECHT]
    let_op = [b for b in alles if b["status"] == LET_OP]
    if slecht:
        sv = _t("Ik heb je pc nagekeken. Er is %d ding dat echt aandacht nodig heeft" % len(slecht),
                "I checked your pc. %d thing really needs attention" % len(slecht), taal)
        sv += _t(", en %d om op te letten." % len(let_op), ", and %d to keep an eye on." % len(let_op), taal) if let_op else "."
    elif let_op:
        if len(let_op) == 1:
            sv = _t("Ik heb je pc nagekeken. Hij is gezond, maar er is 1 ding om op te letten.",
                    "I checked your pc. It's healthy, but there is 1 thing to keep an eye on.", taal)
        else:
            sv = _t("Ik heb je pc nagekeken. Hij is gezond, maar er zijn %d dingen om op te letten." % len(let_op),
                    "I checked your pc. It's healthy, but there are %d things to keep an eye on." % len(let_op), taal)
    else:
        sv = _t("Ik heb je pc nagekeken. Alles ziet er goed uit!", "I checked your pc. Everything looks good!", taal)
    if slecht and taal == "nl" and len(slecht) > 1:
        sv = sv.replace("ding dat echt aandacht nodig heeft", "dingen die echt aandacht nodig hebben")
    return sv, alles


# =====================================================================  2. DOEN (alleen met bevestigd=True)

def _niet_bevestigd(taal):
    return {"gedaan": False, "uitleg": _t("Dit verandert iets op je pc. Ik moet het je eerst vragen.",
                                          "This changes something on your pc. I have to ask you first.", taal)}


def ruim_op(bevestigd=False, taal="nl", soorten=None):
    """Ruimt de veilige rommel op. Naar de prullenbak als dat kan (terug te halen).
    Bestanden die nog in gebruik zijn, slaat hij gewoon over."""
    if bevestigd is not True:
        return _niet_bevestigd(taal)
    try:
        from send2trash import send2trash
    except Exception:
        send2trash = None
    soorten = soorten or rommel_soorten()
    weg = vrij = overgeslagen = 0
    for sleutel, nl, en, mappen, pat, oud in soorten:
        for pad, sz in list(_rommel_bestanden(mappen, pat, oud)):
            try:
                if send2trash:
                    send2trash(pad)                                    # naar de prullenbak: terug te halen
                else:
                    os.remove(pad)                                     # geen prullenbak-hulpje: dan gewoon weg
                weg += 1
                vrij += sz
            except Exception:
                overgeslagen += 1                                      # in gebruik of geen rechten: laten staan
    logboek("RUIM_OP: %d bestanden, %s vrij, %d overgeslagen" % (weg, mooi_getal(vrij), overgeslagen))
    uitleg = _t("Klaar! Ik heb %s opgeruimd." % mooi_getal(vrij), "Done! I cleaned up %s." % mooi_getal(vrij), taal)
    if overgeslagen:
        uitleg += _t(" %d bestandjes waren nog in gebruik, die heb ik laten staan." % overgeslagen,
                     " %d files were still in use, I left them." % overgeslagen, taal)
    return {"gedaan": True, "uitleg": uitleg, "bestanden": weg, "bytes": vrij, "overgeslagen": overgeslagen}


def prullenbak_grootte():
    """Hoeveel staat er in de prullenbak? (bytes, aantal) of (None, None)."""
    try:
        import ctypes

        class INFO(ctypes.Structure):
            _fields_ = [("cbSize", ctypes.c_ulong), ("i64Size", ctypes.c_longlong), ("i64NumItems", ctypes.c_longlong)]
        info = INFO()
        info.cbSize = ctypes.sizeof(INFO)
        if ctypes.windll.shell32.SHQueryRecycleBinW(None, ctypes.byref(info)) == 0:
            return info.i64Size, info.i64NumItems
    except Exception:
        pass
    return None, None


def leeg_prullenbak(bevestigd=False, taal="nl"):
    """LET OP: dit is voorgoed weg. Alleen na een duidelijke vraag mét die waarschuwing."""
    if bevestigd is not True:
        r = _niet_bevestigd(taal)
        r["uitleg"] += _t(" Wat uit de prullenbak gaat, is voorgoed weg.", " What leaves the recycle bin is gone for good.", taal)
        return r
    groot, aantal = prullenbak_grootte()
    try:
        import ctypes
        res = ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0x1 | 0x2 | 0x4)
        ok = res in (0, -2147418113)
    except Exception:
        ok = False
    logboek("LEEG_PRULLENBAK: %s (%s items, %s)" % ("ok" if ok else "mislukt", aantal, mooi_getal(groot or 0)))
    return {"gedaan": ok, "uitleg": _t("De prullenbak is leeg." if ok else "Het legen lukte niet.",
                                       "The recycle bin is empty." if ok else "Emptying failed.", taal)}


# =====================================================================  proef
if __name__ == "__main__":
    taal = "en" if "--en" in sys.argv else "nl"
    samen, lijst = pc_nakijken(taal)
    teken = {GOED: "[goed]   ", LET_OP: "[let op] ", SLECHT: "[SLECHT] ", ONBEKEND: "[?]      "}
    print("DraveHanden %s - pc nakijken (alleen lezen)\n" % VERSIE)
    sys.stdout.flush()
    for b in lijst:
        print(teken[b["status"]] + b["titel"] + ": " + b["uitleg"] + ((" -> " + b["advies"]) if b["advies"] else ""))
    print("\n" + samen)
    g, a = prullenbak_grootte()
    if g is not None:
        print("Prullenbak: %s items, %s" % (a, mooi_getal(g)))
