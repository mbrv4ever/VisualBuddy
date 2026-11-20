from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, KeepTogether
import os
HERE=os.path.dirname(os.path.abspath(__file__))
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.units import cm
P=HexColor('#4a3d8f'); D=HexColor('#222222')
t=ParagraphStyle('t',fontName='Helvetica-Bold',fontSize=26,leading=32,textColor=P)
s=ParagraphStyle('s',fontName='Helvetica',fontSize=14,leading=19,textColor=HexColor('#555555'),spaceAfter=10)
h=ParagraphStyle('h',fontName='Helvetica-Bold',fontSize=18,leading=23,textColor=P,spaceBefore=12,spaceAfter=6)
b=ParagraphStyle('b',fontName='Helvetica',fontSize=14,leading=20,textColor=D,spaceAfter=6)
L=[Paragraph('Drave Visual Buddy - snelgids',t),
   Paragraph('Versie 0.9. Buddy leest hardop voor wat er op je scherm staat, en kijkt je pc na met de Pc-hulp. Alles zit nu in EEN venster: links de Buddy-knoppen, rechts de Buddy Browser. Voor blinden, slechtzienden en iedereen die het lastig vindt op de pc.',s)]
def blok(kop,regels,plaatje=None):
    samen=[Paragraph(kop,h)]
    if plaatje and os.path.exists(os.path.join(HERE,'gids',plaatje)):
        samen+=[Image(os.path.join(HERE,'gids',plaatje),width=16.5*cm,height=16.5*cm*1188/1875),Spacer(1,6)]
    rest=[Paragraph('&bull; '+x,b) for x in regels]
    L.append(KeepTogether(samen+rest[:1])); L.extend(rest[1:])
L.append(Paragraph('Starten',h)); L.append(Paragraph('Dubbelklik op <b>DraveVisualBuddy.exe</b>. Zegt Windows <i>\"Windows heeft uw pc beschermd\"</i>? Klik op <b>Meer informatie</b> en dan <b>Toch uitvoeren</b>.',b))
blok('Links: de Buddy-knoppen',[
 'Bovenaan staat <b>Ik lees:</b> ... Daar zie je welk venster Buddy voorleest: de Buddy Browser, of een ander programma (bijvoorbeeld Chrome).',
 '<b>Wat staat er? (F9)</b>: Buddy zegt waar je bent, en welke koppen, knoppen, invulvakjes en links er zijn.',
 '<b>Lees vanaf hier (F8)</b>: Buddy leest voor vanaf wat bovenaan je scherm staat, tot het eind.',
 '<b>Lees selectie (F7)</b>: selecteer eerst tekst met de muis.',
 '<b>Stop (F10)</b>, <b>Herhaal</b>, <b>Langzamer</b> / <b>Sneller</b> (tempo wordt onthouden).',
 '<b>Bovenop</b>: AAN = Buddy blijft altijd boven andere vensters. <b>Info (F1)</b>: info en doneren.',
 'F7 tot en met F10 werken overal op de pc, ook als Buddy niet voorop staat.'],'gids_mail.png')
blok('Rechts: de Buddy Browser',[
 'Grote knoppen <b>Terug</b>, <b>Vooruit</b>, <b>Start</b> en een adresvak. Typ een adres of een zoekwoord en druk op <b>Enter</b>.',
 'De alinea die Buddy voorleest krijgt een <b>geel kader</b>. De pagina schuift vanzelf mee.',
 '<b>Klik = lees</b>: zet AAN (groen) en klik op een alinea: Buddy leest vanaf daar. Zet UIT om gewoon te klikken.',
 '<b>A -</b> / <b>A +</b> (of Ctrl - en Ctrl +): de pagina kleiner of groter. Wordt onthouden.',
 'Het menu, de reclame en de voettekst van een pagina slaat Buddy over.'])
blok('Leesmodus',[
 'Klik op <b>Leesmodus</b> (of Ctrl + M). Buddy laat alleen het artikel zien: de kop en de tekst, groot en rustig op een donkere achtergrond.',
 'Het menu, de reclame, "Net binnen", video&#39;s en formulieren zijn weg.',
 'Druk op <b>F8</b>: Buddy leest voor met het gele kader. Klik = lees werkt ook.',
 'Nog een keer op <b>Leesmodus</b> = terug naar de gewone pagina. Ga je naar een andere pagina, dan gaat de leesmodus vanzelf uit.',
 'Vindt Buddy geen artikel (bijvoorbeeld op een voorpagina), dan zegt hij dat.'])
blok('Openen met...',[
 'Klik op <b>Openen met...</b> en kies: <b>Buddy Browser (hier)</b>, of een programma dat al op je pc staat (Chrome, Edge, Firefox, Word, Kladblok).',
 'Kies je een browser, dan opent hij met de pagina die je in Buddy had.',
 '<b>Ander programma kiezen...</b>: zoek zelf een programma. Buddy onthoudt het in het lijstje.',
 'Ga daarna naar dat programma en druk op <b>F9</b> of <b>F8</b>. Klik je weer in de Buddy Browser, dan leest Buddy die weer.'])
