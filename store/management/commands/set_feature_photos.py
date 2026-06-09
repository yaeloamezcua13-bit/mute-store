"""
Asigna fotos reales a las características del showcase (sección Calidad),
tomándolas de la carpeta fotos/<slug>/.

    python manage.py set_feature_photos
"""
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from store.models import Product

# producto -> { título de la característica : archivo en fotos/<slug>/ }
MAP = {
    "hoodie-alo-accolade": {
        "Tela premium": "grey.jpg",
        "Logo bordado": "espresso-3.jpeg",      # close-up del logo alo
        "Capucha forrada": "espresso-2.jpeg",   # capucha puesta
        "Puños y cintura tejidos": "espresso.jpg",
        "Bolsillo canguro": "black.jpg",
    },
    "crewneck-navy": {
        "Tela premium": "navy.jpeg",
        "Logo bordado": "navy.jpeg",
        "Cuello redondo reforzado": "navy-2.jpeg",
        "Puños y cintura tejidos": "navy-2.jpeg",
    },
    "hoodie-essentials": {
        "Tela premium": "negra.jpeg",
        "Logo bordado": "gris.jpeg",
        "Capucha forrada": "negra-2.jpeg",      # espalda: capucha visible
        "Puños y cintura tejidos": "blanca-2.jpeg",
    },
    "playera-essentials": {
        "Tela peso medio": "negra.jpeg",
        "Logo bordado": "gris.jpeg",
        "Cuello reforzado": "blanca.jpeg",
        "Corte regular": "negra-2.jpeg",        # espalda: corte/caída
    },
}


class Command(BaseCommand):
    help = "Asigna fotos a las características del showcase (Calidad)"

    def handle(self, *args, **opts):
        base = Path(settings.BASE_DIR) / "fotos"
        total = 0
        for product in Product.objects.all():
            mapping = MAP.get(product.slug)
            if not mapping:
                continue
            self.stdout.write(f"\n📦 {product.name}")
            for feat in product.features.all():
                fname = mapping.get(feat.title)
                if not fname:
                    continue
                path = base / product.slug / fname
                if not path.exists():
                    self.stdout.write(self.style.WARNING(f"   — falta {path.name}"))
                    continue
                if feat.image:
                    feat.image.delete(save=False)
                with open(path, "rb") as fh:
                    feat.image.save(f"{product.slug}-{feat.sort_order}-{fname}",
                                    ContentFile(fh.read()), save=True)
                total += 1
                self.stdout.write(self.style.SUCCESS(f"   ✓ {feat.title}: {fname}"))
        self.stdout.write(self.style.SUCCESS(f"\n¡Listo! {total} fotos asignadas a Calidad."))
