"""
Asigna las fotos de calidad estudio a las hoodies Alo:
imagen principal (color.image) + galería (ProductImage por color).

Idempotente: reconstruye la galería cada vez. Seguro de correr en cada despliegue.

    python manage.py upgrade_photos
"""
from django.core.management.base import BaseCommand

from store.models import Product, ProductImage

# slug -> (imagen principal, [galería])
SETUP = {
    "hoodie-alo-black": (
        "products/colors/mute-black-model.jpg",
        ["products/gallery/black-2.jpeg", "products/gallery/black-4.jpeg"],
    ),
    "hoodie-alo-espresso": (
        "products/colors/mute-espresso-model.jpg",
        ["products/gallery/espresso-2.jpeg"],
    ),
    "hoodie-alo-navy": (
        "products/colors/mute-navy-model.jpg",
        ["products/gallery/mute-navy-flat.jpg", "products/gallery/mute-navy-detail.jpg"],
    ),
    "hoodie-alo-grey": (
        "products/gallery/grey-2.jpeg",
        ["products/gallery/mute-grey-detail.jpg"],
    ),
}


class Command(BaseCommand):
    help = "Asigna fotos de estudio (principal + galería) a las hoodies Alo."

    def handle(self, *args, **opts):
        for slug, (primary, gallery) in SETUP.items():
            product = Product.objects.filter(slug=slug).first()
            if not product:
                continue
            color = product.colors.first()
            if not color:
                continue
            color.image = primary
            color.save(update_fields=["image"])
            ProductImage.objects.filter(color=color).delete()
            for i, path in enumerate(gallery):
                ProductImage.objects.create(
                    product=product, color=color, image=path, sort_order=i
                )
            self.stdout.write(f"{slug}: principal + {len(gallery)} en galería")
        self.stdout.write(self.style.SUCCESS("Fotos de productos actualizadas."))
