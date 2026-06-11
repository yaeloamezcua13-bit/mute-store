"""
Fotos web unificadas para TODO el catálogo (Alo + Essentials + Crewneck).

Cada producto: 5 fotos con variedad de ángulos y UN solo fondo (estudio de
concreto cálido) para armonía visual:
  principal = frente (modelo) · galería = [lado, espalda, producto sin modelo, logo]
Calidad: recortes nítidos con encuadre limpio (sin cordones/barbilla), 1000px.

Las imágenes se generan con image-to-image (Gemini) desde las fotos reales,
conservando logos/colores reales. Aquí solo se ASIGNAN rutas a archivos ya
versionados en media/products/{ai/v2, features}. Idempotente; corre en build.sh.

    python manage.py catalog_photos
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from store.models import Product, ProductImage

SLUGS = [
    "hoodie-alo-black", "hoodie-alo-grey", "hoodie-alo-navy", "hoodie-alo-espresso",
    "crewneck-navy",
    "hoodie-essentials-negra", "hoodie-essentials-gris", "hoodie-essentials-blanca",
    "playera-essentials-negra", "playera-essentials-gris", "playera-essentials-blanca",
]
GALLERY_VIEWS = ["side", "back", "prod", "logo"]   # principal = front

# Overrides explícitos (productos cuyas tomas IA salieron con logos incorrectos
# y no se pueden regenerar): se usan fotos REALES fieles en su lugar.
OVERRIDES = {
    # Grey real: logo NEGRO (las IA lo pusieron tonal); gris-2=frente, gris=espalda.
    "hoodie-essentials-gris": {
        "primary": "products/gallery/gris-2.jpeg",
        "gallery": ["products/colors/gris.jpeg"],
    },
    # Crewneck: se quitan la espalda con 'alo' (la original no lo lleva) y la repetida.
    "crewneck-navy": {
        "primary": "products/ai/crewneck-navy-model.jpg",
        "gallery": ["products/ai/crewneck-navy-front.jpg",
                    "products/gallery/navy-2_WXwwQ6L.jpeg"],
    },
}


class Command(BaseCommand):
    help = "Fotos web unificadas (5 ángulos, fondo único) + Calidad para todo el catálogo."

    def handle(self, *args, **opts):
        for slug in SLUGS:
            product = Product.objects.filter(slug=slug).first()
            if not product:
                continue
            color = product.colors.first()
            if not color:
                continue

            if slug in OVERRIDES:
                ov = OVERRIDES[slug]
                color.image = ov["primary"]
                color.save(update_fields=["image"])
                ProductImage.objects.filter(product=product, color=color).delete()
                for i, path in enumerate(ov["gallery"]):
                    ProductImage.objects.create(product=product, color=color, sort_order=i, image=path)
                for feat in product.features.all():
                    cp = f"products/features/calidad-{slug}-{feat.sort_order}.jpg"
                    if (settings.MEDIA_ROOT / cp).exists():
                        feat.image = cp
                        feat.save(update_fields=["image"])
                self.stdout.write(f"  ✓ {product.name} (fotos reales / curado)")
                continue

            # necesita el frente (principal) + al menos 2 vistas de galería disponibles
            def have(v):
                return (settings.MEDIA_ROOT / f"products/ai/v2/{slug}-{v}.jpg").exists()
            gallery_views = [v for v in GALLERY_VIEWS if have(v)]
            if not have("front") or len(gallery_views) < 2:
                self.stdout.write(f"  · {product.name} — sin fotos v2 suficientes, se deja como está")
                continue

            color.image = f"products/ai/v2/{slug}-front.jpg"
            color.save(update_fields=["image"])

            ProductImage.objects.filter(product=product, color=color).delete()
            for i, view in enumerate(gallery_views):
                ProductImage.objects.create(
                    product=product, color=color, sort_order=i,
                    image=f"products/ai/v2/{slug}-{view}.jpg",
                )

            for feat in product.features.all():
                feat.image = f"products/features/calidad-{slug}-{feat.sort_order}.jpg"
                feat.save(update_fields=["image"])

            self.stdout.write(f"  ✓ {product.name}")
        self.stdout.write(self.style.SUCCESS("Catálogo: fotos (5 ángulos, fondo único) + Calidad actualizadas."))
