"""
Genera imágenes de producto con nano banana (Gemini 2.5 Flash Image)
y las adjunta automáticamente a la base de datos.

Uso:
    export GEMINI_API_KEY=tu_llave
    python manage.py generate_images            # todos los productos + colores
    python manage.py generate_images --features # + fotos de detalle (tela, logo...)
    python manage.py generate_images --product hoodie-alo-accolade

Obtén tu llave gratis en https://aistudio.google.com/apikey
"""
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError

from store.models import Product, ProductImage

MODEL = "gemini-2.5-flash-image"

STYLE = (
    "premium streetwear e-commerce product photography, studio lighting, "
    "deep charcoal seamless background, soft shadows, high detail fabric texture, "
    "minimal, centered, ultra sharp, 4k, no text, no watermark"
)


class Command(BaseCommand):
    help = "Genera imágenes de producto con nano banana (Gemini)"

    def add_arguments(self, parser):
        parser.add_argument("--product", help="slug de un producto específico")
        parser.add_argument("--features", action="store_true",
                            help="También genera fotos de detalle (tela, logo, capucha...)")

    def handle(self, *args, **opts):
        if not settings.GEMINI_API_KEY:
            raise CommandError(
                "Falta GEMINI_API_KEY. Consíguela en https://aistudio.google.com/apikey "
                "y agrégala a tu archivo .env"
            )
        try:
            from google import genai
        except ImportError:
            raise CommandError("Instala el SDK: pip install google-genai")

        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

        qs = Product.objects.all()
        if opts["product"]:
            qs = qs.filter(slug=opts["product"])
            if not qs.exists():
                raise CommandError(f"No existe el producto '{opts['product']}'")

        for product in qs:
            self.stdout.write(f"\n📦 {product.name}")
            garment = self._garment(product)
            for i, color in enumerate(product.colors.all()):
                prompt = (
                    f"A {color.name.lower()} {garment} by streetwear brand MUTE, "
                    f"folded neatly and also shown from the front, {STYLE}"
                )
                img = self._generate(prompt)
                if img:
                    fname = f"{product.slug}-{color.name.lower()}.png"
                    color.image.save(fname, img, save=True)
                    ProductImage.objects.get_or_create(
                        product=product, alt_text=f"{product.name} {color.name}",
                        defaults={"is_primary": i == 0},
                    )
                    # adjunta la imagen a la galería principal
                    gallery = product.images.first()
                    if gallery and not gallery.image:
                        gallery.image.save(fname, img, save=True)
                    self.stdout.write(self.style.SUCCESS(f"   ✓ {color.name}"))

            if opts["features"]:
                for feat in product.features.all():
                    prompt = (
                        f"Extreme close-up macro shot of the {feat.title.lower()} "
                        f"of a {garment} ({feat.description[:80]}), {STYLE}"
                    )
                    img = self._generate(prompt)
                    if img:
                        feat.image.save(f"{product.slug}-{feat.sort_order}.png", img, save=True)
                        self.stdout.write(self.style.SUCCESS(f"   ✓ detalle: {feat.title}"))

        self.stdout.write(self.style.SUCCESS("\n¡Listo! Imágenes generadas y adjuntadas."))

    def _garment(self, product):
        if "playera" in product.category:
            return "heavyweight cotton t-shirt"
        if "crewneck" in product.category:
            return "premium crewneck sweatshirt"
        return "premium heavyweight hoodie"

    def _generate(self, prompt):
        """Llama a nano banana y devuelve un ContentFile con la imagen (o None)."""
        try:
            resp = self.client.models.generate_content(model=MODEL, contents=[prompt])
            for part in resp.candidates[0].content.parts:
                inline = getattr(part, "inline_data", None)
                if inline and inline.data:
                    return ContentFile(inline.data)
            self.stdout.write(self.style.WARNING("   (sin imagen en la respuesta)"))
        except Exception as exc:  # noqa: BLE001
            self.stdout.write(self.style.ERROR(f"   error: {exc}"))
        return None
