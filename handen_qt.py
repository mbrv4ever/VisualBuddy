# -*- coding: utf-8 -*-
"""DraveHanden - gedeelde schermen 0.2 (PyQt6): "Bescherm mij" en "Instellingen".

Een keer gebouwd, overal te gebruiken (Drave Visual Buddy, DraveMaatje, ...):
    from handen_qt import BeschermScherm, KlusjesScherm
    s = BeschermScherm(spreek=mijn_spreek_functie, nl=True, maat=16, terug=lambda: ...)
De app geeft alleen een 'spreek(zinnen)'-functie mee (voorlezen) en wat er bij Terug moet gebeuren.
Alle veiligheidsregels zitten in de hulpjes zelf: niets verandert zonder JA (bevestigd=True).
"""
from __future__ import annotations

import threading

from PyQt6.QtCore import Qt, QObject, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QLabel, QFrame, QScrollArea,
                             QLineEdit, QPlainTextEdit, QSizePolicy)

import bescherm
import klusjes

VERSIE = "0.2"

TX = {
    "terug": ("◀  Terug", "◀  Back"), "ja": ("JA", "YES"), "nee": ("NEE", "NO"),
    "nee_ok": ("Goed, ik doe niets.", "Okay, I won't do anything."),
    "fout": ("Dat lukte niet: %s", "That didn't work: %s"),
    # bescherm
    "bes_kop": ("Bescherm mij tegen oplichters", "Protect me against scammers"),
    "bes_uitleg": ("Kies wat je wilt laten controleren. Alles blijft op je eigen pc.", "Choose what you want checked. Everything stays on your pc."),
    "bes_mee": ("Kijkt er iemand mee?", "Is someone watching?"), "bes_ber": ("Is dit bericht echt?", "Is this message real?"),
    "bes_link": ("Is deze website echt?", "Is this website real?"), "bes_regels": ("Gouden regels", "Golden rules"),
    "bes_ber_uitleg": ("Plak hieronder de mail, sms of WhatsApp (rechtermuisknop, Plakken) en druk op Controleer.",
                       "Paste the mail, text or WhatsApp below (right-click, Paste) and press Check."),
    "bes_link_uitleg": ("Plak hieronder het websiteadres (rechtermuisknop, Plakken) en druk op Controleer.",
                        "Paste the web address below and press Check."),
    "bes_check": ("Controleer", "Check"), "bes_stop": ("Stop het meekijken NU", "Stop the watching NOW"),
    "bes_stop_vraag": ("Zal ik het meekijk-programma nu uitzetten? Dan kan degene aan de andere kant niet meer in je pc.",
                       "Shall I turn off the remote program now?"),
    "bes_bezig": ("Ik kijk even. Een momentje...", "Checking. One moment..."),
    "bes_regels_kop": ("De gouden regels tegen oplichters:", "The golden rules against scammers:"),
    # klusjes
    "kl_kop": ("Waar kan ik je mee helpen?", "What can I help you with?"),
    "kl_uitleg": ("Typ wat je wilt, of kies hieronder een klusje.", "Type what you want, or pick a job below."),
    "kl_hint": ("Bijvoorbeeld: muis groter", "For example: bigger mouse"), "kl_zoek": ("Zoek", "Search"),
    "kl_niet": ("Dat ken ik nog niet. Kies hieronder een klusje, of probeer het met andere woorden.",
                "I don't know that yet. Pick a job below, or try other words."),
    "kl_zien": ("Laat me zien waar het staat", "Show me where it is"),
    "kl_terug": ("Terugzetten zoals het was", "Undo, back as it was"),
    "kl_terug_vraag": ("Zal ik het terugzetten zoals het was, voordat ik iets veranderde?", "Shall I put it back as it was?"),
    "kl_alle": ("◀  Alle klusjes", "◀  All jobs"),
    "kl_zelf": ("Dit doe je zelf. Druk op Laat me zien waar het staat: dan open ik de goede pagina en vertel ik wat je moet doen.",
                "You do this yourself. Press Show me where it is."),
    "kl_kijken": ("Even kijken...", "Let me look..."),
}

