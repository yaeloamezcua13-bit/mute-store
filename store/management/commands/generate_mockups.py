"""
Genera mockups de diseño (ilustraciones flat-lay) de cada prenda en su color,
con el logo MUTE, y los adjunta a la base de datos. Sin dependencias externas
(solo Pillow). Pensado como placeholder profesional hasta tener fotos reales.

    python manage.py generate_mockups
    python manage.py generate_mockups --product hoodie-alo-accolade
"""
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from store.models import Product

W, H = 1000, 1250
SS = 2  # supersampling para bordes suaves

FONTS = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/HelveticaNeue.ttc",
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial.ttf",
]


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def shade(rgb, f):
    return tuple(max(0, min(255, int(c * f))) for c in rgb)


def lum(rgb):
    return 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]


def font(size):
    for p in FONTS:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


def sc(points, k):
    return [(x * k, y * k) for x, y in points]


# Silueta de playera (manga corta)
TEE = [
    (430, 360), (330, 350), (190, 440), (150, 580), (255, 610), (305, 520),
    (310, 1060), (690, 1060), (695, 520), (745, 610), (850, 580), (810, 440),
    (670, 350), (570, 360), (500, 410),
]

# Silueta de sudadera/hoodie (manga larga)
LONG_TEE = [
    (430, 360), (330, 350), (210, 430), (120, 770), (215, 800), (300, 545),
    (310, 1060), (690, 1060), (700, 545), (785, 800), (880, 770), (790, 430),
    (670, 350), (570, 360), (500, 410),
]


class Command(BaseCommand):
    help = "Genera mockups de diseño de los productos (Pillow)"

    def add_arguments(self, parser):
        parser.add_argument("--product", help="slug de un producto específico")

    def handle(self, *args, **opts):
        qs = Product.objects.all()
        if opts["product"]:
            qs = qs.filter(slug=opts["product"])

        for product in qs:
            self.stdout.write(f"📦 {product.name}")
            for color in product.colors.all():
                img = self._render(product.category, color.name, hex_rgb(color.hex_code))
                buf = BytesIO()
                img.save(buf, "PNG", optimize=True)
                if color.image:
                    color.image.delete(save=False)  # evita duplicados en disco
                color.image.save(
                    f"{product.slug}-{color.name.lower()}.png",
                    ContentFile(buf.getvalue()), save=True,
                )
                self.stdout.write(self.style.SUCCESS(f"   ✓ {color.name}"))
        self.stdout.write(self.style.SUCCESS("\n¡Mockups generados y adjuntados!"))

    def _render(self, category, color_name, rgb):
        k = SS
        im = self._background(k)
        d = ImageDraw.Draw(im, "RGBA")

        is_dark = lum(rgb) < 80
        outline = shade(rgb, 1.7) if is_dark else shade(rgb, 0.55)

        long_sleeve = "playera" not in category
        points = LONG_TEE if long_sleeve else TEE

        if "hoodie" in category:
            self._hood(d, k, rgb)
        self._body(d, k, rgb, outline, points)
        if long_sleeve:
            self._cuffs(d, k, rgb)
        if "hoodie" in category:
            self._pocket(d, k, rgb)
            self._drawstrings(d, k)
        if "crewneck" in category:
            self._crew_collar(d, k, rgb, outline)

        self._shading(im, k, rgb)
        self._logo(im, k, rgb)

        return im.resize((W, H), Image.LANCZOS)

    def _background(self, k):
        bg = Image.new("RGB", (W * k, H * k), (13, 13, 13))
        glow = Image.new("L", (W * k, H * k), 0)
        gd = ImageDraw.Draw(glow)
        cx, cy, r = W * k // 2, int(H * k * 0.42), int(W * k * 0.62)
        gd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=90)
        glow = glow.filter(ImageFilter.GaussianBlur(160))
        light = Image.new("RGB", bg.size, (42, 42, 44))
        return Image.composite(light, bg, glow)

    def _body(self, d, k, rgb, outline, points):
        d.polygon(sc(points, k), fill=rgb, outline=outline, width=4 * k)
        # línea de pliegue central sutil
        d.line([(500 * k, 430 * k), (500 * k, 1050 * k)], fill=shade(rgb, 0.85), width=2 * k)

    def _cuffs(self, d, k, rgb):
        c = shade(rgb, 0.82)
        d.polygon(sc([(120, 770), (215, 800), (203, 845), (108, 812)], k), fill=c)
        d.polygon(sc([(880, 770), (785, 800), (797, 845), (892, 812)], k), fill=c)

    def _hood(self, d, k, rgb):
        # capucha redondeada detrás del cuello, con apertura más oscura
        d.ellipse(sc([(372, 252), (628, 408)], k), fill=shade(rgb, 0.8))
        d.ellipse(sc([(408, 292), (592, 412)], k), fill=shade(rgb, 0.6))

    def _pocket(self, d, k, rgb):
        pts = [(372, 770), (628, 770), (660, 905), (340, 905)]
        d.polygon(sc(pts, k), fill=shade(rgb, 0.9), outline=shade(rgb, 0.7), width=2 * k)

    def _drawstrings(self, d, k):
        grey = (210, 208, 202)
        for x in (472, 528):
            d.line([(x * k, 415 * k), (x * k, 545 * k)], fill=grey, width=4 * k)
            d.ellipse([(x - 9) * k, 545 * k, (x + 9) * k, 568 * k], fill=grey)

    def _crew_collar(self, d, k, rgb, outline):
        d.arc(sc([(420, 350), (580, 430)], k), 200, 340, fill=outline, width=6 * k)

    def _shading(self, im, k, rgb):
        # brillo suave en el centro-superior
        sheen = Image.new("L", im.size, 0)
        sd = ImageDraw.Draw(sheen)
        sd.ellipse(sc([(380, 470), (620, 780)], k), fill=60)
        sheen = sheen.filter(ImageFilter.GaussianBlur(90))
        white = Image.new("RGB", im.size, (255, 255, 255))
        im.paste(Image.composite(white, im, sheen), (0, 0),
                 sheen.point(lambda v: int(v * 0.5)))

    def _logo(self, im, k, rgb):
        d = ImageDraw.Draw(im, "RGBA")
        txt_color = (245, 241, 234, 230) if lum(rgb) < 150 else (26, 26, 26, 230)
        f = font(34 * k)
        text, spacing = "MUTE", 8 * k
        widths = [d.textlength(c, font=f) for c in text]
        total = sum(widths) + spacing * (len(text) - 1)
        x = (W * k - total) / 2
        y = 560 * k
        for c, w in zip(text, widths):
            d.text((x, y), c, font=f, fill=txt_color)
            x += w + spacing
