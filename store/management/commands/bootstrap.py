"""
Carga inicial para el despliegue: si la base de datos no tiene productos,
carga el catálogo desde el fixture. Idempotente: no pisa datos existentes.

    python manage.py bootstrap
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand

from store.models import Product


class Command(BaseCommand):
    help = "Carga el catálogo inicial si la BD está vacía (para despliegue)."

    def handle(self, *args, **opts):
        if Product.objects.exists():
            self.stdout.write("Catálogo ya presente; no se carga de nuevo.")
            return
        call_command("loaddata", "catalog")
        self.stdout.write(self.style.SUCCESS("¡Catálogo cargado desde el fixture!"))
