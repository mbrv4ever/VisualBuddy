# Drave Visual Buddy - eigen icoon: een paars oog met een sterretje (Pillow -> geldige .ico)
import os
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(HERE, "assets"), exist_ok=True)
S = 512
im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
d.rounded_rectangle((16, 16, S - 16, S - 16), radius=110, fill=(22, 19, 31, 255), outline=(127, 119, 221, 255), width=18)
# oog
d.ellipse((70, 150, S - 70, S - 150), fill=(240, 236, 255, 255), outline=(181, 156, 255, 255), width=14)
d.ellipse((176, 176, 336, 336), fill=(127, 119, 221, 255))
d.ellipse((216, 216, 296, 296), fill=(22, 19, 31, 255))
d.ellipse((276, 200, 310, 234), fill=(255, 255, 255, 255))
# geluidsgolfjes rechtsboven (hij praat)
for i, r in enumerate((60, 95, 130)):
    d.arc((S - 150 - r, 40 - r // 3, S - 150 + r, 40 + r), start=300, end=360, fill=(255, 220, 90, 255), width=12)
im.resize((256, 256), Image.LANCZOS).save(os.path.join(HERE, "assets", "icon_256.png"))
im.save(os.path.join(HERE, "assets", "icon.ico"), format="ICO", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("icoon klaar")