KLEUR = {"goed": "#78e696", "let_op": "#ffdc5a", "slecht": "#ff7878"}

STIJL = """
QPushButton[hsoort="groen"] { background:#287846; border-color:#78e696; }
QPushButton[hsoort="blauw"] { background:#284670; border-color:#6edcff; }
QPushButton[hsoort="oranje"] { background:#7a3a20; border-color:#ffa070; }
QPushButton[hsoort="klus"] { background:#2a2440; border-color:#6edcff; }
QPushButton[hsoort="rood"] { background:#822832; border-color:#ff7878; }
QPushButton:disabled { background:#1b1728; border-color:#3a3350; color:#6a6680; }
QFrame#hvraag { background:#2a2440; border:3px solid #ffdc5a; border-radius:14px; }
QFrame#hvak { background:#1b1728; border:2px solid #2e2645; border-radius:12px; }
QPlainTextEdit { background:#0f0d17; border:3px solid #ffa070; border-radius:12px; padding:8px; color:white; }
QLineEdit { background:#0f0d17; border:3px solid #6edcff; border-radius:12px; padding:6px 12px; color:white; }
QScrollArea { border:none; }
"""


class _Sein(QObject):
    klaar = pyqtSignal(object)


class _Basis(QWidget):
    def __init__(self, spreek, nl=True, maat=16, terug=None):
        super().__init__()
        self.nl, self.taal, self.maat = nl, ("nl" if nl else "en"), maat
        self._spreek = spreek or (lambda zinnen: None)
        self._terug = terug
        self.setStyleSheet(STIJL)

    def T(self, k):
        return TX[k][0 if self.nl else 1]

    def F(self, extra=0, vet=True):
        return QFont("Segoe UI", max(10, self.maat + extra), QFont.Weight.Bold if vet else QFont.Weight.Normal)

    def _zet(self, w, extra=0, vet=True):
        """Letter zetten en onthouden, zodat zet_maat() later alles groter of kleiner kan maken."""
        w.setProperty("hx", int(extra)); w.setProperty("hv", bool(vet)); w.setFont(self.F(extra, vet))

    def zet_maat(self, maat):
        """0.2: tekst groter/kleiner (knoppen Tekst groter / Tekst kleiner van de app)."""
        self.maat = int(maat)
        for x in self.findChildren(QWidget):
            if x.property("hx") is not None:
                x.setFont(self.F(int(x.property("hx")), bool(x.property("hv"))))

    def knop(self, tekst, soort=None, h=64, extra=2):
        b = QPushButton(tekst); b.setMinimumHeight(h); self._zet(b, extra); b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        if soort:
            b.setProperty("hsoort", soort)
        return b

    def spreek(self, zinnen):
        self._spreek([z for z in zinnen if z])

    def kop(self, tekst, kleur):
        k = QLabel(tekst); self._zet(k, 8); k.setStyleSheet("color:%s;" % kleur)
        rij = QHBoxLayout(); rij.addWidget(k, 1)
        if self._terug:
            b = self.knop(self.T("terug"), None, 60, 0); b.clicked.connect(self._terug); rij.addWidget(b)
        return rij

    def vraag_vak(self):
        v = QFrame(); v.setObjectName("hvraag"); v.setMinimumHeight(190)
        lbl = QLabel(""); lbl.setWordWrap(True); self._zet(lbl, 4)
        ja, nee = self.knop(self.T("ja"), "groen", 90, 10), self.knop(self.T("nee"), "rood", 90, 10)
        l = QVBoxLayout(v); l.setContentsMargins(18, 14, 18, 14); l.addWidget(lbl)
        h = QHBoxLayout(); h.setSpacing(24); h.addWidget(ja); h.addWidget(nee); l.addLayout(h)
        v.hide()
        return v, lbl, ja, nee


