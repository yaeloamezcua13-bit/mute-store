"""
Normaliza las tallas de toda la tienda:
  - Elimina las variantes XL y XXL (ya no se ofrecen).
  - Crea la talla XS donde falte, copiando el stock de la talla S (o 25).

Idempotente: seguro de correr en cada despliegue.

    python manage.py normalize_sizes
"""
from django.core.management.base import BaseCommand

from store.models import ProductVariant


class Command(BaseCommand):
    help = "Elimina XL/XXL y crea XS en toda la tienda (idempotente)."

    def handle(self, *args, **opts):
        deleted, _ = ProductVariant.objects.filter(size__in=["XL", "XXL"]).delete()

        created = 0
        combos = ProductVariant.objects.values_list("product_id", "color_id").distinct()
        for product_id, color_id in combos:
            exists = ProductVariant.objects.filter(
                product_id=product_id, color_id=color_id, size="XS"
            ).exists()
            if exists:
                continue
            s = ProductVariant.objects.filter(
                product_id=product_id, color_id=color_id, size="S"
            ).first()
            ProductVariant.objects.create(
                product_id=product_id,
                color_id=color_id,
                size="XS",
                stock=s.stock if s else 25,
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Tallas normalizadas — XL/XXL eliminadas: {deleted} · XS creadas: {created}"
        ))
