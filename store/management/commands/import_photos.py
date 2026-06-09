"""
Importa fotos reales desde la carpeta fotos/ y las adjunta a cada producto/color.

Estructura esperada (una subcarpeta por producto, archivos por color):

    fotos/
      hoodie-alo-accolade/  black.jpg  navy.jpg  espresso.jpg  grey.jpg
      crewneck-navy/        navy.jpg
      hoodie-essentials/    negra.jpg  gris.jpg  blanca.jpg
      playera-essentials/   negra.jpg  gris.jpg  blanca.jpg

La foto principal (de frente) se llama como el color: black.jpg
Fotos extra (espalda, detalle): black-2.jpg, black-espalda.jpg, etc.

    python manage.py import_photos
    python manage.py import_photos --dir /ruta/a/fotos
"""
import unicodedata
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from store.models import Product, ProductImage

EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return s.lower().strip()


class Command(BaseCommand):
    help = "Importa fotos reales desde fotos/ y las adjunta a productos/colores"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dir", default=str(settings.BASE_DIR / "fotos"),
            help="Carpeta con las fotos (por defecto: fotos/)",
        )

    def handle(self, *args, **opts):
        base = Path(opts["dir"])
        if not base.exists():
            self.stdout.write(self.style.ERROR(f"No existe la carpeta: {base}"))
            return

        total = 0
        for product in Product.objects.all():
            folder = base / product.slug
            if not folder.is_dir():
                continue
            self.stdout.write(f"\n📦 {product.name}")
            files = [f for f in folder.iterdir() if f.suffix.lower() in EXTS]

            # Limpia galería previa para poder re-importar sin duplicar
            for old in product.images.all():
                old.image.delete(save=False)
                old.delete()

            for color in product.colors.all():
                ckey = norm(color.name)
                matches = [
                    f for f in files
                    if norm(f.stem) == ckey
                    or norm(f.stem).startswith(ckey + "-")
                    or norm(f.stem).startswith(ckey + "_")
                ]
                # La foto de frente (nombre exacto del color) va primero
                matches.sort(key=lambda f: (norm(f.stem) != ckey, f.name))
                if not matches:
                    self.stdout.write(self.style.WARNING(f"   — {color.name}: sin foto"))
                    continue

                # Principal (de frente) -> imagen del color
                main = matches[0]
                if color.image:
                    color.image.delete(save=False)
                with open(main, "rb") as fh:
                    color.image.save(main.name, ContentFile(fh.read()), save=True)
                total += 1
                self.stdout.write(self.style.SUCCESS(f"   ✓ {color.name}: {main.name}"))

                # Fotos extra -> galería del color
                for i, extra in enumerate(matches[1:], start=1):
                    with open(extra, "rb") as fh:
                        img = ProductImage(product=product, color=color,
                                           sort_order=i,
                                           alt_text=f"{product.name} {color.name}")
                        img.image.save(extra.name, ContentFile(fh.read()), save=True)
                    total += 1
                    self.stdout.write(f"      + extra: {extra.name}")

        self.stdout.write(self.style.SUCCESS(f"\n¡Listo! {total} fotos importadas."))
