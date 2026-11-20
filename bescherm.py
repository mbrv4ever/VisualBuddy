# -*- coding: utf-8 -*-
"""DraveHanden - bescherm 0.1: het Maatje als waakhond tegen oplichters.

  1. meekijk()          - staat of draait er een programma waarmee iemand op afstand in je pc kan?
                          (AnyDesk, TeamViewer, NetSupport ... - oplichters laten je die installeren)
     stop_meekijken()   - na JA: zet de draaiende meekijk-programma's uit
  2. bericht(tekst)     - is deze mail / sms / WhatsApp echt? (de bekende trucjes, in gewone taal)
  3. link(adres)        - is deze website te vertrouwen? (nep-namen, rare extensies, verkorte links)
  4. GOUDEN_REGELS      - om voor te lezen

Alles gebeurt op je eigen pc. Er gaat niets naar internet. Het Maatje kan het nooit 100% zeker weten,
en zegt dat ook eerlijk: bij twijfel bel je de afzender zelf, via een nummer dat je zelf opzoekt.
"""
from __future__ import annotations

import difflib
import os
import re
import subprocess
import sys
import time
from urllib.parse import urlsplit

VERSIE = "0.3"
NO_WIN = getattr(subprocess, "CREATE_NO_WINDOW", 0)
GOED, LET_OP, SLECHT = "goed", "let_op", "slecht"


def _hier():
    return os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))