class BeschermScherm(_Basis):
    """Meekijk-alarm, is dit bericht echt?, is deze website echt?, gouden regels."""

    def __init__(self, spreek, nl=True, maat=16, terug=None):
        super().__init__(spreek, nl, maat, terug)
        self.modus = None
        self.sein = _Sein(); self.sein.klaar.connect(self._klaar)
        self.uitleg = QLabel(self.T("bes_uitleg")); self.uitleg.setWordWrap(True); self._zet(self.uitleg, 0, False)
        self.uitleg.setStyleSheet("color:#d0d0e0;")
        self.b_mee, self.b_ber = self.knop(self.T("bes_mee"), "oranje", 72, 4), self.knop(self.T("bes_ber"), "oranje", 72, 4)
        self.b_link, self.b_regels = self.knop(self.T("bes_link"), "oranje", 72, 4), self.knop(self.T("bes_regels"), "oranje", 72, 4)
        self.invoer = QPlainTextEdit(); self.invoer.setMinimumHeight(130); self._zet(self.invoer, 0, False); self.invoer.hide()
        self.adres = QLineEdit(); self.adres.setMinimumHeight(62); self._zet(self.adres, 4); self.adres.hide()
        self.b_check = self.knop(self.T("bes_check"), "groen", 66, 6); self.b_check.hide()
        self.oordeel = QLabel(""); self.oordeel.setWordWrap(True); self._zet(self.oordeel, 6)
        self.tekst = QLabel(""); self.tekst.setWordWrap(True); self.tekst.setTextFormat(Qt.TextFormat.RichText)
        self._zet(self.tekst, 2, False); self.tekst.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        sc = QScrollArea(); sc.setWidgetResizable(True); sc.setWidget(self.tekst)
        self.b_stop = self.knop(self.T("bes_stop"), "rood", 76, 6); self.b_stop.hide()
        self.vraag, self.vraag_lbl, b_ja, b_nee = self.vraag_vak(); self.vraag_lbl.setText(self.T("bes_stop_vraag"))
        L = QVBoxLayout(self); L.setContentsMargins(18, 14, 18, 14); L.setSpacing(10)
        L.addLayout(self.kop(self.T("bes_kop"), "#ffa070")); L.addWidget(self.uitleg)
        g = QGridLayout(); g.setSpacing(10)
        g.addWidget(self.b_mee, 0, 0); g.addWidget(self.b_ber, 0, 1); g.addWidget(self.b_link, 1, 0); g.addWidget(self.b_regels, 1, 1)
        L.addLayout(g); L.addWidget(self.invoer); L.addWidget(self.adres); L.addWidget(self.b_check)
        L.addWidget(self.oordeel); L.addWidget(self.vraag); L.addWidget(sc, 1); L.addWidget(self.b_stop)
        self.b_mee.clicked.connect(self.meekijk); self.b_ber.clicked.connect(self.bericht); self.b_link.clicked.connect(self.link)
        self.b_regels.clicked.connect(self.regels); self.b_check.clicked.connect(self.check); self.adres.returnPressed.connect(self.check)
        self.b_stop.clicked.connect(lambda: (self.vraag.show(), self.b_stop.setEnabled(False), self.spreek([self.T("bes_stop_vraag")])))
        b_ja.clicked.connect(lambda: self._stop_antwoord(True)); b_nee.clicked.connect(lambda: self._stop_antwoord(False))

    def open(self):
        self._leeg(None); self.uitleg.setText(self.T("bes_uitleg"))
        self.spreek([self.T("bes_kop") + ".", self.T("bes_uitleg")])

    def _leeg(self, modus):
        self.modus = modus
        self.invoer.setVisible(modus == "bericht"); self.adres.setVisible(modus == "link"); self.b_check.setVisible(modus in ("bericht", "link"))
        self.b_stop.hide(); self.vraag.hide(); self.oordeel.setText(""); self.tekst.setText("")

    def _toon(self, status, oordeel, html, advies=""):
        self.oordeel.setText(oordeel); self.oordeel.setStyleSheet("color:%s;" % KLEUR.get(status, "#f0f0f5"))
        if advies:
            html += "<p style='color:#ffdc5a'><b>%s</b></p>" % advies
        self.tekst.setText(html)

    def meekijk(self):
        self._leeg("mee"); self.oordeel.setText(self.T("bes_bezig")); self.oordeel.setStyleSheet("color:#ffdc5a;")
        self.spreek([self.T("bes_bezig")])

        def werk():
            try:
                sv, lijst, nu = bescherm.meekijk(self.taal)
                self.sein.klaar.emit({"soort": "mee", "sv": sv, "lijst": lijst, "nu": nu})
            except Exception as ex:
                self.sein.klaar.emit({"soort": "fout", "sv": self.T("fout") % ex})
        threading.Thread(target=werk, daemon=True).start()

    def _klaar(self, r):
        if r["soort"] == "mee":
            status = "slecht" if r["nu"] else ("let_op" if r["lijst"] else "goed")
            html = "".join("<p><span style='color:%s'><b>%s</b></span><br>%s<br><span style='color:#ffdc5a'>%s</span></p>"
                           % (KLEUR[b["status"]], b["titel"], b["uitleg"], b["advies"]) for b in r["lijst"])
            self._toon(status, r["sv"], html); self.b_stop.setVisible(bool(r["nu"]))
            self.spreek([r["sv"]] + [b["uitleg"] + " " + b["advies"] for b in r["lijst"]])
        elif r["soort"] == "stop":
            self._toon("goed" if r.get("gedaan") else "slecht", r["uitleg"], ""); self.spreek([r["uitleg"]])
            QTimer.singleShot(1500, self.meekijk)                   # daarna opnieuw kijken: is het echt weg?
        else:
            self._toon("let_op", r["sv"], ""); self.spreek([r["sv"]])

    def bericht(self):
        self._leeg("bericht"); self.uitleg.setText(self.T("bes_ber_uitleg")); self.invoer.clear(); self.invoer.setFocus()
        self.spreek([self.T("bes_ber_uitleg")])

    def link(self):
        self._leeg("link"); self.uitleg.setText(self.T("bes_link_uitleg")); self.adres.clear(); self.adres.setFocus()
        self.spreek([self.T("bes_link_uitleg")])

    def check(self):
        if self.modus == "bericht":
            r = bescherm.bericht(self.invoer.toPlainText(), self.taal)
        elif self.modus == "link":
            r = bescherm.link(self.adres.text(), self.taal)
        else:
            return
        self._toon(r["status"], r["oordeel"], "".join("<p>&bull; %s</p>" % x for x in r["redenen"]), r.get("advies", ""))
        self.spreek([r["oordeel"]] + r["redenen"] + ([r["advies"]] if r.get("advies") else []))

    def regels(self):
        self._leeg("regels"); self.uitleg.setText(self.T("bes_uitleg"))
        rg = bescherm.GOUDEN_REGELS[self.taal]
        self._toon("goed", self.T("bes_regels_kop"), "".join("<p><b>%d.</b> %s</p>" % (i + 1, x) for i, x in enumerate(rg)))
        self.oordeel.setStyleSheet("color:#ffa070;")
        self.spreek([self.T("bes_regels_kop")] + rg)

    def _stop_antwoord(self, ja):
        self.vraag.hide(); self.b_stop.setEnabled(True)
        if not ja:
            self.spreek([self.T("nee_ok")]); return

        def werk():                                                 # de gebruiker drukte zelf op JA
            try:
                r = bescherm.stop_meekijken(bevestigd=True, taal=self.taal)
            except Exception as ex:
                r = {"gedaan": False, "uitleg": self.T("fout") % ex}
            r["soort"] = "stop"
            self.sein.klaar.emit(r)
        threading.Thread(target=werk, daemon=True).start()


