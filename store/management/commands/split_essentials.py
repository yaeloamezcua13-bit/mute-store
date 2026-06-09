"""
Separa los productos combinados de Essentials en un producto por color
(igual que las Hoodie Alo). Reasigna el color, sus variantes y su galería al
nuevo producto, copia las características y borra el combinado.

Preserva las fotos ya cargadas (no re-importa). Idempotente: si ya están
separados, no hace nada.

    python manage.py split_essentials
"""
from django.core.management.base import BaseCommand

from store.models import Product, ProductFeature

# slug del combinado -> sort_order del primer color
TARGETS = {
    "hoodie-essentials": 6,
    "playera-essentials": 9,
}


class Command(BaseCommand):
    help = "Separa Hoodie/Playera Essentials en un producto por color"

    def handle(self, *args, **opts):
        for base_slug, start_order in TARGETS.items():
            base = Product.objects.filter(slug=base_slug).first()
            if not base:
                self.stdout.write(f"  {base_slug}: ya separado o inexistente; salto.")
                continue

            feats = [
                (f.icon, f.title, f.description, f.sort_order)
                for f in base.features.all()
            ]

            for i, color in enumerate(list(base.colors.all())):
                new = Product.objects.create(
                    name=f"{base.name} · {color.name}",
                    category=base.category,
                    price=base.price,
                    fabric=base.fabric,
                    description=base.description,
                    badge=base.badge,
                    is_featured=False,
                    is_active=True,
                    sort_order=start_order + i,
                )
                # mover variantes y galería de ese color al nuevo producto
                color.variants.update(product=new)
                color.gallery.update(product=new)
                # mover el color en sí
                color.product = new
                color.sort_order = 0
                color.save(update_fields=["product", "sort_order"])
                # características propias (sin imagen; las pone crop_quality)
                for icon, title, desc, so in feats:
                    ProductFeature.objects.create(
                        product=new, icon=icon, title=title,
                        description=desc, sort_order=so,
                    )
                self.stdout.write(self.style.SUCCESS(f"  ✓ {new.name}"))

            base.delete()  # ya sin colores/variantes; sus features caen en cascada

        self.stdout.write(self.style.SUCCESS("\n¡Essentials separadas por color!"))
