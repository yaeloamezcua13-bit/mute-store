"""
Recorta detalles (tela, logo, capucha, puños, bolsillo, cuello...) para la
sección Calidad. Un solo color (negro) y enfocado a la zona de cada
característica. Cada detalle toma su recorte de la foto NEGRA de MÁS resolución
donde mejor se ve esa zona (no del flat-lay pequeño).

    python manage.py crop_quality
"""
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image

from store.models import Category, Product

# título -> (foto fuente, caja x0,y0,x1,y1 en fracciones)
ALO = {
    "Tela premium":            ("hoodie-alo-black/black-4.jpeg", (0.42, 0.46, 0.97, 1.00)),
    "Logo bordado":            ("hoodie-alo-black/black-4.jpeg", (0.20, 0.14, 0.82, 0.76)),
    "Capucha forrada":         ("hoodie-alo-black/black-2.jpeg", (0.12, 0.00, 0.88, 0.34)),
    "Puños y cintura tejidos": ("hoodie-alo-black/black-2.jpeg", (0.20, 0.74, 0.78, 0.98)),
    "Bolsillo canguro":        ("hoodie-alo-black/black-2.jpeg", (0.16, 0.46, 0.82, 0.78)),
}
ESS_HOODIE = {
    "Tela premium":            ("hoodie-essentials-negra/negra.jpeg", (0.30, 0.42, 0.55, 0.62)),
    "Logo bordado":            ("hoodie-essentials-negra/negra.jpeg", (0.50, 0.41, 0.76, 0.52)),
    "Capucha forrada":         ("hoodie-essentials-negra/negra.jpeg", (0.33, 0.15, 0.67, 0.36)),
    "Puños y cintura tejidos": ("hoodie-essentials-negra/negra.jpeg", (0.10, 0.68, 0.40, 0.86)),
}
PLAYERA = {
    "Tela peso medio":  ("playera-essentials-negra/negra.jpeg", (0.30, 0.45, 0.55, 0.65)),
    "Logo bordado":     ("playera-essentials-negra/negra.jpeg", (0.50, 0.36, 0.78, 0.47)),
    "Cuello reforzado": ("playera-essentials-negra/negra.jpeg", (0.36, 0.15, 0.64, 0.30)),
    "Corte regular":    ("playera-essentials-negra/negra.jpeg", (0.22, 0.45, 0.78, 0.85)),
}


def crop_square(img, x0, y0, x1, y1):
    """Recorta la zona indicada y la EXPANDE a cuadrado (sin recortar contenido)."""
    W, H = img.size
    bx0, by0, bx1, by1 = x0 * W, y0 * H, x1 * W, y1 * H
    s = max(bx1 - bx0, by1 - by0)
    cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
    nx0, ny0, nx1, ny1 = cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2
    if nx0 < 0: nx1 -= nx0; nx0 = 0
    if ny0 < 0: ny1 -= ny0; ny0 = 0
    if nx1 > W: nx0 -= (nx1 - W); nx1 = W
    if ny1 > H: ny0 -= (ny1 - H); ny1 = H
    return img.crop((int(max(0, nx0)), int(max(0, ny0)), int(nx1), int(ny1)))


class Command(BaseCommand):
    help = "Recorta detalles en negro (alta calidad) para la sección Calidad"

    def handle(self, *args, **opts):
        base = settings.BASE_DIR / "fotos"
        img_cache = {}

        def get_img(src):
            if src not in img_cache:
                img_cache[src] = Image.open(base / src).convert("RGB")
            return img_cache[src]

        def cfg_for(product):
            if product.category == Category.HOODIE_ALO:
                return ALO
            if product.slug.startswith("hoodie-essentials"):
                return ESS_HOODIE
            if product.slug.startswith("playera-essentials"):
                return PLAYERA
            return None

        n = 0
        for product in Product.objects.all():
            cfg = cfg_for(product)
            if not cfg:
                continue
            for feat in product.features.all():
                if feat.title not in cfg:
                    continue
                src, box = cfg[feat.title]
                crop = crop_square(get_img(src), *box)
                side = min(crop.size[0], 1000)  # no agrandar más de lo necesario
                crop = crop.resize((side, side), Image.LANCZOS)
                buf = BytesIO()
                crop.save(buf, "JPEG", quality=92)
                if feat.image:
                    feat.image.delete(save=False)
                feat.image.save(
                    f"calidad-{product.slug}-{feat.sort_order}.jpg",
                    ContentFile(buf.getvalue()), save=True,
                )
                n += 1
            self.stdout.write(self.style.SUCCESS(f"  ✓ {product.name}"))
        self.stdout.write(self.style.SUCCESS(f"\n¡Listo! {n} detalles de Calidad."))
