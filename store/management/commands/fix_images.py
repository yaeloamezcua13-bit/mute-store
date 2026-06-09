"""
Ajustes puntuales de fotos pedidos por el cliente:
  - Recorta la franja blanca del borde izquierdo en los flat-lay (negra, gris, navy).
  - Quita la 2da y 3ra foto de galería de la hoodie negra (baja calidad).
  - Navy: la imagen principal pasa a ser el flat-lay; la de modelo va a galería.
  - Verifica que la gris tenga sus dos fotos (flat-lay + modelo).

    python manage.py fix_images
"""
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image

from store.models import Product


def _col_brightness(px, x, H):
    rows = range(0, H, 5)
    return sum(px[x, y] for y in rows) / len(rows)


def trim_left_strip(path):
    """Detecta y recorta una franja clara pegada al borde izquierdo (fondo del
    flat-lay). Busca un 'escalón': columnas iniciales claras que bajan de golpe
    al fondo real. Devuelve bytes JPEG recortados, o None si no hay franja."""
    im = Image.open(path).convert("RGB")
    g = im.convert("L")
    W, H = g.size
    px = g.load()
    base = _col_brightness(px, 0, H)
    cut = 0
    for x in range(1, int(W * 0.08)):
        if _col_brightness(px, x, H) <= base - 24:
            cut = x
            break
    if cut < 1:
        return None  # sin escalón: borde uniforme, no hay franja
    cut = min(cut + 1, int(W * 0.08))
    buf = BytesIO()
    im.crop((cut, 0, W, H)).save(buf, "JPEG", quality=92)
    return buf.getvalue()


class Command(BaseCommand):
    help = "Arregla fotos: franja blanca, galería negra, principal navy."

    def handle(self, *args, **opts):
        # 1) Quitar 2da y 3ra foto de galería de la negra (black-2, black-3)
        black = Product.objects.get(slug="hoodie-alo-black")
        bc = black.colors.first()
        removed = 0
        for g in list(bc.gallery.all()):
            if "black-2" in g.image.name or "black-3" in g.image.name:
                g.image.delete(save=False)
                g.delete()
                removed += 1
        self.stdout.write(f"  Negra: {removed} fotos de galería quitadas.")

        # 2) Navy: principal <-> flat-lay (navy-3). Swap de punteros (sin copiar).
        navy = Product.objects.get(slug="hoodie-alo-navy")
        nc = navy.colors.first()
        flat_row = nc.gallery.filter(image__contains="navy-3").first()
        if flat_row:
            worn_name = nc.image.name
            flat_name = flat_row.image.name
            nc.image.name = flat_name
            nc.save(update_fields=["image"])
            flat_row.image.name = worn_name
            flat_row.sort_order = 0
            flat_row.save(update_fields=["image", "sort_order"])
            back = nc.gallery.filter(image__contains="navy-back").first()
            if back:
                back.sort_order = 1
                back.save(update_fields=["sort_order"])
            self.stdout.write("  Navy: principal cambiada al flat-lay; modelo a galería.")
        else:
            self.stdout.write("  Navy: no se encontró el flat-lay (navy-3); sin cambios.")

        # 3) Recortar franja blanca izquierda en los flat-lay principales
        for slug in ["hoodie-alo-black", "hoodie-alo-grey", "hoodie-alo-navy"]:
            color = Product.objects.get(slug=slug).colors.first()
            data = trim_left_strip(color.image.path)
            if data:
                color.image.delete(save=False)
                color.image.save(f"{slug}-clean.jpg", ContentFile(data), save=True)
                self.stdout.write(f"  {slug}: franja izquierda recortada.")
            else:
                self.stdout.write(f"  {slug}: sin franja, intacta.")

        # 4) Verificar gris (flat-lay + modelo)
        grey = Product.objects.get(slug="hoodie-alo-grey")
        gc = grey.colors.first()
        n_grey = (1 if gc.image else 0) + gc.gallery.count()
        self.stdout.write(f"  Gris: {n_grey} foto(s) en total (principal + galería).")

        self.stdout.write(self.style.SUCCESS("\n¡Listo! Fotos ajustadas."))
