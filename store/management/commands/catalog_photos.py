"""
Fotos web para Essentials (hoodies + playeras) y Crewneck Navy.

Asigna fotos IA (calidad estudio, mismo look que las Alo) generadas con
image-to-image desde las fotos reales, conservando los logos reales
(ESSENTIALS / FEAR OF GOD, alo). Todo es ASIGNACIÓN de rutas a archivos ya
versionados en media/products/{ai,features}; no procesa imágenes. Idempotente.

  Galería por producto (5 fotos): modelo IA (principal) + producto frente IA +
  producto espalda IA + foto real frente + foto real espalda.
  Calidad (4): recortes nítidos 2K en media/products/features/calidad-<slug>-<i>.jpg

    python manage.py catalog_photos
"""
from django.core.management.base import BaseCommand

from store.models import Product, ProductImage

# slug -> (real_front, real_back)
REAL = {
    "hoodie-essentials-negra":  ("products/colors/negra.jpeg",          "products/gallery/negra-2.jpeg"),
    "hoodie-essentials-gris":   ("products/colors/gris.jpeg",           "products/gallery/gris-2.jpeg"),
    "hoodie-essentials-blanca": ("products/colors/blanca.jpeg",         "products/gallery/blanca-2.jpeg"),
    "playera-essentials-negra": ("products/colors/negra_qke4OBM.jpeg",  "products/gallery/negra-2_Bvypcq0.jpeg"),
    "playera-essentials-gris":  ("products/colors/gris_iCSh2gS.jpeg",   "products/gallery/gris-2_mM3PDpV.jpeg"),
    "playera-essentials-blanca":("products/colors/blanca_oLbbsBF.jpeg", "products/gallery/blanca-2_4WIEAJt.jpeg"),
    "crewneck-navy":            ("products/colors/navy_JWqkkTB.jpeg",   "products/gallery/navy-2_WXwwQ6L.jpeg"),
}


class Command(BaseCommand):
    help = "Fotos web (IA + reales) para Essentials y Crewneck."

    def handle(self, *args, **opts):
        for slug, (real_front, real_back) in REAL.items():
            product = Product.objects.filter(slug=slug).first()
            if not product:
                continue
            color = product.colors.first()
            if not color:
                continue

            # principal = modelo IA
            color.image = f"products/ai/{slug}-model.jpg"
            color.save(update_fields=["image"])

            # galería: limpia filas (NO borra archivos: las reales se reusan)
            ProductImage.objects.filter(product=product, color=color).delete()
            gallery = [
                f"products/ai/{slug}-front.jpg",
                f"products/ai/{slug}-back.jpg",
                real_front,
                real_back,
            ]
            for i, path in enumerate(gallery):
                ProductImage.objects.create(product=product, color=color, sort_order=i, image=path)

            # Calidad: recortes 2K por sort_order
            for feat in product.features.all():
                feat.image = f"products/features/calidad-{slug}-{feat.sort_order}.jpg"
                feat.save(update_fields=["image"])

            self.stdout.write(f"  ✓ {product.name}")
        self.stdout.write(self.style.SUCCESS("Fotos Essentials/Crewneck actualizadas."))