blok('Pc-hulp',[
 'Klik links op <b>Pc-hulp</b>. Buddy kijkt je pc na en vertelt het in gewone taal: hoe vol je schijven zijn, het werkgeheugen, je virusscanner, je firewall, Windows Update, hoeveel programma&#39;s meestarten en hoeveel rommel er weg mag.',
 'Achter elk punt staat een kleur, een teken en een woord: <b>Goed</b> (groen, met een vinkje), <b>Let op</b> (geel, met een uitroepteken), <b>Aandacht</b> (rood, met een kruisje). De belangrijkste staan bovenaan.',
 'Buddy leest alles voor. <b>F8</b> of <b>F9</b> = nog een keer voorlezen. <b>F10</b> = stop.',
 '<b>Ruim de rommel op</b>: Buddy vraagt het eerst, groot in beeld, met <b>JA</b> en <b>NEE</b>. Alleen bij <b>JA</b> ruimt hij op. Alles gaat naar de prullenbak, dus je kunt het terughalen.',
 '<b>Prullenbak legen</b>: Buddy vraagt het apart, en zegt erbij dat het dan voorgoed weg is.',
 'Hij komt nooit aan je documenten, foto&#39;s, persoonlijke mappen of het register. Wat hij doet, schrijft hij in <b>handen_logboek.txt</b>.',
 '<b>Terug naar de browser</b> brengt je weer bij de Buddy Browser.'],'gids_pc.png')
blok('Je mail lezen en controleren', [
 'Open je webmail (bijvoorbeeld <b>Gmail</b>) in de Buddy Browser. Je logt <b>zelf</b> in: Buddy ziet je wachtwoord nooit.',
 'Open een mail en druk links op <b>Lees mail</b>: Buddy leest voor van wie hij is, het onderwerp en de tekst.',
 'Druk op <b>Controleer mail</b>: Buddy kijkt of de afzender klopt (zegt hij ING te zijn maar komt hij van een raar adres of een gewoon Gmail-adres?), zoekt de bekende oplichterstrucjes, en kijkt waar elke link <b>echt</b> naartoe gaat.',
 'Een link die liegt (er staat <i>ing.nl</i>, maar hij gaat naar een ander adres) of naar een gevaarlijke site gaat, krijgt in de mail een <b>dik rood kader</b>. Klik daar niet op.',
 'Het oordeel staat links: <b>groen</b>, <b>geel</b> of <b>rood</b>, met uitleg, en wordt voorgelezen. Buddy verandert niets aan je mail.'])
blok('Bescherm mij en Instellingen', [
 'In de <b>Pc-hulp</b> staan twee nieuwe knoppen: <b>Bescherm mij</b> (oranje) en <b>Instellingen</b> (blauw). <b>Terug</b> brengt je weer bij de Pc-hulp.',
 '<b>Bescherm mij</b>: <b>Kijkt er iemand mee?</b> (programma&#39;s zoals AnyDesk of TeamViewer, met <b>Stop het meekijken NU</b> na JA), <b>Is dit bericht echt?</b> en <b>Is deze website echt?</b> (plakken en Controleer: groen, geel of rood met uitleg), en de <b>Gouden regels</b> tegen oplichters.',
 '<b>Instellingen</b>: 20 klusjes. Typ wat je wilt in gewone woorden (bijvoorbeeld <b>ik hoor niets</b> of <b>muis groter</b>). Buddy doet het zelf na JA (geluid, muispijl, vergrootglas, Verteller, donker/licht, dubbelklik, printer, meestarters, updates), met <b>Terugzetten zoals het was</b>. Of hij opent de goede pagina en vertelt stap voor stap wat je moet doen.',
 'Alles wordt voorgelezen. <b>F8</b> of <b>F9</b> = nog een keer. Je beveiliging verandert Buddy nooit zelf.'],'gids_bes.png')
blok('Veilig',[
 'Buddy leest alleen. Hij klikt niets, typt niets en verstuurt niets. De Pc-hulp ruimt alleen op als jij op JA drukt.',
 'Inloggen en cookies van de Buddy Browser blijven in de map <b>browserdata</b> naast de app. Niet op C:, niet in de cloud.',
 'De stem is Leon, met de uitspraaklijst van DraveLeon. Alles blijft op je eigen pc.'])
blok('Wat komt nog',[ 'Praten tegen Buddy, samen een klus doen, en post voorlezen via de camera.'])
L.append(Spacer(1,12)); L.append(Paragraph('Dravenlock (Roger &amp; Claudio) - gratis, steun via paypal.me/roger076 - service@dravenlock.nl',s))
SimpleDocTemplate(os.path.join(HERE,'DraveVisualBuddy_snelgids.pdf'),pagesize=A4,leftMargin=2*cm,rightMargin=2*cm,topMargin=1.8*cm,bottomMargin=1.8*cm,title='Drave Visual Buddy snelgids').build(L)