class KlusjesScherm(_Basis):
    """Instellingen: zoeken in gewone taal, uitleg + pagina, en (na JA) zelf doen, met Terugzetten."""

    def __init__(self, spreek, nl=True, maat=16, terug=None):
        super().__init__(spreek, nl, maat, terug)
        self.klus, self.wacht = None, None
        self.sein = _Sein(); self.sein.klaar.connect(self._klus_klaar)
        self.uitleg = QLabel(self.T("kl_uitleg")); self.uitleg.setWordWrap(True); self._zet(self.uitleg, 0, False)
        self.uitleg.setStyleSheet("color:#d0d0e0;")
        self.zoekvak = QLineEdit(); self.zoekvak.setPlaceholderText(self.T("kl_hint")); self.zoekvak.setMinimumHeight(62)
        self._zet(self.zoekvak, 4)
        b_zoek = self.knop(self.T("kl_zoek"), "blauw", 62, 2)
        lijst_w = QWidget(); self.grid = QGridLayout(lijst_w); self.grid.setSpacing(10); self.grid.setContentsMargins(0, 0, 8, 0)
        self.lijst = QScrollArea(); self.lijst.setWidgetResizable(True); self.lijst.setWidget(lijst_w)
        self.lijst.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        for i, k in enumerate(klusjes.KLUSJES):
            b = self.knop(klusjes.titel(k, self.taal), "klus" if k.get("acties") else None, 68, 2)
            b.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
            b.clicked.connect(lambda _=False, k=k: self.kies(k))
            self.grid.addWidget(b, i // 2, i % 2)
        self.vak = QFrame(); self.vak.setObjectName("hvak")
        self.titel = QLabel(""); self._zet(self.titel, 6); self.titel.setStyleSheet("color:#5ee0c8;"); self.titel.setWordWrap(True)
        self.b_alle = self.knop(self.T("kl_alle"), None, 58, 0)
        self.tekst = QLabel(""); self.tekst.setWordWrap(True); self.tekst.setTextFormat(Qt.TextFormat.RichText); self._zet(self.tekst, 2, False)
        self.vraag, self.vraag_lbl, b_ja, b_nee = self.vraag_vak()
        self.acties_w = QWidget(); self.acties = QGridLayout(self.acties_w); self.acties.setSpacing(10); self.acties.setContentsMargins(0, 0, 0, 0)
        self.b_terug = self.knop(self.T("kl_terug"), "rood", 70, 2); self.b_zien = self.knop(self.T("kl_zien"), "blauw", 70, 2)
        vl = QVBoxLayout(self.vak); vl.setContentsMargins(16, 12, 16, 12); vl.setSpacing(10)
        th = QHBoxLayout(); th.addWidget(self.titel, 1); th.addWidget(self.b_alle); vl.addLayout(th)
        vl.addWidget(self.tekst); vl.addWidget(self.vraag); vl.addWidget(self.acties_w)
        bh = QHBoxLayout(); bh.setSpacing(12); bh.addWidget(self.b_terug); bh.addWidget(self.b_zien); vl.addLayout(bh); vl.addStretch(1)
        self.vak.hide()
        L = QVBoxLayout(self); L.setContentsMargins(18, 14, 18, 14); L.setSpacing(10)
        L.addLayout(self.kop(self.T("kl_kop"), "#6edcff")); L.addWidget(self.uitleg)
        zr = QHBoxLayout(); zr.setSpacing(10); zr.addWidget(self.zoekvak, 1); zr.addWidget(b_zoek); L.addLayout(zr)
        L.addWidget(self.lijst, 1); L.addWidget(self.vak, 1)
        b_zoek.clicked.connect(self.zoeken); self.zoekvak.returnPressed.connect(self.zoeken)
        self.b_alle.clicked.connect(self.alle); self.b_zien.clicked.connect(self.zien)
        self.b_terug.clicked.connect(lambda: self._vraag("terug"))
        b_ja.clicked.connect(lambda: self._antwoord(True)); b_nee.clicked.connect(lambda: self._antwoord(False))

    def open(self):
        self.alle(); self.uitleg.setText(self.T("kl_uitleg")); self.zoekvak.clear(); self.zoekvak.setFocus()
        self.spreek([self.T("kl_kop"), self.T("kl_uitleg")])

    def alle(self):
        self.klus, self.wacht = None, None; self.vraag.hide(); self.vak.hide(); self.lijst.show()

    def _knoppen(self):
        vrij = self.wacht is None
        self.acties_w.setVisible(vrij); self.b_zien.setVisible(vrij); self.b_alle.setEnabled(vrij)
        self.b_terug.setVisible(bool(vrij and self.klus and klusjes.kan_terug(self.klus)))

    def kies(self, k, extra=""):
        self.klus, self.wacht = k, None; self.vraag.hide(); self.lijst.hide(); self.vak.show()
        self.titel.setText(klusjes.titel(k, self.taal))
        while self.acties.count():
            it = self.acties.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        self.tekst.setText((extra + "<br><br>" if extra else "") + self.T("kl_kijken")); self._knoppen()

        def werk():
            self.sein.klaar.emit({"klus": k, "nu": klusjes.huidig(k, self.taal), "acties": klusjes.acties(k, self.taal), "extra": extra})
        threading.Thread(target=werk, daemon=True).start()

    def _klus_klaar(self, r):
        k = r["klus"]
        if self.klus is not k:
            return
        tekst = r["nu"] or ""
        if not k.get("acties"):
            tekst = (tekst + "<br><br>" if tekst else "") + self.T("kl_zelf")
        self.tekst.setText(((r["extra"] + "<br><br>") if r["extra"] else "") + tekst)
        for i, a in enumerate(r["acties"]):
            b = self.knop(a["label"], "groen", 68, 2)
            b.clicked.connect(lambda _=False, a=a: self._vraag(a))
            self.acties.addWidget(b, i // 2, i % 2)
        self._knoppen()
        if not r["extra"]:
            self.spreek([klusjes.titel(k, self.taal) + ".", r["nu"]] + ([] if k.get("acties") else [self.T("kl_zelf")]))

    def zoeken(self):
        g = klusjes.zoek(self.zoekvak.text())
        if g:
            self.kies(g[0])
        else:
            self.alle(); self.uitleg.setText(self.T("kl_niet")); self.spreek([self.T("kl_niet")])

    def zien(self):
        if not self.klus:
            return
        zinnen = klusjes.stappen(self.klus, self.taal)
        self.tekst.setText("<br>".join("<b>%d.</b> %s" % (i + 1, z) for i, z in enumerate(zinnen)))
        self.spreek(zinnen)
        klusjes.open_pagina(self.klus["pagina"])

    def _vraag(self, actie):
        self.wacht = actie
        zin = self.T("kl_terug_vraag") if actie == "terug" else actie["vraag"]
        self.vraag_lbl.setText(zin); self.vraag.show(); self._knoppen()
        self.spreek([zin])

    def _antwoord(self, ja):
        k, actie = self.klus, self.wacht
        if not k or not actie:
            return
        self.wacht = None; self.vraag.hide()
        if not ja:
            self._knoppen(); self.tekst.setText(self.T("nee_ok")); self.spreek([self.T("nee_ok")]); return
        if actie == "terug":                                        # de gebruiker drukte zelf op JA
            r = klusjes.terugzetten(k, bevestigd=True, taal=self.taal)
        else:
            r = klusjes.doe_actie(k, actie, bevestigd=True, taal=self.taal)
        self.spreek([r["uitleg"]])
        self.kies(k, extra="<b>%s</b>" % r["uitleg"])

    def eerste_vraag(self):
        """Alleen voor de proef: toon de vraag van de eerste knop (NOOIT ja drukken)."""
        for i in range(self.acties.count()):
            x = self.acties.itemAt(i).widget()
            if x:
                x.click()
                return
