# -*- coding: utf-8 -*-
# Drave Visual Buddy 0.9 - leest voor wat er op je scherm staat, kijkt je pc na, beschermt en helpt met instellingen.
# Voor blinden, slechtzienden en iedereen die het lastig vindt op de pc.
# 0.5: alles in EEN venster: links de Buddy-knoppen, rechts de Buddy Browser.
#      "Openen met..." opent de Buddy Browser hier, of een eigen programma (Chrome, Edge, Word...).
#      Buddy leest alleen. Hij klikt niets, typt niets en verstuurt niets. Alles blijft op je eigen pc.
# 0.7: Pc-hulp met de gedeelde "handen" (DraveHanden): pc nakijken en uitleggen in gewone taal.
#      Opruimen ALLEEN als jij op Ja drukt (naar de prullenbak, terug te halen).
# 0.8: in de Pc-hulp ook "Bescherm mij" (meekijk-alarm, bericht/website echt?, gouden regels) en "Instellingen"
#      (20 klusjes: zoeken in gewone taal, uitleg, of na JA zelf doen met Terugzetten). Gedeelde schermen: handen_qt.
# 0.9: mail in de Buddy Browser: "Lees deze mail" en "Controleer deze mail" (afzender, trucjes, links die liegen ->
#      verdachte links ROOD omlijnd in de mail). Je logt zelf in; Buddy ziet je wachtwoord nooit en verandert niets.
# Dravenlock (Roger & Claudio), 19-11-2026. Donationware: paypal.me/roger076
import os, sys, time, threading, locale, traceback, webbrowser, ctypes, json, subprocess

HERE = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "cache")
os.makedirs(CACHE, exist_ok=True)
VERSIE = "0.9"
try:
    NL = (locale.getlocale()[0] or "nl").lower().startswith(("nl", "dutch"))
except Exception:
    NL = True

TX = {
    "titel": ("Drave Visual Buddy", "Drave Visual Buddy"),
    "lees": ("Wat staat er?  (F9)", "What's on screen?  (F9)"),
    "tekst": ("Lees vanaf hier  (F8)", "Read from here  (F8)"),
    "selectie": ("Lees selectie  (F7)", "Read selection  (F7)"),
    "stop": ("Stop  (F10)", "Stop  (F10)"),
    "herhaal": ("Herhaal", "Repeat"),
    "langzamer": ("Langzamer", "Slower"), "sneller": ("Sneller", "Faster"), "tempo": ("Tempo: %d%%", "Speed: %d%%"),
    "openen": ("Openen met...", "Open with..."),
    "hier": ("Buddy Browser (hier)", "Buddy Browser (here)"),
    "ander": ("Ander programma kiezen...", "Choose another program..."),
    "bovenop_aan": ("Bovenop: AAN", "On top: ON"), "bovenop_uit": ("Bovenop: UIT", "On top: OFF"),
    "info_knop": ("Info  (F1)", "Info  (F1)"),
    "lm_aan": ("Leesmodus: AAN", "Reader mode: ON"), "lm_uit": ("Leesmodus", "Reader mode"),
    "lm_klaar": ("Leesmodus: alleen het artikel. Druk op F8 om voor te lezen. Nog een keer op Leesmodus = terug.",
                 "Reader mode: only the article. Press F8 to read aloud. Press Reader mode again to go back."),
    "lm_geen": ("Ik vind op deze pagina geen artikel om in de leesmodus te zetten.", "I can't find an article on this page for reader mode."),
    "klik_aan": ("Klik = lees: AAN", "Click = read: ON"), "klik_uit": ("Klik = lees: UIT", "Click = read: OFF"),
    "klik_uitleg": ("Klik nu op een stukje tekst: Buddy leest vanaf daar. (Links werken dan even niet.)",
                    "Now click some text: Buddy reads from there. (Links don't work for now.)"),
    "terug": ("◀  Terug", "◀  Back"), "vooruit": ("Vooruit  ▶", "Forward  ▶"), "start": ("⌂  Start", "⌂  Home"), "ga": ("Ga", "Go"),
    "adres": ("Typ een adres of een zoekwoord en druk op Enter", "Type an address or search words and press Enter"),
    "ik_lees_br": ("Ik lees:  de Buddy Browser", "I read:  the Buddy Browser"),
    "ik_lees": ("Ik lees:  %s", "I read:  %s"),
    "ik_lees_niets": ("Ik lees:  nog niets gekozen", "I read:  nothing chosen yet"),
    "geen_sel": ("Selecteer eerst een stuk tekst met de muis en druk dan op F7.", "First select some text with the mouse, then press F7."),
    "geen_sel_ext": ("Selecteer eerst een stuk tekst met de muis en druk dan op F7. Lukt dat niet: rechtermuisknop, Kopiëren, en dan F7.",
                     "First select some text with the mouse, then press F7. If that doesn't work: right-click, Copy, then F7."),
    "bezig": ("Even kijken...", "Let me look..."),
    "geen": ("Ik weet nog niet welk venster ik moet lezen. Klik eerst even op dat venster.", "I don't know which window to read yet. Click that window first."),
    "niets_pagina": ("Ik kan op deze pagina nog niets lezen.", "I can't read anything on this page yet."),
    "vanaf": ("Ik lees voor vanaf alinea %d van %d.", "Reading from paragraph %d of %d."),
    "fout": ("Lezen lukt niet: %s", "Reading failed: %s"),
    "stem_laden": ("Stem wordt geladen...", "Loading voice..."),
    "gaat_open": ("%s gaat open. Ga erheen en druk op F9 of F8: dan lees ik dat venster.", "%s is opening. Go there and press F9 or F8: I'll read that window."),
    "niet_open": ("%s openen lukt niet.", "Could not open %s."),
    "gestopt": ("Gestopt.", "Stopped."),
    "info": ("Drave Visual Buddy %s - testversie.\nDravenlock (Roger & Claudio).\n\nBuddy leest alleen. Hij klikt, typt en verstuurt niets.\nPc-hulp verandert alleen iets als jij op Ja drukt.\nAlles blijft op je eigen pc.\n\nSteun ons: paypal.me/roger076\nVragen: service@dravenlock.nl",
             "Drave Visual Buddy %s - test version.\nDravenlock (Roger & Claudio).\n\nBuddy only reads. It does not click, type or send.\nPc help only changes things when you press Yes.\nEverything stays on your pc.\n\nSupport us: paypal.me/roger076\nQuestions: service@dravenlock.nl"),
    "pc": ("Pc-hulp", "Pc help"),
    "pc_titel": ("Pc-hulp: ik kijk je pc na", "Pc help: I check your pc"),
    "pc_terug": ("◀  Terug naar de browser", "◀  Back to the browser"),
    "pc_opnieuw": ("Kijk opnieuw", "Check again"),
    "pc_ruim": ("Ruim de rommel op", "Clean up the junk"),
    "pc_prul": ("Prullenbak legen", "Empty recycle bin"),
    "mail_lees": ("Lees mail", "Read mail"), "mail_check": ("Controleer mail", "Check mail"),
    "mail_geen": ("Ik zie geen geopende mail. Open eerst een mail in de Buddy Browser, bijvoorbeeld in Gmail.",
                  "I see no open mail. First open a mail in the Buddy Browser, for example in Gmail."),
    "mail_van": ("Mail van %s. Onderwerp: %s.", "Mail from %s. Subject: %s."),
    "mail_rood": ("Ik heb %d verdachte link(s) in de mail rood omlijnd. Klik daar niet op.", "I outlined %d suspicious link(s) in red. Don't click them."),
    "pc_bes": ("Bescherm mij", "Protect me"), "pc_inst": ("Instellingen", "Settings"),
    "pc_bezig": ("Ik kijk je pc na. Een momentje...", "I'm checking your pc. One moment..."),
    "pc_ja": ("JA", "YES"), "pc_nee": ("NEE", "NO"),
    "pc_vraag_ruim": ("Zal ik %s aan rommel opruimen? Het gaat naar de prullenbak, dus je kunt het altijd terughalen.",
                      "Shall I clean up %s of junk? It goes to the recycle bin, so you can always get it back."),
    "pc_vraag_prul": ("Zal ik de prullenbak legen? Er staan %s dingen in, samen %s. Let op: wat eruit gaat, is voorgoed weg.",
                      "Shall I empty the recycle bin? It holds %s items, %s in total. Careful: what goes is gone for good."),
    "pc_prul_leeg": ("De prullenbak is al leeg.", "The recycle bin is already empty."),
    "pc_niets_ruim": ("Er is bijna geen rommel. Opruimen is niet nodig.", "There is hardly any junk. No need to clean up."),
    "pc_nee_ok": ("Goed, ik doe niets.", "Okay, I won't do anything."),
    "pc_bezig_ruim": ("Ik ruim op. Een momentje...", "Cleaning up. One moment..."),
    "pc_status": ({"goed": "✔  Goed", "let_op": "!  Let op", "slecht": "✖  Aandacht", "onbekend": "?  Weet ik niet"},
                  {"goed": "✔  Good", "let_op": "!  Note", "slecht": "✖  Attention", "onbekend": "?  Unknown"}),
    "doneer": ("Doneren via PayPal", "Donate via PayPal"), "sluit": ("Sluiten", "Close"),
    "hulp": ("F9 = wat staat er  |  F8 = lees  |  F7 = selectie  |  F10 = stop  |  F1 = info",
             "F9 = overview  |  F8 = read  |  F7 = selection  |  F10 = stop  |  F1 = info"),
}
def T(k): return TX[k][0 if NL else 1]

