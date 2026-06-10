"""
Fotos de las hoodies Alo usando FOTOS REALES distintas por área
(no recortes de una sola foto). Donde falta una toma, se rellena con un
recorte de una foto de ALTA resolución (nítido).

  - Principal: model shot del color.
  - Galería: flat (sin persona) + detalle de logo.
  - Calidad (5): tela, logo, capucha, puños/cintura, bolsillo — fotos distintas.

Lee de media/products/ (versionado). Idempotente. Corre en cada despliegue.

    python manage.py alo_photos
"""
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image, ImageFilter

from store.models import Product, ProductImage

# spec: ("full", ruta)  ó  ("crop", ruta, (x0,y0,x1,y1))
CONFIG = {
    "hoodie-alo-black": {
        "primary": "products/editorial/black.jpg",
        "gallery": [("full", "products/colors/mute-black-model.jpg"),
                    ("full", "products/ai/hoodie-alo-black-front.jpg"),
                    ("full", "products/colors/hoodie-alo-black-clean.jpg"),
                    ("full", "products/gallery/black-4.jpeg")],
        "features": {
            "Tela premium":            ("crop", "products/ai/hoodie-alo-black-front.jpg", (0.20, 0.50, 0.46, 0.74)),
            "Logo bordado":            ("full", "products/gallery/black-4.jpeg"),
            "Capucha forrada":         ("full", "products/gallery/black-2.jpeg"),
            "Puños y cintura tejidos": ("full", "products/gallery/black-3.jpeg"),
            "Bolsillo canguro":        ("full", "products/gallery/black-5.jpeg"),
        },
    },
    "hoodie-alo-navy": {
        "primary": "products/editorial/navy.jpg",
        "gallery": [("full", "products/colors/mute-navy-model.jpg"),
                    ("full", "products/ai/hoodie-alo-navy-front.jpg"),
                    ("full", "products/gallery/mute-navy-flat.jpg"),
                    ("full", "products/gallery/mute-navy-detail.jpg")],
        "features": {
            "Tela premium":            ("crop", "products/ai/hoodie-alo-navy-front.jpg", (0.20, 0.50, 0.46, 0.74)),
            "Logo bordado":            ("full", "products/gallery/mute-navy-detail.jpg"),
            "Capucha forrada":         ("full", "products/gallery/navy-3.png"),
            "Puños y cintura tejidos": ("full", "products/gallery/navy-back.jpeg"),
            "Bolsillo canguro":        ("full", "products/gallery/navy-2.jpeg"),
        },
    },
    "hoodie-alo-grey": {
        "primary": "products/editorial/grey.jpg",
        "gallery": [("full", "products/gallery/grey-2.jpeg"),
                    ("full", "products/ai/hoodie-alo-grey-front.jpg"),
                    ("full", "products/colors/hoodie-alo-grey-clean.jpg"),
                    ("full", "products/gallery/mute-grey-detail.jpg")],
        "features": {
            "Tela premium":            ("crop", "products/ai/hoodie-alo-grey-front.jpg", (0.20, 0.50, 0.46, 0.74)),
            "Logo bordado":            ("full", "products/gallery/mute-grey-detail.jpg"),
            "Capucha forrada":         ("crop", "products/ai/hoodie-alo-grey-front.jpg", (0.30, 0.09, 0.70, 0.33)),
            "Puños y cintura tejidos": ("full", "products/gallery/grey-3.jpeg"),
            "Bolsillo canguro":        ("crop", "products/ai/hoodie-alo-grey-front.jpg", (0.30, 0.55, 0.70, 0.80)),
        },
    },
    "hoodie-alo-espresso": {
        "primary": "products/editorial/espresso.jpg",
        "gallery": [("full", "products/colors/mute-espresso-model.jpg"),
                    ("full", "products/ai/hoodie-alo-espresso-front.jpg"),
                    ("full", "products/colors/espresso.jpg"),
                    ("full", "products/gallery/espresso-3.jpeg")],
        "features": {
            "Tela premium":            ("crop", "products/ai/hoodie-alo-espresso-front.jpg", (0.20, 0.50, 0.46, 0.74)),
            "Logo bordado":            ("full", "products/gallery/espresso-3.jpeg"),
            "Capucha forrada":         ("full", "products/gallery/espresso-2.jpeg"),
            "Puños y cintura tejidos": ("crop", "products/ai/hoodie-alo-espresso-front.jpg", (0.10, 0.74, 0.40, 0.93)),
            "Bolsillo canguro":        ("crop", "products/ai/hoodie-alo-espresso-front.jpg", (0.30, 0.55, 0.70, 0.80)),
        },
    },
}
GALLERY_ORDER = None  # usa el orden de la lista


def crop_square(img, box):
    W, H = img.size
    x0, y0, x1, y1 = box
    bx0, by0, bx1, by1 = x0 * W, y0 * H, x1 * W, y1 * H
    s = max(bx1 - bx0, by1 - by0)
    cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
    nx0, ny0 = cx - s / 2, cy - s / 2
    nx1, ny1 = cx + s / 2, cy + s / 2
    if nx0 < 0: nx1 -= nx0; nx0 = 0
    if ny0 < 0: ny1 -= ny0; ny0 = 0
    if nx1 > W: nx0 -= (nx1 - W); nx1 = W
    if ny1 > H: ny0 -= (ny1 - H); ny1 = H
    c = img.crop((int(nx0), int(ny0), int(nx1), int(ny1)))
    c = c.resize((1000, 1000), Image.LANCZOS)
    return c.filter(ImageFilter.UnsharpMask(1.6, 110, 2))


class Command(BaseCommand):
    help = "Fotos reales distintas (galería + Calidad) para las hoodies Alo."

    def handle(self, *args, **opts):
        cache = {}

        def load(path):
            if path not in cache:
                cache[path] = Image.open(settings.MEDIA_ROOT / path).convert("RGB")
            return cache[path]

        def render(spec):
            if spec[0] == "full":
                im = load(spec[1]).copy()
                im.thumbnail((1100, 1100), Image.LANCZOS)
                return im
            return crop_square(load(spec[1]), spec[2])

        def jpg(im):
            buf = BytesIO(); im.save(buf, "JPEG", quality=90); return buf.getvalue()

        for slug, cfg in CONFIG.items():
            product = Product.objects.filter(slug=slug).first()
            if not product:
                continue
            color = product.colors.first()
            if not color:
                continue
            color.image = cfg["primary"]
            color.save(update_fields=["image"])

            for old in ProductImage.objects.filter(color=color):
                if old.image:
                    old.image.delete(save=False)
                old.delete()
            for i, spec in enumerate(cfg["gallery"]):
                pi = ProductImage(product=product, color=color, sort_order=i)
                pi.image.save(f"alo-{slug}-{i}.jpg", ContentFile(jpg(render(spec))), save=True)

            for feat in product.features.all():
                spec = cfg["features"].get(feat.title)
                if not spec:
                    continue
                if feat.image:
                    feat.image.delete(save=False)
                feat.image.save(f"calidad-{slug}-{feat.sort_order}.jpg",
                                ContentFile(jpg(render(spec))), save=True)
            self.stdout.write(f"  ✓ {product.name}")
        self.stdout.write(self.style.SUCCESS("Fotos Alo (reales) actualizadas."))
