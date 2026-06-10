"""
Fotos coordinadas de las hoodies Alo:
  - Imagen principal: el model shot de cada color.
  - Galería: recortes de LOGO y BOLSILLO (mismas tomas en cada color).
  - Calidad (5): tela, logo, capucha, puños, bolsillo — recortados de la foto
    de ESE color (color-correcto) y en las mismas posiciones que los demás.

Lee de media/products/ (versionado en el repo) y se regenera en cada despliegue.
Idempotente.

    python manage.py alo_photos
"""
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image, ImageFilter

from store.models import Product, ProductImage

# cajas (x0,y0,x1,y1 en fracciones) por tipo de encuadre
MODEL = {  # model shots AI 896x1152
    "Tela premium":            (0.13, 0.50, 0.45, 0.80),
    "Logo bordado":            (0.45, 0.37, 0.74, 0.55),
    "Capucha forrada":         (0.20, 0.31, 0.78, 0.55),
    "Puños y cintura tejidos": (0.22, 0.85, 0.74, 1.00),
    "Bolsillo canguro":        (0.20, 0.66, 0.76, 0.94),
}
FLAT = {  # navy flat-lay 1024x1024
    "Tela premium":            (0.14, 0.50, 0.40, 0.74),
    "Logo bordado":            (0.47, 0.35, 0.74, 0.53),
    "Capucha forrada":         (0.30, 0.07, 0.70, 0.40),
    "Puños y cintura tejidos": (0.30, 0.80, 0.70, 0.96),
    "Bolsillo canguro":        (0.31, 0.57, 0.71, 0.89),
}
GREY = {  # grey-2 real 1176x1398
    "Tela premium":            (0.09, 0.28, 0.40, 0.54),
    "Logo bordado":            (0.43, 0.14, 0.67, 0.31),
    "Capucha forrada":         (0.13, 0.15, 0.81, 0.34),
    "Puños y cintura tejidos": (0.11, 0.56, 0.59, 0.72),
    "Bolsillo canguro":        (0.24, 0.41, 0.73, 0.66),
}

# slug -> (imagen principal, fuente de recortes, cajas)
COLORS = {
    "hoodie-alo-black":    ("products/colors/mute-black-model.jpg",    "products/colors/mute-black-model.jpg",    MODEL),
    "hoodie-alo-navy":     ("products/colors/mute-navy-model.jpg",     "products/gallery/mute-navy-flat.jpg",     FLAT),
    "hoodie-alo-espresso": ("products/colors/mute-espresso-model.jpg", "products/colors/mute-espresso-model.jpg", MODEL),
    "hoodie-alo-grey":     ("products/gallery/grey-2.jpeg",            "products/gallery/grey-2.jpeg",            GREY),
}
# galería coordinada (mismas tomas en cada color)
GALLERY = ["Logo bordado", "Bolsillo canguro"]


def crop_square(img, box):
    W, H = img.size
    x0, y0, x1, y1 = box
    bx0, by0, bx1, by1 = x0 * W, y0 * H, x1 * W, y1 * H
    s = max(bx1 - bx0, by1 - by0)
    cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
    nx0, ny0, nx1, ny1 = cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2
    if nx0 < 0: nx1 -= nx0; nx0 = 0
    if ny0 < 0: ny1 -= ny0; ny0 = 0
    if nx1 > W: nx0 -= (nx1 - W); nx1 = W
    if ny1 > H: ny0 -= (ny1 - H); ny1 = H
    c = img.crop((int(max(0, nx0)), int(max(0, ny0)), int(nx1), int(ny1)))
    side = min(900, max(c.size))
    c = c.resize((side, side), Image.LANCZOS)
    return c.filter(ImageFilter.UnsharpMask(2.0, 130, 2))


class Command(BaseCommand):
    help = "Fotos coordinadas y color-correctas de las hoodies Alo."

    def handle(self, *args, **opts):
        cache = {}

        def src(path):
            if path not in cache:
                cache[path] = Image.open(settings.MEDIA_ROOT / path).convert("RGB")
            return cache[path]

        def save_jpg(crop):
            buf = BytesIO(); crop.save(buf, "JPEG", quality=90); return buf.getvalue()

        for slug, (primary, crop_src, boxes) in COLORS.items():
            product = Product.objects.filter(slug=slug).first()
            if not product:
                continue
            color = product.colors.first()
            if not color:
                continue
            color.image = primary
            color.save(update_fields=["image"])
            img = src(crop_src)

            # galería coordinada (borra archivos viejos para no acumular basura)
            for old in ProductImage.objects.filter(color=color):
                if old.image:
                    old.image.delete(save=False)
                old.delete()
            for i, feat_name in enumerate(GALLERY):
                data = save_jpg(crop_square(img, boxes[feat_name]))
                pi = ProductImage(product=product, color=color, sort_order=i)
                pi.image.save(f"alo-{slug}-{i}.jpg", ContentFile(data), save=True)

            # calidad (5) color-correctos
            for feat in product.features.all():
                if feat.title not in boxes:
                    continue
                data = save_jpg(crop_square(img, boxes[feat.title]))
                if feat.image:
                    feat.image.delete(save=False)
                feat.image.save(f"calidad-{slug}-{feat.sort_order}.jpg",
                                ContentFile(data), save=True)
            self.stdout.write(f"  ✓ {product.name}")
        self.stdout.write(self.style.SUCCESS("Fotos Alo coordinadas."))
