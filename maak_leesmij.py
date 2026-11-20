# Drave Visual Buddy - "Lees mij eerst" (PDF, grote letters, simpele woorden). Voor slechtzienden.
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
import os
HERE = os.path.dirname(os.path.abspath(__file__))
t = ParagraphStyle('t', fontName='Helvetica-Bold', fontSize=34, leading=42, textColor='#2c8f7c', spaceAfter=12)
h = ParagraphStyle('h', fontName='Helvetica-Bold', fontSize=24, leading=30, textColor='#4a3d66', spaceBefore=18, spaceAfter=8)
b = ParagraphStyle('b', fontName='Helvetica', fontSize=20, leading=28, spaceAfter=10)
L = []
ic = os.path.join(HERE, 'assets', 'icon_256.png')
if os.path.exists(ic):
    L.append(Image(ic, width=3.2 * cm, height=3.2 * cm, hAlign='LEFT'))
L += [Paragraph('Lees mij eerst', t),
      Paragraph('Hallo! Dit is <b>Drave Visual Buddy</b>. Buddy leest voor wat er op uw scherm staat, en helpt u met internet, uw mail en uw pc. Voor iedereen die slecht ziet.', b)]


def blok(kop, regels):
    L.append(Paragraph(kop, h))
    for x in regels:
        L.append(Paragraph(x, b))


blok('1. Buddy starten', [
    'Dubbelklik op <b>DraveVisualBuddy.exe</b>.',
    'Tip: vraag iemand om een <b>snelkoppeling</b> op uw bureaublad te zetten. Dan vindt u Buddy altijd terug.'])
blok('2. Ziet u een blauw venster van Windows?', [
    'Soms zegt Windows: <i>"Windows heeft uw pc beschermd"</i>. Dat is normaal bij nieuwe gratis programma&#39;s.',
    'Klik dan op <b>Meer informatie</b>. Klik daarna op <b>Toch uitvoeren</b>. Dit hoeft maar &eacute;&eacute;n keer.'])
blok('3. De belangrijkste toetsen', [
    '<b>F9</b>: wat staat er op mijn scherm?',
    '<b>F8</b>: lees voor vanaf hier.',
    '<b>F7</b>: lees de tekst voor die ik heb geselecteerd.',
    '<b>F10</b>: stop met voorlezen. <b>F1</b>: info.',
    'Deze toetsen werken overal op de pc, ook als Buddy niet voorop staat.'])
blok('4. Wat kan Buddy nog meer?', [
    '<b>De Buddy Browser</b> (rechts): grote knoppen, een geel kader bij wat Buddy voorleest, en <b>Leesmodus</b> voor rustige, grote tekst.',
    '<b>Lees mail</b> en <b>Controleer mail</b>: Buddy leest uw mail voor en zegt of hij te vertrouwen is.',
    '<b>Pc-hulp</b>: Buddy kijkt uw pc na, helpt met instellingen en beschermt u tegen oplichters.'])
blok('5. Buddy is veilig', [
    'Buddy verandert <b>nooit</b> iets zonder het eerst te vragen. U drukt zelf op <b>JA</b> of <b>NEE</b>.',
    'Inloggen doet u zelf. Buddy ziet uw wachtwoord niet.',
    'Alles blijft op uw eigen pc. Buddy stuurt niets door.'])
blok('6. Gouden regel', [
    'Belt iemand op over een virus, of vraagt iemand uw pincode? <b>Ophangen.</b> Een bank of Microsoft doet dat nooit.'])
blok('Vragen?', [
    'In de map staat ook de <b>snelgids</b> en een <b>uitlegfilmpje</b>.',
    'Mail ons: <b>service@dravenlock.nl</b>',
    'Buddy is gratis. Wilt u ons steunen? <b>paypal.me/roger076</b>. Dank u wel!',
    '<i>Dravenlock - Roger en Claudio</i>'])
SimpleDocTemplate(os.path.join(HERE, 'Lees_mij_eerst.pdf'), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                  topMargin=1.8 * cm, bottomMargin=1.8 * cm, title='Drave Visual Buddy - Lees mij eerst').build(L)
print('KLAAR')