user32 = ctypes.windll.user32 if os.name == "nt" else None
WM_HOTKEY, VK_F7, VK_F8, VK_F9, VK_F10 = 0x0312, 0x76, 0x77, 0x78, 0x79
INST_JSON = os.path.join(HERE, "buddy_instellingen.json")


def lees_inst():
    try:
        with open(INST_JSON, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def schrijf_inst(d):
    try:
        with open(INST_JSON, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
    except Exception:
        pass


def zoek_programmas():
    """Programma's die al op de pc staan: (naam, pad, is_browser)."""
    uit = []
    if os.name != "nt":
        return uit
    import winreg
    def app_pad(exe):
        for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            try:
                with winreg.OpenKey(hive, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\\" + exe) as k:
                    p = winreg.QueryValue(k, None).strip('"')
                    if p and os.path.isfile(p):
                        return p
            except OSError:
                pass
        return None
    pf = [os.environ.get(x, "") for x in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA")]
    vast = {"chrome.exe": [os.path.join(b, r"Google\Chrome\Application\chrome.exe") for b in pf],
            "msedge.exe": [os.path.join(b, r"Microsoft\Edge\Application\msedge.exe") for b in pf],
            "firefox.exe": [os.path.join(b, r"Mozilla Firefox\firefox.exe") for b in pf]}
    for naam, exe, br in (("Chrome", "chrome.exe", True), ("Edge", "msedge.exe", True), ("Firefox", "firefox.exe", True),
                          ("Word", "winword.exe", False)):
        p = app_pad(exe) or next((x for x in vast.get(exe, []) if x and os.path.isfile(x)), None)
        if p:
            uit.append((naam, p, br))
    kl = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "notepad.exe")
    if os.path.isfile(kl):
        uit.append(("Kladblok" if NL else "Notepad", kl, False))
    return uit


def main():
    sys.path.insert(0, HERE)
    import lezer
    import browser as br
    from stem import Stem
    from PyQt6.QtCore import Qt, QUrl, pyqtSignal, QObject, QTimer, QEvent, QRectF
    from PyQt6.QtGui import QFont, QShortcut, QKeySequence, QIcon, QPainter, QColor, QPen
    from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
                                 QLabel, QTextEdit, QMenu, QFileDialog, QDialog, QFrame, QStackedWidget, QScrollArea)
    import handen                                                # 0.7: de gedeelde handen (DraveHanden)
    import handen_qt                                             # 0.8: gedeelde schermen Bescherm + Instellingen
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEnginePage

    app = QApplication(sys.argv)
    profiel = br.maak_profiel(app)
    inst = lees_inst()

    class Sein(QObject):
        markeer = pyqtSignal(int)
        actie = pyqtSignal(str)
        regels = pyqtSignal(object)
        melding = pyqtSignal(str)
        klik = pyqtSignal()
        pc = pyqtSignal(object)                                 # 0.7: uitslag van de Pc-hulp
    sein = Sein()

    class Pagina(QWebEnginePage):
        def javaScriptConsoleMessage(self, niveau, bericht, regel, bron):
            if bericht == "BUDDYKLIK":
                sein.klik.emit()

    # ---------- stem
    stem = Stem(stem="Leon", taal="nl" if NL else "en")
    stem.stappen = 8
    INST = os.path.join(HERE, "instellingen.txt")
    try:
        stem.snelheid = max(0.6, min(1.4, float(open(INST, encoding="utf-8").read().strip())))
    except Exception:
        stem.snelheid = 0.85

    def bij_begin(label):
        if isinstance(label, str) and label.startswith("§"):
            try:
                sein.markeer.emit(int(label[1:]))
            except ValueError:
                pass
    stem.bij_begin = bij_begin
    if os.environ.get("BUDDY_STIL"):                            # alleen voor de proef: geen geluid ('s nachts)
        stem.zeg = lambda *a, **k: None
    stem.warm_op()

    # ---------- venster
    w = QMainWindow()
    w.setWindowTitle(T("titel"))
    try:
        w.setWindowIcon(QIcon(os.path.join(HERE, "assets", "icon_256.png")))
    except Exception:
        pass
    w.resize(1500, 950)
    w.setStyleSheet("""
        QMainWindow, QWidget { background:#16131f; color:#f0f0f5; }
        QPushButton { background:#221c34; border:2px solid #b59cff; border-radius:10px; padding:6px 12px; color:white; }
        QPushButton:hover { background:#4a3d66; }
        QPushButton[soort="hoofd"] { background:#3c306e; }
        QPushButton[soort="lees"] { background:#285a46; border-color:#78e696; }
        QPushButton[soort="sel"] { background:#6e5020; border-color:#ffdc5a; }
        QPushButton[soort="stop"] { background:#822832; border-color:#ff7878; }
        QPushButton[soort="open"] { background:#284670; border-color:#6edcff; }
        QPushButton[soort="pc"] { background:#20504a; border-color:#5ee0c8; }
        QPushButton[soort="ja"] { background:#287846; border-color:#78e696; font-size:22pt; }
        QPushButton[soort="nee"] { background:#822832; border-color:#ff7878; font-size:22pt; }
        QPushButton:disabled { background:#1b1728; border-color:#3a3350; color:#6a6680; }
        QFrame#vraag { background:#2a2440; border:3px solid #ffdc5a; border-radius:14px; }
        QFrame#rij { background:#1b1728; border:2px solid #2e2645; border-radius:12px; }
        QPushButton[aan="true"] { background:#287846; border-color:#78e696; }
        QLineEdit { background:#0f0d17; border:2px solid #4a3d66; border-radius:10px; padding:4px 10px; color:white; }
        QTextEdit { background:#0f0d17; border:2px solid #2e2645; border-radius:10px; padding:6px; color:#f0f0f5; }
        QMenu { background:#221c34; color:white; border:2px solid #b59cff; font-size:16pt; }
        QMenu::item { padding:8px 22px; } QMenu::item:selected { background:#4a3d66; }
        QFrame#links { background:#1b1728; border-right:2px solid #2e2645; }
        QLabel { background:transparent; }
    """)
    F_KNOP = QFont("Segoe UI", 14, QFont.Weight.Bold)
    F_GROOT = QFont("Segoe UI", 15, QFont.Weight.Bold)

    def knop(tekst, soort=None, h=46, f=F_KNOP):
        b = QPushButton(tekst); b.setFont(f); b.setMinimumHeight(h); b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        if soort:
            b.setProperty("soort", soort)
        return b

    class Oog(QWidget):                                         # oogje dat 'kijkt' als hij praat
        def __init__(self):
            super().__init__(); self.setFixedSize(70, 44); self.setStyleSheet("background:transparent;")
        def paintEvent(self, e):
            p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
            p.setPen(QPen(QColor(127, 119, 221), 3)); p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QRectF(3, 3, 64, 38))
            n = stem.niveau() if hasattr(stem, "niveau") else 0
            r = 7 + 7 * max(0.0, min(1.0, n))
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(181, 156, 255)); p.drawEllipse(QRectF(35 - r, 22 - r, 2 * r, 2 * r))

    # links: de Buddy-knoppen
    titel = QLabel(T("titel")); titel.setFont(QFont("Segoe UI", 19, QFont.Weight.Bold)); titel.setStyleSheet("color:#b59cff;")
    oog = Oog()
    kop = QHBoxLayout(); kop.addWidget(titel, 1); kop.addWidget(oog)
    doel_lbl = QLabel(T("ik_lees_br")); doel_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold)); doel_lbl.setWordWrap(True)
    doel_lbl.setStyleSheet("color:#6edcff;")
    b_lees = knop(T("lees"), "hoofd", 52, F_GROOT)
    b_tekst = knop(T("tekst"), "lees"); b_sel = knop(T("selectie"), "sel")
    b_stop = knop(T("stop"), "stop"); b_herhaal = knop(T("herhaal"))
    b_trager, b_sneller = knop(T("langzamer")), knop(T("sneller"))
    tempo_lbl = QLabel(); tempo_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold)); tempo_lbl.setStyleSheet("color:#ffdc5a;")
    tempo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    b_open = knop(T("openen"), "open")
    b_pc = knop(T("pc"), "pc", 52, F_GROOT)                     # 0.7
    b_mail_lees = knop(T("mail_lees"), "lees")                   # 0.9
    b_mail_check = knop(T("mail_check")); b_mail_check.setStyleSheet("background:#7a3a20; border-color:#ffa070;")
    b_boven = knop(T("bovenop_uit")); b_info = knop(T("info_knop"))
    melding_lbl = QLabel(""); melding_lbl.setWordWrap(True); melding_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
    melding_lbl.setStyleSheet("color:#ffdc5a;")
    tekstvak = QTextEdit(); tekstvak.setReadOnly(True); tekstvak.setFont(QFont("Segoe UI", 13))
    hulp = QLabel(T("hulp")); hulp.setWordWrap(True); hulp.setFont(QFont("Segoe UI", 10)); hulp.setStyleSheet("color:#9696aa;")

    L = QVBoxLayout(); L.setContentsMargins(14, 12, 14, 12); L.setSpacing(9)
    L.addLayout(kop); L.addWidget(doel_lbl); L.addWidget(b_lees); L.addWidget(b_tekst); L.addWidget(b_sel)
    r = QHBoxLayout(); r.addWidget(b_stop); r.addWidget(b_herhaal); L.addLayout(r)
    r = QHBoxLayout(); r.addWidget(b_trager); r.addWidget(tempo_lbl); r.addWidget(b_sneller); L.addLayout(r)
    L.addWidget(b_open); L.addWidget(b_pc)
    r = QHBoxLayout(); r.addWidget(b_mail_lees); r.addWidget(b_mail_check); L.addLayout(r)
    r = QHBoxLayout(); r.addWidget(b_boven); r.addWidget(b_info); L.addLayout(r)
    L.addWidget(melding_lbl); L.addWidget(tekstvak, 1); L.addWidget(hulp)
    links = QFrame(); links.setObjectName("links"); links.setLayout(L); links.setFixedWidth(400)

    # rechts: de Buddy Browser
    view = QWebEngineView()
    pagina = Pagina(profiel, view)
    view.setPage(pagina)
    view.setZoomFactor(float(inst.get("zoom", 1.25)))
    b_terug, b_vooruit, b_thuis = knop(T("terug")), knop(T("vooruit")), knop(T("start"))
    adres = QLineEdit(); adres.setFont(F_GROOT); adres.setMinimumHeight(46); adres.setPlaceholderText(T("adres"))
    b_ga = knop(T("ga")); b_lm = knop(T("lm_uit")); b_klik = knop(T("klik_uit")); b_zmin = knop("A −"); b_zplus = knop("A +")
    R1 = QHBoxLayout(); R1.setSpacing(8)
    for x in (b_terug, b_vooruit, b_thuis):
        R1.addWidget(x)
    R1.addWidget(adres, 1)
    for x in (b_ga, b_lm, b_klik, b_zmin, b_zplus):
        R1.addWidget(x)
    R = QVBoxLayout(); R.setContentsMargins(10, 12, 12, 12); R.setSpacing(8); R.addLayout(R1); R.addWidget(view, 1)
    rechts_br = QWidget(); rechts_br.setLayout(R)

    # 0.7: rechts kan ook de Pc-hulp staan
    pc_kop = QLabel(T("pc_titel")); pc_kop.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold)); pc_kop.setStyleSheet("color:#5ee0c8;")
    b_pc_terug = knop(T("pc_terug"))
    pc_sv = QLabel(""); pc_sv.setWordWrap(True); pc_sv.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
    pc_lijst_w = QWidget(); pc_lijst = QVBoxLayout(pc_lijst_w); pc_lijst.setSpacing(10); pc_lijst.setContentsMargins(0, 0, 8, 0)
    pc_scroll = QScrollArea(); pc_scroll.setWidgetResizable(True); pc_scroll.setWidget(pc_lijst_w)
    pc_scroll.setStyleSheet("QScrollArea { border:none; }")
    b_pc_opnieuw = knop(T("pc_opnieuw"), "lees", 56, F_GROOT)
    b_pc_ruim = knop(T("pc_ruim"), "pc", 56, F_GROOT)
    b_pc_prul = knop(T("pc_prul"), "sel", 56, F_GROOT)
    b_pc_bes = knop(T("pc_bes"), None, 56, F_GROOT); b_pc_bes.setStyleSheet("background:#7a3a20; border-color:#ffa070;")
    b_pc_inst = knop(T("pc_inst"), None, 56, F_GROOT); b_pc_inst.setStyleSheet("background:#284670; border-color:#6edcff;")
    vraag = QFrame(); vraag.setObjectName("vraag")
    vraag_lbl = QLabel(""); vraag_lbl.setWordWrap(True); vraag_lbl.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
    b_ja, b_nee = knop(T("pc_ja"), "ja", 80), knop(T("pc_nee"), "nee", 80)
    vq = QVBoxLayout(vraag); vq.setContentsMargins(18, 14, 18, 14); vq.addWidget(vraag_lbl)
    vh = QHBoxLayout(); vh.setSpacing(24); vh.addWidget(b_ja); vh.addWidget(b_nee); vq.addLayout(vh)
    vraag.hide()
    P = QVBoxLayout(); P.setContentsMargins(18, 14, 18, 14); P.setSpacing(12)
    ph = QHBoxLayout(); ph.addWidget(pc_kop, 1); ph.addWidget(b_pc_terug); P.addLayout(ph)
    P.addWidget(pc_sv); P.addWidget(vraag); P.addWidget(pc_scroll, 1)
    pk = QHBoxLayout(); pk.setSpacing(12)
    for x in (b_pc_opnieuw, b_pc_ruim, b_pc_prul):
        pk.addWidget(x)
    P.addLayout(pk)
    pk2 = QHBoxLayout(); pk2.setSpacing(12); pk2.addWidget(b_pc_bes); pk2.addWidget(b_pc_inst); P.addLayout(pk2)
    rechts_pc = QWidget(); rechts_pc.setLayout(P)
    rechts = QStackedWidget(); rechts.addWidget(rechts_br); rechts.addWidget(rechts_pc)
    terug_pc = lambda: (stem.stil(), rechts.setCurrentIndex(1))
    spreek_en_toon = lambda z: (toon_regels(list(z)), spreek(list(z)))                                       # ook links in het tekstvak
    scherm_bes = handen_qt.BeschermScherm(spreek=spreek_en_toon, nl=NL, maat=15, terug=terug_pc)             # 0.8: index 2
    scherm_kl = handen_qt.KlusjesScherm(spreek=spreek_en_toon, nl=NL, maat=15, terug=terug_pc)               # 0.8: index 3
    rechts.addWidget(scherm_bes); rechts.addWidget(scherm_kl)

    hoofd = QWidget(); H = QHBoxLayout(hoofd); H.setContentsMargins(0, 0, 0, 0); H.setSpacing(0)
    H.addWidget(links); H.addWidget(rechts, 1)
    w.setCentralWidget(hoofd)

    st = {"doel": "browser", "vorig": None, "bezig": False, "klik": False, "markeer": True, "laatst": [],
          "klem_nr": None, "klem_t": 0.0, "eigen": None, "lm": False,
          "pc": None, "pc_bezig": False, "pc_vraag": None, "pc_zinnen": []}

    # ---------- kleine hulpjes
    def melding(t):
        melding_lbl.setText(t or "")

    def toon_regels(regels):
        tekstvak.setPlainText("\n\n".join(regels[:40]))

    sein.melding.connect(melding)
    sein.regels.connect(toon_regels)

    def spreek(zinnen, labels=None):
        """Zinnen voorlezen en onthouden voor Herhaal."""
        stem.stil()
        st["laatst"] = list(zip(zinnen, labels or [None] * len(zinnen)))
        for z, lb in st["laatst"]:
            stem.zeg(z, label=lb) if lb else stem.zeg(z)

    def tempo(d):
        stem.snelheid = round(max(0.6, min(1.4, stem.snelheid + d)), 2)
        try:
            open(INST, "w", encoding="utf-8").write(str(stem.snelheid))
        except Exception:
            pass
        stem.stil(); stem.zeg("Zo klink ik nu." if NL else "This is how I sound now.")
        tempo_lbl.setText(T("tempo") % round(stem.snelheid * 100))
    tempo_lbl.setText(T("tempo") % round(stem.snelheid * 100))

    def venster_titel(h):
        try:
            buf = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(h, buf, 256)
            return lezer._titel(buf.value) or "?"
        except Exception:
            return "?"

    def toon_doel():
        if st["doel"] == "browser":
            doel_lbl.setText(T("ik_lees_br"))
        elif st["vorig"]:
            doel_lbl.setText(T("ik_lees") % venster_titel(st["vorig"]))
        else:
            doel_lbl.setText(T("ik_lees_niets"))

    def naar_browser():
        st["doel"] = "browser"; toon_doel()

    # ---------- de Buddy Browser lezen
    def br_lees_vanaf(index=None):
        stem.stil(); melding(T("bezig"))

        def klaar(r):
            if not r or not r.get("teksten"):
                melding(T("niets_pagina")); spreek([T("niets_pagina")]); return
            st["markeer"] = bool(r.get("markeer"))
            teksten = r["teksten"]
            begin = index if index is not None and index >= 0 else int(r.get("start", 0))
            melding(T("vanaf") % (begin + 1, len(teksten)))
            toon_regels(teksten[begin:begin + 40])
            zinnen, labels = [], []
            for i in range(begin, min(len(teksten), begin + 250)):
                for z in lezer.in_zinnen(teksten[i]):
                    zinnen.append(z); labels.append("§%d" % i)
            spreek(zinnen, labels)
        pagina.runJavaScript(br.BLOKKEN_JS, klaar)

    def br_overzicht():
        stem.stil(); melding("")

        def klaar(r):
            zinnen = lezer.maak_tekst(r or {}, NL)
            toon_regels(zinnen); spreek(zinnen)
        pagina.runJavaScript(br.OVERZICHT_JS, klaar)

    def br_selectie():
        stem.stil()

        def klaar(t):
            t = (t or "").strip()
            if not t:
                melding(T("geen_sel")); toon_regels([]); spreek([T("geen_sel")]); return
            zinnen = lezer.in_zinnen(t)
            melding(""); toon_regels(zinnen); spreek(zinnen)
        pagina.runJavaScript("window.getSelection().toString()", klaar)

    def markeer(i):
        if st["markeer"]:
            pagina.runJavaScript(br.MARKEER_JS % i)
    sein.markeer.connect(markeer)

    def wissel_klik():
        st["klik"] = not st["klik"]
        b_klik.setText(T("klik_aan") if st["klik"] else T("klik_uit"))
        b_klik.setProperty("aan", "true" if st["klik"] else "false")
        b_klik.style().unpolish(b_klik); b_klik.style().polish(b_klik)
        pagina.runJavaScript(br.KLIK_JS % ("true" if st["klik"] else "false"))
        melding(T("klik_uitleg") if st["klik"] else "")
        naar_browser()

    def zet_lm_knop():
        b_lm.setText(T("lm_aan") if st["lm"] else T("lm_uit"))
        b_lm.setProperty("aan", "true" if st["lm"] else "false"); b_lm.style().unpolish(b_lm); b_lm.style().polish(b_lm)

    def wissel_leesmodus():
        stem.stil(); pagina.runJavaScript(br.MARKEER_JS % -1); naar_browser()
        aan = not st["lm"]

        def klaar(n):
            if aan and not n:
                st["lm"] = False; melding(T("lm_geen")); spreek([T("lm_geen")])
            else:
                st["lm"] = aan; melding(T("lm_klaar") if aan else "")
                if aan:
                    spreek(["Leesmodus." if NL else "Reader mode."])
            zet_lm_knop()
            pagina.runJavaScript(br.KLIK_JS % ("true" if st["klik"] else "false"))
        pagina.runJavaScript(br.LEESMODUS_JS % ("true" if aan else "false"), klaar)

    def na_klik():
        naar_browser()
        def doel(i):
            if isinstance(i, (int, float)) and i >= 0:
                br_lees_vanaf(int(i))
        pagina.runJavaScript(br.BLOKKEN_JS, lambda _r: pagina.runJavaScript(br.INDEX_VAN_DOEL_JS, doel))
    sein.klik.connect(na_klik)

    def zoom(d):
        view.setZoomFactor(round(max(0.5, min(3.0, view.zoomFactor() + d)), 2))
        inst["zoom"] = view.zoomFactor(); schrijf_inst(inst)
        melding("%d%%" % round(view.zoomFactor() * 100))

    def ga_naar(t=None):
        url = br.adres_naar_url(adres.text() if t is None else t)
        if url:
            view.setUrl(url); naar_browser()

    # ---------- andere vensters lezen (Chrome, Word...) met Windows UI Automation
    def ext_lees(alles=False):
        hwnd = st["vorig"]
        if not hwnd:
            melding(T("geen")); spreek([T("geen")]); return
        if st["bezig"]:
            return
        st["bezig"] = True
        stem.stil(); stem.zeg(T("bezig"))

        def werk():
            try:
                r = lezer.lees(hwnd)
                zinnen = lezer.maak_voorleestekst(r, NL) if alles else lezer.maak_tekst(r, NL)
                sein.regels.emit(zinnen)
                sein.melding.emit((T("fout") % r["fout"]) if r.get("fout") and not r.get("knoppen") else "")
                spreek(zinnen)
            except Exception as ex:
                sein.melding.emit(T("fout") % ex)
            finally:
                st["bezig"] = False
        threading.Thread(target=werk, daemon=True).start()

    def ext_selectie():
        hwnd = st["vorig"]
        if st["bezig"]:
            return
        st["bezig"] = True
        stem.stil()

        def werk():
            try:
                tekst = lezer.lees_selectie(hwnd) if hwnd else ""
                if not tekst and time.time() - st["klem_t"] < 60:     # alleen als je het NET gekopieerd hebt
                    tekst = lezer.klembord_tekst()
                if not tekst:
                    sein.regels.emit([]); sein.melding.emit(T("geen_sel_ext")); spreek([T("geen_sel_ext")]); return
                zinnen = lezer.in_zinnen(tekst)
                sein.regels.emit(zinnen); sein.melding.emit(""); spreek(zinnen)
            except Exception as ex:
                sein.melding.emit(T("fout") % ex)
            finally:
                st["bezig"] = False
        threading.Thread(target=werk, daemon=True).start()

    # ---------- 0.7: Pc-hulp (met de gedeelde handen)
    taal = "nl" if NL else "en"
    KLEUR = {"goed": "#78e696", "let_op": "#ffdc5a", "slecht": "#ff7878", "onbekend": "#9696aa"}

    def pc_zichtbaar():
        return rechts.currentIndex() == 1

    def toon_pc(aan=True):
        rechts.setCurrentIndex(1 if aan else 0)
        if not aan:
            pc_vraag_weg()

    def pc_rijen_leeg():
        while pc_lijst.count():
            it = pc_lijst.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

    def pc_knoppen():
        bezig = st["pc_bezig"]
        for b in (b_pc_opnieuw, b_pc_ruim, b_pc_prul):
            b.setEnabled(not bezig and st["pc_vraag"] is None)

    def pc_nakijken():
        if st["pc_bezig"]:
            return
        toon_pc(True); pc_vraag_weg()
        st["pc_bezig"] = True; pc_knoppen()
        pc_sv.setText(T("pc_bezig")); pc_sv.setStyleSheet("color:#ffdc5a;"); pc_rijen_leeg()
        stem.stil(); stem.zeg(T("pc_bezig"))

        def werk():
            try:
                sv, lijst = handen.pc_nakijken(taal)
                g, n = handen.prullenbak_grootte()
                sein.pc.emit({"sv": sv, "lijst": lijst, "prul": (g, n)})
            except Exception as ex:
                sein.pc.emit({"sv": T("fout") % ex, "lijst": [], "prul": (None, None)})
        threading.Thread(target=werk, daemon=True).start()

    def pc_klaar(r):
        st["pc_bezig"] = False; st["pc"] = r
        if "uitleg" in r:                                       # uitslag van opruimen of legen
            pc_vraag_weg(); spreek([r["uitleg"]]); melding(r["uitleg"])
            QTimer.singleShot(400, pc_nakijken)                 # daarna meteen opnieuw kijken
            return
        pc_sv.setText(r["sv"]); pc_sv.setStyleSheet("color:#f0f0f5;"); pc_rijen_leeg()
        volgorde = {"slecht": 0, "let_op": 1, "onbekend": 2, "goed": 3}
        lijst = sorted(r["lijst"], key=lambda b: volgorde.get(b["status"], 9))   # belangrijkste bovenaan
        zinnen = [r["sv"]]
        for b in lijst:
            rij = QFrame(); rij.setObjectName("rij")
            hl = QHBoxLayout(rij); hl.setContentsMargins(14, 10, 14, 10); hl.setSpacing(16)
            stat = QLabel(TX["pc_status"][0 if NL else 1].get(b["status"], "?"))
            stat.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold)); stat.setFixedWidth(190)
            stat.setStyleSheet("color:%s;" % KLEUR.get(b["status"], "#ffffff"))
            tekst = "<b>%s</b><br>%s" % (b["titel"], b["uitleg"])
            if b.get("advies"):
                tekst += "<br><span style='color:#ffdc5a'>%s</span>" % b["advies"]
            tl = QLabel(tekst); tl.setWordWrap(True); tl.setFont(QFont("Segoe UI", 15))
            hl.addWidget(stat); hl.addWidget(tl, 1)
            pc_lijst.addWidget(rij)
            zinnen.append(b["uitleg"] + ((" " + b["advies"]) if b.get("advies") else ""))
        pc_lijst.addStretch(1)
        st["pc_zinnen"] = zinnen
        pc_knoppen(); spreek(zinnen)
        toon_regels(zinnen)
    sein.pc.connect(pc_klaar)

    def pc_rommel_bytes():
        for b in (st["pc"] or {}).get("lijst", []):
            if b["soort"] == "rommel":
                return b["extra"].get("bytes", 0)
        return 0

    def pc_vraag(soort):
        if soort == "ruim":
            n = pc_rommel_bytes()
            if n < 1024 * 1024:
                spreek([T("pc_niets_ruim")]); melding(T("pc_niets_ruim")); return
            zin = T("pc_vraag_ruim") % handen.mooi_getal(n)
        else:
            g, n = handen.prullenbak_grootte()
            if not n:
                spreek([T("pc_prul_leeg")]); melding(T("pc_prul_leeg")); return
            zin = T("pc_vraag_prul") % (n, handen.mooi_getal(g or 0))
        st["pc_vraag"] = soort
        vraag_lbl.setText(zin); vraag.show(); pc_knoppen()
        spreek([zin])

    def pc_vraag_weg():
        st["pc_vraag"] = None; vraag.hide(); pc_knoppen()

    def pc_antwoord(ja):
        soort = st["pc_vraag"]
        if soort is None:
            return
        if not ja:
            pc_vraag_weg(); spreek([T("pc_nee_ok")]); melding(T("pc_nee_ok")); return
        vraag.hide(); st["pc_vraag"] = None
        st["pc_bezig"] = True; pc_knoppen(); stem.stil(); stem.zeg(T("pc_bezig_ruim")); melding(T("pc_bezig_ruim"))

        def werk():                                             # de gebruiker drukte zelf op JA
            try:
                r = handen.ruim_op(bevestigd=True, taal=taal) if soort == "ruim" else handen.leeg_prullenbak(bevestigd=True, taal=taal)
            except Exception as ex:
                r = {"gedaan": False, "uitleg": T("fout") % ex}
            sein.pc.emit(r)
        threading.Thread(target=werk, daemon=True).start()

    # ---------- 0.9: mail in de Buddy Browser lezen en controleren (alleen lezen)
    def _mail(klaar):
        stem.stil(); toon_pc(False); naar_browser(); melding(T("bezig"))

        def terug(info):
            if not info or not (info.get("tekst") or "").strip() or (info.get("bron") == "pagina" and not info.get("afzender")
                                                                   and "mail" not in view.url().host()):
                melding(T("mail_geen")); spreek([T("mail_geen")]); return
            klaar(info)
        pagina.runJavaScript(br.MAIL_JS, terug)

    def mail_lees():
        def klaar(info):
            van = info.get("naam") or info.get("afzender") or ("onbekend" if NL else "unknown")
            if info.get("naam") and info.get("afzender"):
                van = "%s (%s)" % (info["naam"], info["afzender"])
            zinnen = [T("mail_van") % (van, info.get("onderwerp") or "-")] + lezer.in_zinnen(info["tekst"])[:300]
            melding(""); toon_regels(zinnen); spreek(zinnen)
        _mail(klaar)

    def mail_check():
        def klaar(info):
            import bescherm
            r = bescherm.mail(info, taal)
            kleur = {"goed": "#78e696", "let_op": "#ffdc5a", "slecht": "#ff7878"}.get(r["status"], "#ffdc5a")
            zinnen = [r["oordeel"]] + r["redenen"]
            if r["slechte_links"]:
                import json as _json
                pagina.runJavaScript(br.ROOD_JS % _json.dumps(r["slechte_links"]),
                                     lambda n: None)
                zinnen.append(T("mail_rood") % len(r["slechte_links"]))
            if r.get("advies"):
                zinnen.append(r["advies"])
            melding_lbl.setStyleSheet("color:%s;" % kleur); melding(r["oordeel"])
            toon_regels(zinnen); spreek(zinnen)
            QTimer.singleShot(15000, lambda: melding_lbl.setStyleSheet("color:#ffdc5a;"))
        _mail(klaar)

    # ---------- een knop of sneltoets: wat moet Buddy doen?
    def stoppen():
        stem.stil(); pagina.runJavaScript(br.MARKEER_JS % -1); melding(T("gestopt"))

    def doe(actie):
        if actie == "stop":
            stoppen(); return
        if actie == "info":
            info(); return
        if rechts.currentIndex() in (2, 3) and st["doel"] == "browser" and actie in ("overzicht", "lees"):
            spreek([z for z, _ in st["laatst"]]); return              # 0.8: Bescherm/Instellingen nog eens voorlezen
        if pc_zichtbaar() and st["doel"] == "browser" and actie in ("overzicht", "lees"):
            if st["pc_zinnen"]:
                spreek(st["pc_zinnen"])                         # 0.7: Pc-hulp nog een keer voorlezen
            return
        browser = st["doel"] == "browser"
        if actie == "overzicht":
            br_overzicht() if browser else ext_lees(False)
        elif actie == "lees":
            br_lees_vanaf() if browser else ext_lees(True)
        elif actie == "selectie":
            br_selectie() if browser else ext_selectie()
    sein.actie.connect(doe)

    # ---------- openen met...
    progs = zoek_programmas()
    for p in inst.get("programmas", []):
        if os.path.exists(p.get("pad", "")) and not any(x[1].lower() == p["pad"].lower() for x in progs):
            progs.append((p.get("naam") or os.path.splitext(os.path.basename(p["pad"]))[0], p["pad"], False))

    def open_prog(naam, pad, is_br):
        try:
            u = view.url().toString()
            if is_br and u.startswith("http"):
                subprocess.Popen([pad, u])                         # de pagina die je hier had, in je eigen browser
            else:
                os.startfile(pad)
            melding(T("gaat_open") % naam)
        except Exception:
            melding(T("niet_open") % naam)

    def kies_ander():
        pad, _ = QFileDialog.getOpenFileName(w, T("ander"), os.environ.get("ProgramFiles", ""),
                                             "Programma's (*.exe *.lnk);;Alles (*.*)" if NL else "Programs (*.exe *.lnk);;All (*.*)")
        if not pad:
            return
        pad = os.path.normpath(pad)
        naam = os.path.splitext(os.path.basename(pad))[0]
        lijst = inst.get("programmas", [])
        if not any(x.get("pad", "").lower() == pad.lower() for x in lijst):
            lijst.append({"naam": naam, "pad": pad}); inst["programmas"] = lijst; schrijf_inst(inst)
            progs.append((naam, pad, False)); bouw_menu()
        open_prog(naam, pad, False)

    menu = QMenu(w)

    def bouw_menu():
        menu.clear()
        a = menu.addAction(T("hier")); a.triggered.connect(lambda: (naar_browser(), view.setFocus()))
        menu.addSeparator()
        for naam, pad, is_br in progs:
            a = menu.addAction(naam); a.triggered.connect(lambda _=False, n=naam, p=pad, b=is_br: open_prog(n, p, b))
        menu.addSeparator()
        a = menu.addAction(T("ander")); a.triggered.connect(kies_ander)
    bouw_menu()
    b_open.clicked.connect(lambda: menu.exec(b_open.mapToGlobal(b_open.rect().bottomLeft())))

    # ---------- altijd bovenop (onthouden)
    def zet_bovenop(aan, bewaar=True):
        w.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, aan); w.show()
        b_boven.setText(T("bovenop_aan") if aan else T("bovenop_uit"))
        b_boven.setProperty("aan", "true" if aan else "false"); b_boven.style().unpolish(b_boven); b_boven.style().polish(b_boven)
        if bewaar:
            inst["bovenop"] = aan; schrijf_inst(inst)

    # ---------- info en doneren
    def info():
        d = QDialog(w); d.setWindowTitle(T("titel")); d.setStyleSheet(w.styleSheet())
        v = QVBoxLayout(d); v.setContentsMargins(24, 20, 24, 20); v.setSpacing(14)
        l = QLabel(T("info") % VERSIE); l.setFont(QFont("Segoe UI", 14)); v.addWidget(l)
        k1, k2 = knop(T("doneer"), "open"), knop(T("sluit"))
        k1.clicked.connect(lambda: webbrowser.open("https://paypal.me/roger076")); k2.clicked.connect(d.accept)
        h = QHBoxLayout(); h.addWidget(k1); h.addWidget(k2); v.addLayout(h)
        d.exec()

    # ---------- knoppen koppelen
    b_lees.clicked.connect(lambda: doe("overzicht")); b_tekst.clicked.connect(lambda: doe("lees"))
    b_sel.clicked.connect(lambda: doe("selectie")); b_stop.clicked.connect(stoppen)
    b_herhaal.clicked.connect(lambda: spreek([z for z, _ in st["laatst"]], [lb for _, lb in st["laatst"]]))
    b_trager.clicked.connect(lambda: tempo(-0.1)); b_sneller.clicked.connect(lambda: tempo(0.1))
    b_boven.clicked.connect(lambda: zet_bovenop(not w.windowFlags() & Qt.WindowType.WindowStaysOnTopHint))
    b_info.clicked.connect(info)
    b_pc.clicked.connect(lambda: (naar_browser(), pc_nakijken()))       # 0.7
    b_mail_lees.clicked.connect(mail_lees); b_mail_check.clicked.connect(mail_check)     # 0.9
    b_pc_terug.clicked.connect(lambda: (stem.stil(), toon_pc(False)))
    b_pc_opnieuw.clicked.connect(pc_nakijken)
    b_pc_ruim.clicked.connect(lambda: pc_vraag("ruim")); b_pc_prul.clicked.connect(lambda: pc_vraag("prul"))
    b_ja.clicked.connect(lambda: pc_antwoord(True)); b_nee.clicked.connect(lambda: pc_antwoord(False))
    b_pc_bes.clicked.connect(lambda: (stem.stil(), naar_browser(), rechts.setCurrentIndex(2), scherm_bes.open()))     # 0.8
    b_pc_inst.clicked.connect(lambda: (stem.stil(), naar_browser(), rechts.setCurrentIndex(3), scherm_kl.open()))
    b_terug.clicked.connect(lambda: (view.back(), naar_browser())); b_vooruit.clicked.connect(lambda: (view.forward(), naar_browser()))
    b_thuis.clicked.connect(lambda: (toon_pc(False), ga_naar(br.START))); b_ga.clicked.connect(lambda: ga_naar()); adres.returnPressed.connect(lambda: ga_naar())
    b_klik.clicked.connect(wissel_klik); b_lm.clicked.connect(wissel_leesmodus); b_zmin.clicked.connect(lambda: zoom(-0.1)); b_zplus.clicked.connect(lambda: zoom(0.1))
    view.urlChanged.connect(lambda u: adres.setText(u.toString()))
    view.loadStarted.connect(lambda: (st.update(lm=False), zet_lm_knop()))
    view.loadFinished.connect(lambda ok: (pagina.runJavaScript(br.KLIK_JS % ("true" if st["klik"] else "false")),
                                          w.setWindowTitle(T("titel") + "  -  " + (view.title() or ""))))
    for toets, a in (("F9", "overzicht"), ("F8", "lees"), ("F7", "selectie"), ("F10", "stop"), ("F1", "info")):
        QShortcut(QKeySequence(toets), w, activated=lambda a=a: doe(a))
    for toets, f in (("Ctrl+L", adres.setFocus), ("Ctrl+M", wissel_leesmodus), ("Alt+Left", view.back), ("Alt+Right", view.forward),
                     ("Ctrl++", lambda: zoom(0.1)), ("Ctrl+=", lambda: zoom(0.1)), ("Ctrl+-", lambda: zoom(-0.1))):
        QShortcut(QKeySequence(toets), w, activated=f)

    # klik je IN de Buddy Browser, dan leest Buddy de Buddy Browser
    class KlikWacht(QObject):
        def eventFilter(self, obj, e):
            if e.type() in (QEvent.Type.MouseButtonPress, QEvent.Type.KeyPress) and isinstance(obj, QWidget):
                x = obj
                while x is not None:
                    if x is view or x is adres:
                        if st["doel"] != "browser":
                            naar_browser()
                        break
                    x = x.parentWidget()
            return False
    wacht = KlikWacht(); app.installEventFilter(wacht)

    # ---------- Windows: welk venster had je net, en F7-F10 overal op de pc
    def volg():
        while True:
            try:
                h = user32.GetForegroundWindow()
                eigen = st["eigen"]
                if h and eigen and h != eigen and user32.GetAncestor(h, 3) != eigen:
                    if st["vorig"] != h or st["doel"] != "extern":
                        st["vorig"], st["doel"] = h, "extern"
                nr = user32.GetClipboardSequenceNumber()          # wanneer is er voor het laatst iets gekopieerd?
                if st["klem_nr"] is not None and nr != st["klem_nr"]:
                    st["klem_t"] = time.time()
                st["klem_nr"] = nr
            except Exception:
                pass
            time.sleep(0.25)

    def sneltoetsen():
        import ctypes.wintypes
        for nr, vk in ((1, VK_F9), (2, VK_F10), (3, VK_F8), (4, VK_F7)):
            user32.RegisterHotKey(None, nr, 0, vk)
        msg = ctypes.wintypes.MSG()
        welke = {1: "overzicht", 2: "stop", 3: "lees", 4: "selectie"}
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            if msg.message == WM_HOTKEY and msg.wParam in welke:
                h = user32.GetForegroundWindow()
                eigen = st["eigen"]
                if h and eigen and h != eigen and user32.GetAncestor(h, 3) != eigen:
                    st["vorig"], st["doel"] = h, "extern"
                sein.actie.emit(welke[msg.wParam])

    timer = QTimer(w); timer.timeout.connect(lambda: (oog.update(), toon_doel(),
                                                      melding_lbl.setText(T("stem_laden")) if stem.status == "laden" and not melding_lbl.text() else None))
    timer.start(120)

    beginpagina = next((a for a in sys.argv[1:] if a.startswith(("http", "file:"))), br.START)
    view.setUrl(QUrl(beginpagina))
    w.show()
    st["eigen"] = int(w.winId())
    if inst.get("bovenop"):
        zet_bovenop(True, bewaar=False)
    if user32 and not os.environ.get("BUDDY_SHOT"):              # 0.9.1: bij schermfoto's geen andere vensters volgen (privacy)
        threading.Thread(target=volg, daemon=True).start()
        threading.Thread(target=sneltoetsen, daemon=True).start()

    # alleen voor de proef
    if os.environ.get("BUDDY_LEES"):
        QTimer.singleShot(int(float(os.environ["BUDDY_LEES"]) * 1000), lambda: doe("lees"))
    if os.environ.get("BUDDY_KLIK"):
        QTimer.singleShot(2500, wissel_klik)
        QTimer.singleShot(3500, lambda: pagina.runJavaScript("document.querySelectorAll('p')[1].click()"))
    if os.environ.get("BUDDY_JS"):                                 # "sec|javascript"
        _t, _js = os.environ["BUDDY_JS"].split("|", 1)
        QTimer.singleShot(int(float(_t) * 1000), lambda: pagina.runJavaScript(_js))
    if os.environ.get("BUDDY_JSLOG"):                              # "sec|javascript" -> cache\jslog.txt
        _t2, _js2 = os.environ["BUDDY_JSLOG"].split("|", 1)
        QTimer.singleShot(int(float(_t2) * 1000), lambda: pagina.runJavaScript(
            _js2, lambda r: open(os.path.join(CACHE, "jslog.txt"), "w", encoding="utf-8").write(repr(r))))
    if os.environ.get("BUDDY_LM"):
        QTimer.singleShot(int(float(os.environ["BUDDY_LM"]) * 1000), wissel_leesmodus)
    if os.environ.get("BUDDY_SCROL"):
        QTimer.singleShot(int(float(os.environ["BUDDY_SCROL"]) * 1000), lambda: pagina.runJavaScript("window.scrollBy(0,60)"))
    if os.environ.get("BUDDY_PC"):                                 # 0.7: Pc-hulp openen
        QTimer.singleShot(int(float(os.environ["BUDDY_PC"]) * 1000), lambda: (naar_browser(), pc_nakijken()))
    if os.environ.get("BUDDY_MAIL"):                               # 0.9: "sec|lees" of "sec|check"
        _t10, _s10 = os.environ["BUDDY_MAIL"].split("|", 1)
        QTimer.singleShot(int(float(_t10) * 1000), mail_check if _s10 == "check" else mail_lees)
    if os.environ.get("BUDDY_BES"):                                # 0.8: "sec|mee" / "sec|regels" / "sec|bericht:..." / "sec|link:..."
        _t8, _s8 = os.environ["BUDDY_BES"].split("|", 1)

        def _bes():
            b_pc_bes.click()
            if _s8 == "mee": scherm_bes.meekijk()
            elif _s8 == "regels": scherm_bes.regels()
            elif _s8.startswith("bericht:"): scherm_bes.bericht(); scherm_bes.invoer.setPlainText(_s8[8:]); scherm_bes.check()
            elif _s8.startswith("link:"): scherm_bes.link(); scherm_bes.adres.setText(_s8[5:]); scherm_bes.check()
        QTimer.singleShot(int(float(_t8) * 1000), _bes)
    if os.environ.get("BUDDY_KLUS"):                               # 0.8: "sec|klus-id" (alleen tonen)
        _t9, _s9 = os.environ["BUDDY_KLUS"].split("|", 1)
        QTimer.singleShot(int(float(_t9) * 1000), lambda: (b_pc_inst.click(), scherm_kl.kies(handen_qt.klusjes.zoek_klus(_s9))))
    if os.environ.get("BUDDY_KVRAAG"):                             # 0.8: alleen de vraag tonen, NOOIT ja
        QTimer.singleShot(int(float(os.environ["BUDDY_KVRAAG"]) * 1000), scherm_kl.eerste_vraag)
    if os.environ.get("BUDDY_PCVRAAG"):                            # 0.7: alleen de vraag tonen (NOOIT ja drukken)
        _t3, _s3 = os.environ["BUDDY_PCVRAAG"].split("|", 1)
        QTimer.singleShot(int(float(_t3) * 1000), lambda: pc_vraag(_s3))
    if os.environ.get("BUDDY_SHOT"):
        def foto():
            w.grab().save(os.path.join(CACHE, "shot.png")); app.quit()
        QTimer.singleShot(int(float(os.environ["BUDDY_SHOT"]) * 1000), foto)
    app.exec()
    stem.stil()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        with open(os.path.join(CACHE, "error.log"), "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + traceback.format_exc() + "\n")
    finally:
        os._exit(0)