def _logboek(regel):
    try:
        with open(os.path.join(_hier(), "handen_logboek.txt"), "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + regel + "\n")
    except Exception:
        pass


# =====================================================================  1. meekijk-alarm
# naam, programma-bestanden (kleine letters), woorden in de naam van het geinstalleerde programma
MEEKIJKERS = [
    ("AnyDesk", ["anydesk.exe"], ["anydesk"]),
    ("TeamViewer", ["teamviewer.exe", "teamviewer_service.exe", "tv_w32.exe", "tv_x64.exe"], ["teamviewer"]),
    ("RustDesk", ["rustdesk.exe"], ["rustdesk"]),
    ("UltraViewer", ["ultraviewer_desktop.exe", "ultraviewer_service.exe"], ["ultraviewer"]),
    ("NetSupport", ["client32.exe", "pcicfgui.exe"], ["netsupport"]),
    ("ScreenConnect / ConnectWise", ["screenconnect.clientservice.exe", "screenconnect.windowsclient.exe"], ["screenconnect", "connectwise control"]),
    ("Supremo", ["supremo.exe", "supremoservice.exe"], ["supremo"]),
    ("LogMeIn", ["logmein.exe", "lmiguardiansvc.exe"], ["logmein"]),
    ("GoTo / GoToAssist", ["g2ax_comm_customer.exe", "gotoassist.exe"], ["gotoassist", "goto resolve"]),
    ("Splashtop", ["srservice.exe", "strwinclt.exe"], ["splashtop"]),
    ("Ammyy Admin", ["aa_v3.exe", "ammyy_admin.exe"], ["ammyy"]),
    ("AeroAdmin", ["aeroadmin.exe"], ["aeroadmin"]),
    ("RemotePC", ["remotepcservice.exe", "remotepcdesktop.exe"], ["remotepc"]),
    ("Zoho Assist", ["zohoassist.exe", "zaservice.exe"], ["zoho assist"]),
    ("Remote Utilities", ["rutserv.exe", "rfusclient.exe"], ["remote utilities"]),
    ("HopToDesk", ["hoptodesk.exe"], ["hoptodesk"]),
    ("Getscreen", ["getscreen.exe"], ["getscreen"]),
    ("Iperius Remote", ["iperiusremote.exe"], ["iperius remote"]),
    ("Radmin", ["rserver3.exe", "radmin.exe"], ["radmin"]),
    ("DWService", ["dwagent.exe", "dwagsvc.exe"], ["dwagent", "dwservice"]),
    ("SimpleHelp", ["remote access.exe", "simplehelp.exe"], ["simplehelp"]),
    ("Atera", ["ateraagent.exe"], ["atera"]),
    ("VNC", ["winvnc.exe", "tvnserver.exe", "vncserver.exe", "uvnc_service.exe"], ["vnc server", "tightvnc", "ultravnc", "realvnc"]),
    ("Chrome Extern bureaublad", ["remoting_host.exe"], ["chrome remote desktop"]),
    ("Snelle hulp (Quick Assist)", ["quickassist.exe"], []),          # zit in Windows; alleen als hij NU draait
]


def _draaiend():
    """Namen (klein) van de programma's die nu draaien."""
    try:
        r = subprocess.run(["tasklist", "/fo", "csv", "/nh"], capture_output=True, text=True, timeout=20, creationflags=NO_WIN)
        return {regel.split('","')[0].strip('"').lower() for regel in (r.stdout or "").splitlines() if regel.strip()}
    except Exception:
        return set()


def _geinstalleerd():
    """Namen (klein) van geinstalleerde programma's (Programma's en onderdelen)."""
    namen = set()
    try:
        import winreg
    except Exception:
        return namen
    for hive, pad in ((winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
                      (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
                      (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")):
        try:
            with winreg.OpenKey(hive, pad) as k:
                for i in range(winreg.QueryInfoKey(k)[0]):
                    try:
                        with winreg.OpenKey(k, winreg.EnumKey(k, i)) as s:
                            namen.add(str(winreg.QueryValueEx(s, "DisplayName")[0]).lower())
                    except OSError:
                        pass
        except OSError:
            pass
    return namen


def _extern_bureaublad_aan():
    """Staat 'Extern bureaublad' van Windows zelf aan?"""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Terminal Server") as k:
            return int(winreg.QueryValueEx(k, "fDenyTSConnections")[0]) == 0
    except Exception:
        return False


def meekijk(taal="nl"):
    """Geeft (samenvatting, [bevindingen], [draaiende programma-bestanden])."""
    nl = taal == "nl"
    draait, staat = _draaiend(), _geinstalleerd()
    uit, nu = [], []
    for naam, exes, woorden in MEEKIJKERS:
        actief = [e for e in exes if e in draait]
        aanwezig = any(w in g for w in woorden for g in staat)
        if actief:
            nu += actief
            uit.append({"status": SLECHT, "titel": naam,
                        "uitleg": ("%s DRAAIT NU. Daarmee kan iemand op afstand in je pc kijken en dingen doen." % naam) if nl
                        else "%s is RUNNING NOW. Someone could be watching and controlling your pc." % naam,
                        "advies": ("Heeft iemand je gebeld en gevraagd dit te openen? Dan is het bijna zeker een oplichter. "
                                   "Druk op Stop het meekijken, of trek de internetkabel eruit. Bel daarna je bank als je iets hebt ingetypt.") if nl
                        else "Did someone call and ask you to open this? It's almost certainly a scammer. Press Stop, or unplug the internet."})
        elif aanwezig:
            uit.append({"status": LET_OP, "titel": naam,
                        "uitleg": ("%s staat op je pc. Daarmee kan iemand op afstand in je pc, als jij het opent." % naam) if nl
                        else "%s is installed. With it someone can get into your pc remotely, if you open it." % naam,
                        "advies": ("Heb je dit zelf laten installeren door iemand die je echt kent en vertrouwt? Dan is het goed. "
                                   "Zo niet: laat het verwijderen, en open het nooit voor iemand die je belt.") if nl
                        else "Did someone you really know and trust install it? Fine. If not: have it removed."})
    if _extern_bureaublad_aan():
        uit.append({"status": LET_OP, "titel": "Extern bureaublad (Windows)" if nl else "Remote Desktop (Windows)",
                    "uitleg": "Extern bureaublad van Windows staat aan." if nl else "Windows Remote Desktop is on.",
                    "advies": "Gebruik je dat niet zelf? Laat het dan uitzetten." if nl else "Not using it? Have it turned off."})
    if any(b["status"] == SLECHT for b in uit):
        sv = "PAS OP! Er draait NU een programma waarmee iemand in je pc kan meekijken." if nl \
            else "CAREFUL! A program is running NOW that lets someone watch your pc."
    elif uit:
        sv = "Er kijkt nu niemand mee. Maar er staan programma's op je pc waarmee het zou kunnen." if nl \
            else "Nobody is watching now. But there are programs on your pc that could allow it."
    else:
        sv = "Goed zo: ik vind geen programma's waarmee iemand op afstand in je pc kan." if nl \
            else "Good: I find no programs that let someone into your pc remotely."
    return sv, uit, sorted(set(nu))


def stop_meekijken(bevestigd=False, taal="nl"):
    """Na JA: zet de draaiende meekijk-programma's uit. Lukt het niet (diensten van het systeem)? Dan zeggen we dat eerlijk."""
    nl = taal == "nl"
    if bevestigd is not True:
        return {"gedaan": False, "uitleg": "Dit verandert iets op je pc. Ik moet het je eerst vragen." if nl
                else "This changes something on your pc. I have to ask you first."}
    _sv, _l, nu = meekijk(taal)
    if not nu:
        return {"gedaan": True, "uitleg": "Er draait geen meekijk-programma meer." if nl else "No remote program is running."}
    gestopt, mislukt = [], []
    for exe in nu:
        try:
            r = subprocess.run(["taskkill", "/f", "/im", exe], capture_output=True, text=True, timeout=20, creationflags=NO_WIN)
            (gestopt if r.returncode == 0 else mislukt).append(exe)
        except Exception:
            mislukt.append(exe)
    _logboek("STOP_MEEKIJKEN: gestopt %s, mislukt %s" % (gestopt, mislukt))
    if mislukt:
        return {"gedaan": bool(gestopt), "uitleg": ("Ik kon niet alles stoppen (%s). Trek nu de internetkabel eruit of zet de wifi uit, "
                                                    "en vraag iemand die je vertrouwt om hulp." % ", ".join(mislukt)) if nl
                else "I couldn't stop everything. Unplug the internet now and ask someone you trust for help."}
    return {"gedaan": True, "uitleg": ("Klaar. Ik heb het meekijken gestopt. Heb je iets ingetypt of betaald terwijl er iemand meekeek? "
                                       "Bel dan meteen je bank, via het nummer op je bankpas.") if nl
            else "Done. I stopped the remote access. Did you type or pay anything? Call your bank right away."}


# =====================================================================  2. bericht-controle
# (soort, woorden/patronen, gewicht, uitleg NL, uitleg EN)
# (soort, STERK: zinnen die op JOU gericht zijn, ZWAK: losse woorden die ook in gewone mail/kranten staan, gewicht, uitleg NL, uitleg EN)
# 0.3: losse woorden alleen tellen ze nog licht mee (en alleen 2 of meer verschillende), en we zeggen altijd WAT we zagen.
TRUCJES = [
    ("haast",
     [r"binnen \d+ ?uur", r"(wordt|is|worden) (uw|je|jouw) .{0,40}(geblokkeerd|opgeschort|afgesloten|verwijderd|stopgezet)",
      r"laatste (kans|herinnering|waarschuwing|aanmaning)", r"vandaag nog (betalen|reageren|inloggen|bevestigen)", r"\bspoed",
      r"zo snel mogelijk (betalen|reageren|inloggen|bevestigen)", r"within \d+ hours", r"account (will be|has been) (suspended|locked)"],
     [r"onmiddellijk", r"verloopt", r"dringend", r"geblokkeerd", r"urgent"],
     2, "Er wordt haast gemaakt. Oplichters willen dat je snel handelt, zonder na te denken.",
     "It pushes you to hurry. Scammers want you to act fast without thinking."),
    ("geld",
     [r"erfenis", r"loterij", r"\b(u|je|jij) (heeft|hebt) .{0,40}gewonnen", r"\bprins\w*\b.{0,120}\b(met u|met je|aan u|aan je|voor u|voor je)\b.{0,40}(delen|geven|sturen)", r"\b(u|je) .{0,30}(erven|erft)\b",
      r"gratis geld", r"(miljoen|million) .{0,15}(dollar|euro|usd|pond).{0,120}\b(u|je|jou|you)\b", r"inheritance", r"lottery",
      r"you (have|ha\'?ve) won", r"gegarandeerd rendement", r"verdubbel (uw|je) geld"],
     [r"\bmiljoen", r"\bbitcoin", r"\bcrypto", r"rendement", r"fortuin", r"gewonnen"],
     3, "Je krijgt zomaar geld, een prijs of een erfenis beloofd. Dat is bijna altijd nep.",
     "You're promised money, a prize or an inheritance. That's almost always fake."),
    ("gegevens",
     [r"pincode", r"\bpin\b", r"wachtwoord", r"verifi[eë]er (uw|je|hier)", r"bevestig (uw|je) (gegevens|identiteit|account|rekening)",
      r"betaalpas .{0,25}(op)?sturen", r"(sms|beveiligings|verificatie|controle)-?code .{0,20}(door|geven|sturen|invullen)",
      r"stuur (uw|je) (iban|bsn|paspoort|identiteitsbewijs)", r"password", r"verify your (account|identity)", r"\bpin code"],
     [r"\binlog", r"\blog (hier )?in\b", r"\bdigid\b", r"\biban\b", r"\bbsn\b"],
     3, "Er wordt gevraagd om je pincode, wachtwoord, code of gegevens. Een echte bank of instantie vraagt dat NOOIT via een bericht.",
     "It asks for your pin, password, code or details. A real bank never asks that in a message."),
    ("betalen",
     [r"betaalverzoek", r"openstaande? (factuur|bedrag|betaling|rekening)", r"achterstand", r"deurwaarder", r"\bboete\b",
      r"incasso .{0,25}(mislukt|teruggestort|niet gelukt)", r"betaal .{0,40}(via|op) (de |deze |onderstaande )?(link|knop)",
      r"(maak|stort) .{0,30}over (naar|op)", r"\bbetaal (€ ?)?\d", r"\bbetaal .{0,20}(verzendkosten|kosten)", r"payment (failed|request)", r"overdue"],
     [r"\bbetaal\b", r"€\s?\d", r"\d+[,.]\d{2} ?(euro|eur)\b", r"\btikkie"],
     2, "Er wordt om geld of een betaling gevraagd. Controleer dat altijd eerst zelf, via de echte website of het echte nummer.",
     "It asks for money or a payment. Always check it yourself first."),
    ("familie",
     [r"hoi (mam|pap|ma|pa|oma|opa)\b.{0,60}(nummer|telefoon)", r"nieuw(e)? nummer", r"telefoon (is )?(kapot|stuk|gevallen)",
      r"dit is mijn nieuwe", r"kun je .{0,25}(voor me )?(betalen|overmaken|voorschieten)", r"hi mum", r"new number"],
     [],
     5, "Dit lijkt op het 'Hoi mam, nieuw nummer'-trucje. Bel je kind of kleinkind op het OUDE nummer, voordat je iets doet.",
     "This looks like the 'Hi mum, new number' trick. Call your child on their OLD number first."),
    ("helpdesk",
     [r"virus (gevonden|gedetecteerd|aangetroffen)", r"(uw|je) (computer|pc|laptop) is (besmet|ge[iï]nfecteerd|gehackt)",
      r"bel (\w+ )?(dit|ons|het volgende|onderstaand) nummer", r"(installeer|download|open) (anydesk|teamviewer|quick ?support)",
      r"your computer is infected", r"call (this|our) number"],
     [r"\bmicrosoft\b", r"helpdesk", r"anydesk", r"teamviewer"],
     5, "Een 'helpdesk' meldt een probleem met je pc of wil dat je belt of een programma installeert. Microsoft belt of mailt je NOOIT zelf over virussen.",
     "A 'helpdesk' reports a pc problem or wants you to call or install something. Microsoft NEVER does that."),
    ("pakket",
     [r"pakket.{0,40}(niet|kon niet|kan niet) (worden )?(bezorgd|geleverd|afgeleverd)", r"(verzendkosten|douanekosten|inklaringskosten).{0,40}(betalen|voldoen)",
      r"parcel .{0,30}(could not|cannot) be delivered"],
     [r"\bpakket", r"bezorg", r"douane", r"zending"],
     1, "Het gaat over een pakketje dat niet bezorgd kon worden, of kosten. Nep-pakketberichten zijn heel gewoon. Verwacht je echt iets? Kijk op de site van de vervoerder zelf.",
     "A parcel that couldn't be delivered, or fees. Fake parcel messages are very common."),
    ("aanhef",
     [r"beste klant", r"geachte (klant|heer/mevrouw|heer of mevrouw)", r"dear (customer|user|client)", r"beste gebruiker"],
     [],
     1, "Je wordt niet bij je naam genoemd ('Beste klant'). Echte bedrijven kennen meestal je naam.",
     "You're not addressed by name ('Dear customer')."),
]
VERKORT = ("bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd", "cutt.ly", "rebrand.ly", "shorturl.at", "rb.gy", "t.ly", "tiny.cc", "ow.ly")

ECHT = {"ing": "ing.nl", "rabobank": "rabobank.nl", "abn amro": "abnamro.nl", "abnamro": "abnamro.nl", "sns": "snsbank.nl",
        "asn": "asnbank.nl", "regiobank": "regiobank.nl", "knab": "knab.nl", "bunq": "bunq.com", "triodos": "triodos.nl",
        "digid": "digid.nl", "belastingdienst": "belastingdienst.nl", "mijnoverheid": "mijnoverheid.nl", "postnl": "postnl.nl",
        "dhl": "dhl.nl", "ziggo": "ziggo.nl", "kpn": "kpn.com", "odido": "odido.nl", "vodafone": "vodafone.nl", "bol.com": "bol.com",
        "marktplaats": "marktplaats.nl", "paypal": "paypal.com", "microsoft": "microsoft.com", "apple": "apple.com",
        "netflix": "netflix.com", "svb": "svb.nl", "uwv": "uwv.nl", "cjib": "cjib.nl", "toeslagen": "toeslagen.nl", "ns": "ns.nl",
        "albert heijn": "ah.nl", "coolblue": "coolblue.nl", "google": "google.com", "whatsapp": "whatsapp.com", "facebook": "facebook.com",
        "zilveren kruis": "zilverenkruis.nl", "cz": "cz.nl", "vgz": "vgz.nl", "menzis": "menzis.nl", "essent": "essent.nl",
        "eneco": "eneco.nl", "vattenfall": "vattenfall.nl", "thuisbezorgd": "thuisbezorgd.nl", "amazon": "amazon.nl"}
OFFICIEEL = set(ECHT.values()) | {"rijksoverheid.nl", "overheid.nl", "dhl.com", "amazon.com", "amazon.de", "google.nl", "live.com",
                                  "outlook.com", "office.com", "icloud.com", "youtube.com", "instagram.com", "nu.nl", "nos.nl"}


def _links(tekst):
    return re.findall(r"(?:https?://|www\.)[^\s<>\"')\]]+|\b[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:nl|com|net|org|info|xyz|top|shop|online|site|"
                      r"live|icu|click|buzz|app|eu|be|de|me|co|io|ly|gd|at|cc)(?:/[^\s<>\"')\]]*)?", tekst, flags=re.I)


def _zag(m, tekst):
    """Het stukje tekst dat we zagen, kort, om eerlijk te laten zien WAAROM."""
    g = tekst[m.start():m.end()].strip()
    return g if len(g) <= 60 else g[:57] + "..."


def bericht(tekst, taal="nl", merk_check=True):
    """Beoordeelt een geplakte mail/sms. Geeft {'oordeel', 'status', 'redenen': [..], 'advies', 'punten', 'sterk': [soorten]}."""
    nl = taal == "nl"
    t = (tekst or "").lower()
    if len(t.strip()) < 10:
        return {"status": LET_OP, "oordeel": "Plak eerst het hele bericht in het vak." if nl else "Paste the whole message first.",
                "redenen": [], "advies": "", "punten": 0, "sterk": []}
    punten, redenen, sterk, zwak_gezien = 0, [], [], []
    for soort, sterke, zwakke, gewicht, u_nl, u_en in TRUCJES:
        m = next((m for m in (re.search(p, t) for p in sterke) if m), None)
        if m:
            punten += gewicht
            sterk.append(soort)
            redenen.append(("%s (Ik zag: \"%s\")" % (u_nl, _zag(m, tekst))) if nl else "%s (I saw: \"%s\")" % (u_en, _zag(m, tekst)))
        else:
            for p in zwakke:
                mz = re.search(p, t)
                if mz:
                    zwak_gezien.append(_zag(mz, tekst))
                    break
    if len(zwak_gezien) >= 3:                                         # alleen bij veel verschillende losse woorden: licht meetellen
        punten += 1
        redenen.append(("Er staan een paar woorden in die oplichters ook vaak gebruiken, maar dat kan ook gewoon zijn. (Ik zag: %s)"
                        % ", ".join('"%s"' % z for z in zwak_gezien[:4])) if nl
                       else "There are some words scammers also use, but that can be normal. (I saw: %s)" % ", ".join(zwak_gezien[:4]))
    links = _links(tekst)
    for l in links:
        dom = _domein(l)
        if any(dom == v or dom.endswith("." + v) for v in VERKORT):
            punten += 2
            redenen.append(("Er staat een verkorte link in (%s). Daarmee verstoppen oplichters waar je echt naartoe gaat." % dom) if nl
                           else "There's a shortened link (%s). Scammers use these to hide where you really go." % dom)
            break
    begin = t[:400]                                                    # 0.3: alleen het begin, en niet bij lange nieuwsbrieven
    for merk, echt in (ECHT.items() if merk_check and len(t) < 1500 else []):  # noemt de ING, maar de link gaat ergens anders heen?
        if len(merk) >= 3 and re.search(r"\b%s\b" % re.escape(merk), begin) and links:
            vreemd = [_domein(l) for l in links if not _is_van(_domein(l), echt) and _domein(l) not in VERKORT]
            if vreemd:
                punten += 3
                redenen.append(("Het bericht noemt %s, maar de link gaat naar %s. De echte site is %s." % (merk.upper() if len(merk) <= 4 else merk.title(), vreemd[0], echt)) if nl
                               else "It mentions %s, but the link goes to %s. The real site is %s." % (merk, vreemd[0], echt))
                break
    for l in links:
        r = link(l, taal)
        if r["status"] == SLECHT:
            punten += 2
            redenen.append(("De link %s ziet er verdacht uit: %s" % (_domein(l), r["redenen"][0])) if nl and r["redenen"]
                           else "The link %s looks suspicious." % _domein(l))
            break
    if punten >= 5:
        st, oordeel = SLECHT, ("GEVAARLIJK: dit is bijna zeker oplichting." if nl else "DANGEROUS: this is almost certainly a scam.")
        advies = ("Klik nergens op, betaal niets, en geef geen gegevens. Gooi het bericht weg. Twijfel je toch? Bel de afzender zelf, "
                  "via een nummer dat JIJ opzoekt (bijvoorbeeld op je bankpas), niet het nummer uit het bericht.") if nl \
            else "Don't click, pay or share anything. Delete it. In doubt? Call the sender yourself via a number YOU look up."
    elif punten >= 2:
        st, oordeel = LET_OP, ("LET OP: dit kan echt zijn, maar er zit iets in dat oplichters ook vaak gebruiken. Controleer het eerst zelf."
                               if nl else "CAREFUL: this may be real, but it has something scammers often use too. Check it yourself first.")
        advies = ("Klik nog niet. Controleer het eerst zelf: ga zelf naar de echte website, of bel het echte nummer.") if nl \
            else "Don't click yet. Check it yourself first via the real website or number."
    else:
        st, oordeel = GOED, ("Ik zie geen bekende oplichterstrucjes. Maar helemaal zeker weten kan ik het nooit." if nl
                             else "I see no known scam tricks. But I can never be completely sure.")
        advies = ("Twijfel je toch? Bel de afzender zelf, via een nummer dat je zelf opzoekt.") if nl \
            else "Still in doubt? Call the sender via a number you look up yourself."
    if st == GOED:
        redenen = []                                                   # groen: geen losse "redenen" die verwarren
    return {"status": st, "oordeel": oordeel, "redenen": redenen, "advies": advies, "punten": punten, "sterk": sterk}


# =====================================================================  3. link-controle
RARE_EXT = (".xyz", ".top", ".icu", ".click", ".shop", ".online", ".site", ".live", ".buzz", ".rest", ".cfd", ".sbs", ".monster",
            ".work", ".cyou", ".support", ".help", ".loan", ".win", ".bid", ".ga", ".tk", ".ml", ".cf", ".gq")


def _domein(adres):
    a = (adres or "").strip().lower()
    if not re.match(r"^[a-z]+://", a):
        a = "http://" + a
    try:
        h = urlsplit(a).hostname or ""
    except Exception:
        h = ""
    return h[4:] if h.startswith("www.") else h


def _is_van(dom, echt):
    return dom == echt or dom.endswith("." + echt)


def _hoofd(dom):
    """'inloggen.ing.nl' -> 'ing.nl' (de laatste twee stukjes)."""
    d = dom.split(".")
    return ".".join(d[-2:]) if len(d) >= 2 else dom


def link(adres, taal="nl"):
    """Beoordeelt een websiteadres. Geeft {'status', 'oordeel', 'redenen', 'advies', 'domein'}."""
    nl = taal == "nl"
    ruw = (adres or "").strip()
    dom = _domein(ruw)
    if not dom or "." not in dom:
        return {"status": LET_OP, "oordeel": "Plak eerst een websiteadres in het vak." if nl else "Paste a web address first.",
                "redenen": [], "advies": "", "domein": dom}
    redenen, punten = [], 0
    hoofd = _hoofd(dom)
    if hoofd in OFFICIEEL:
        return {"status": GOED, "domein": dom, "redenen": [],
                "oordeel": ("Dit is de echte website van %s." % hoofd) if nl else "This is the real website of %s." % hoofd,
                "advies": ("Let wel op dat je het adres goed hebt overgenomen. Typ het bij twijfel zelf in.") if nl
                else "Make sure you copied it right. In doubt, type it yourself."}
    if re.match(r"^\d+\.\d+\.\d+\.\d+$", dom):
        punten += 3; redenen.append("Het adres is alleen een getal (IP-adres). Echte bedrijven gebruiken een naam." if nl else "The address is just a number.")
    if "xn--" in dom:
        punten += 4; redenen.append("Het adres gebruikt nep-letters die op gewone letters lijken." if nl else "It uses look-alike letters.")
    if "@" in ruw.split("//")[-1].split("/")[0]:
        punten += 3; redenen.append("Er staat een @ in het adres. Daarmee wordt verstopt waar je echt heen gaat." if nl else "There's an @ hiding the real address.")
    if any(dom == v or dom.endswith("." + v) for v in VERKORT):
        punten += 2; redenen.append("Dit is een verkorte link. Je kunt niet zien waar hij echt heen gaat." if nl else "This is a shortened link.")
    if dom.endswith(RARE_EXT):
        punten += 2; redenen.append(("Het adres eindigt op %s. Dat gebruiken oplichters veel, echte Nederlandse bedrijven bijna nooit." % ("." + dom.rsplit(".", 1)[-1])) if nl
                                    else "The ending is often used by scammers.")
    if ruw.lower().startswith("http://"):
        punten += 1; redenen.append("De verbinding is niet beveiligd (geen slotje, geen https)." if nl else "The connection is not secure (no https).")
    if not redenen and (dom.count("-") >= 2 or len(dom.split(".")) >= 4):
        punten += 1; redenen.append("Het adres is lang en rommelig, met veel streepjes of puntjes." if nl else "The address is long and messy.")
    # bekende naam erin, maar niet de echte site ("rabobank-veilig-inloggen.nl")
    for merk, echt in ECHT.items():
        m = merk.replace(" ", "")
        if len(m) >= 4 and m in dom.replace("-", "").replace(".", "") and not _is_van(dom, echt):
            punten += 4
            redenen.insert(0, ("Het adres gebruikt de naam %s, maar het is NIET de echte site. De echte is %s." % (merk, echt)) if nl
                           else "It uses the name %s but is NOT the real site (%s)." % (merk, echt))
            break
    else:
        naam = hoofd.split(".")[0]                                     # lijkt het erop? ("rabob4nk.nl", "ingg.nl")
        for echt in OFFICIEEL:
            en = echt.split(".")[0]
            if len(en) >= 4 and naam != en and difflib.SequenceMatcher(None, naam, en).ratio() >= 0.8:
                punten += 4
                redenen.insert(0, ("Het adres lijkt op %s, maar is net anders. Dat is een bekend trucje." % echt) if nl
                               else "It looks like %s but is slightly different. A known trick." % echt)
                break
    if punten >= 4:
        st = SLECHT
        oordeel = "GEVAARLIJK: dit is waarschijnlijk een nep-site." if nl else "DANGEROUS: this is probably a fake site."
        advies = "Open hem niet, en vul er zeker niets in. Ga zelf naar de echte website." if nl else "Don't open it, and never fill anything in."
    elif punten >= 2:
        st = LET_OP
        oordeel = "PAS OP: deze site heeft kenmerken van een nep-site." if nl else "CAREFUL: this site has signs of a fake site."
        advies = "Vul er geen gegevens in, en betaal er niet. Twijfel je? Vraag het iemand die je vertrouwt." if nl else "Don't enter details or pay."
    else:
        st = GOED
        oordeel = "Ik zie niets verdachts aan dit adres. Maar ik ken niet elke site." if nl else "Nothing suspicious, but I don't know every site."
        advies = "Vraagt de site om je bankgegevens of DigiD? Wees dan extra voorzichtig." if nl else "Extra careful if it asks for bank details."
    return {"status": st, "oordeel": oordeel, "redenen": redenen, "advies": advies, "domein": dom}


# =====================================================================  3b. mail-controle (uit de webmail in de Buddy Browser)
GRATIS_MAIL = ("gmail.com", "googlemail.com", "hotmail.com", "hotmail.nl", "outlook.com", "outlook.nl", "live.nl", "live.com",
               "yahoo.com", "yahoo.nl", "icloud.com", "ziggo.nl", "kpnmail.nl", "planet.nl", "home.nl", "gmx.com", "proton.me")


def _lijkt_url(tekst):
    t = (tekst or "").strip().lower()
    return bool(re.match(r"^(https?://|www\.)\S+$", t) or re.match(r"^[a-z0-9-]+(\.[a-z0-9-]+)+(/\S*)?$", t))


def mail(info, taal="nl"):
    """info = {'afzender': adres, 'naam': weergavenaam, 'onderwerp', 'tekst', 'links': [{'tekst', 'href'}]}
    Geeft hetzelfde als bericht(), plus 'slechte_links': [domein, ...] - alle links daarheen maken we rood in de pagina."""
    nl = taal == "nl"
    tekst = "%s\n%s" % (info.get("onderwerp") or "", info.get("tekst") or "")
    r = bericht(tekst, taal, merk_check=False)                         # de afzender en links bekijken we hieronder zelf
    redenen, punten = list(r["redenen"]), r.get("punten", 0)
    slecht = []
    link_probleem = afzender_probleem = False
    # 1. de afzender: noemt zich een bank of instantie, maar het adres hoort er niet bij
    adres = (info.get("afzender") or "").strip().lower()
    naam = (info.get("naam") or "").lower()
    dom = adres.split("@")[-1] if "@" in adres else ""
    if dom:
        for merk, echt in ECHT.items():
            if len(merk) >= 3 and re.search(r"\b%s\b" % re.escape(merk), naam + " " + (info.get("onderwerp") or "").lower()):
                if not _is_van(dom, echt) and not _is_van(dom, _hoofd(echt)):
                    punten += 4; afzender_probleem = True
                    redenen.insert(0, ("De mail zegt van %s te komen, maar het adres is %s. Dat hoort NIET bij %s." % (merk.upper() if len(merk) <= 4 else merk.title(), adres, echt)) if nl
                                   else "It claims to be from %s, but the address is %s." % (merk, adres))
                break
        if dom in GRATIS_MAIL and any(re.search(r"\b%s\b" % re.escape(m), naam) for m in ECHT if len(m) >= 3):
            punten += 2; afzender_probleem = True
            redenen.append("Een bedrijf of bank mailt nooit vanaf een gewoon %s-adres." % dom if nl else "A company never mails from a %s address." % dom)
    # 2. de links: waar gaan ze ECHT naartoe?
    gezien = set()
    for l in info.get("links") or []:
        href = (l.get("href") or "").strip()
        if not href.lower().startswith(("http://", "https://")):
            continue
        hd = _domein(href)
        if not hd or hd in gezien or hd.endswith(("google.com", "gstatic.com", "googleusercontent.com")) and "mail" not in hd:
            continue
        gezien.add(hd)
        zicht = (l.get("tekst") or "").strip()
        if _lijkt_url(zicht):                                          # de tekst is zelf een adres: klopt die met de echte link?
            zd = _domein(zicht)
            if zd and zd != hd and _hoofd(zd) != _hoofd(hd):
                punten += 5; link_probleem = True
                slecht.append(hd)
                redenen.insert(0, ("Een link LIEGT: er staat %s, maar hij gaat echt naar %s." % (zd, hd)) if nl
                               else "A link LIES: it shows %s but really goes to %s." % (zd, hd))
                continue
        lr = link(href, taal)
        if lr["status"] == SLECHT:
            punten += 3; link_probleem = True
            slecht.append(hd)
            redenen.append(("De link naar %s is gevaarlijk: %s" % (hd, lr["redenen"][0])) if nl and lr["redenen"] else "The link to %s is dangerous." % hd)
    # 3. betrouwbare afzender (eigen, echt ogend domein), geen liegende of gevaarlijke links, en niets gevraagd
    #    -> gewone woorden in een nieuwsbrief maken hem niet verdacht
    afzender_ok = bool(dom) and dom not in GRATIS_MAIL and link(dom, taal)["status"] == GOED
    gevaarlijk_gevraagd = any(x in r.get("sterk", []) for x in ("gegevens", "familie", "helpdesk"))
    if afzender_ok and not (afzender_probleem or link_probleem or gevaarlijk_gevraagd):
        punten = min(punten, 1)
    if punten >= 5:
        st = SLECHT
        oordeel = "GEVAARLIJK: deze mail is bijna zeker oplichting." if nl else "DANGEROUS: this mail is almost certainly a scam."
        advies = ("Klik nergens op, betaal niets, en geef geen gegevens. Verdachte links heb ik ROOD omlijnd in de mail. "
                  "Gooi de mail weg. Twijfel je? Bel de afzender zelf, via een nummer dat JIJ opzoekt.") if nl \
            else "Don't click, pay or share anything. I outlined suspicious links in RED. Delete the mail."
    elif punten >= 2:
        st = LET_OP
        oordeel = ("LET OP: deze mail kan echt zijn, maar er zit iets in dat oplichters ook vaak gebruiken. Controleer het eerst zelf."
                   if nl else "CAREFUL: this may be real, but check it yourself first.")
        advies = r["advies"]
    else:
        st = GOED
        oordeel = ("Ik zie geen bekende oplichterstrucjes in deze mail. Maar helemaal zeker weten kan ik het nooit."
                   if nl else "I see no known scam tricks. But I can never be completely sure.")
        advies = r["advies"]
    if st == GOED:
        redenen = []
    return {"status": st, "oordeel": oordeel, "redenen": redenen, "advies": advies, "punten": punten, "slechte_links": slecht}


# =====================================================================  4. gouden regels
GOUDEN_REGELS = {
    "nl": ["Een bank vraagt NOOIT om je pincode, je wachtwoord of je bankpas. Ook niet aan de telefoon.",
           "Microsoft, Apple of Google bellen je NOOIT zelf over een virus op je pc.",
           "Laat nooit iemand die je belt in je pc meekijken. Niet met AnyDesk, niet met TeamViewer, met niets.",
           "Haast is een alarmbel. Echte bedrijven geven je de tijd. Hang op, en denk rustig na.",
           "Hoi mam, nieuw nummer? Bel eerst je kind of kleinkind op het oude nummer.",
           "Klik niet op links in mails of sms'jes van je bank of de overheid. Ga zelf naar de website, of open de app.",
           "Wie belt, hoeft niet te zijn wie hij zegt. Hang op en bel zelf terug, via het nummer op je pas of de echte website.",
           "Te mooi om waar te zijn? Dan is het niet waar. De prins met het fortuin bestaat niet.",
           "Twijfel? Vraag het iemand die je vertrouwt. Daar hoef je je nooit voor te schamen.",
           "Ben je toch in de val gelopen? Bel meteen je bank, en doe aangifte. Iedereen kan dit overkomen."],
    "en": ["A bank NEVER asks for your pin, password or bank card. Not even on the phone.",
           "Microsoft, Apple or Google NEVER call you about a virus.",
           "Never let a caller watch your pc. Not with AnyDesk, TeamViewer or anything.",
           "Hurry is an alarm bell. Hang up and think calmly.",
           "Hi mum, new number? Call your child on the old number first.",
           "Don't click links in messages from your bank. Go to the website yourself.",
           "Callers aren't always who they say. Hang up and call back via the number on your card.",
           "Too good to be true? Then it isn't true.",
           "In doubt? Ask someone you trust. Never be ashamed of that.",
           "Fell for it anyway? Call your bank right away and report it. It can happen to anyone."],
}


if __name__ == "__main__":                                             # proef: alleen lezen
    sv, lijst, nu = meekijk()
    print(sv)
    for b in lijst:
        print(" ", b["status"], b["titel"], "-", b["uitleg"])
