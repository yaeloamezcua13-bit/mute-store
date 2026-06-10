"""Carga los productos iniciales de MUTE. Idempotente: puede correrse varias veces."""
from django.core.management.base import BaseCommand

from store.models import (
    Category,
    Product,
    ProductColor,
    ProductFeature,
    ProductVariant,
)

SIZES = ["XS", "S", "M", "L"]
DEFAULT_STOCK = 25

# Características para el showcase deslizable (tela, logo, capucha, cuello...)
HOODIE_FEATURES = [
    ("🧵", "Tela premium", "Algodón peinado de 380 g/m² con interior afelpado (french terry). Suave, pesada y con caída estructurada."),
    ("🏷️", "Logo bordado", "Logotipo MUTE bordado a hilo, no estampado. Resiste cientos de lavadas sin desgastarse."),
    ("🧥", "Capucha forrada", "Capucha de doble capa con cordón de algodón grueso y ojales metálicos antióxido."),
    ("👕", "Puños y cintura tejidos", "Rib acanalado 2x2 en puños y bastilla que mantiene la forma y no se vence."),
    ("🦘", "Bolsillo canguro", "Bolsillo frontal reforzado con costura doble y entrada amplia."),
]

CREWNECK_FEATURES = [
    ("🧵", "Tela premium", "Algodón peinado de 380 g/m² con interior afelpado. Estructura firme y abrigadora."),
    ("🏷️", "Logo bordado", "Logotipo MUTE bordado en el pecho con acabado tonal."),
    ("⭕", "Cuello redondo reforzado", "Cuello rib 2x2 con cinta de hombro a hombro para que no se deforme."),
    ("👕", "Puños y cintura tejidos", "Acanalado elástico que recupera su forma."),
]

PLAYERA_FEATURES = [
    ("🧵", "Tela peso medio", "Jersey 100% algodón de 220 g/m². Fresca, opaca y con cuerpo."),
    ("🏷️", "Logo bordado", "Detalle MUTE bordado, acabado premium."),
    ("⭕", "Cuello reforzado", "Cuello redondo con rib y costura doble que no se estira."),
    ("✂️", "Corte regular", "Silueta recta moderna, ni muy holgada ni entallada."),
]


class Command(BaseCommand):
    help = "Carga los productos de la tienda MUTE"

    def handle(self, *args, **options):
        self.stdout.write("Sembrando productos MUTE...")

        # Elimina los productos combinados anteriores (ahora son por color)
        Product.objects.filter(
            name__in=["Hoodie Alo Accolade", "Hoodie Essentials", "Playera Essentials"]
        ).delete()

        # Hoodie Alo Accolade — un producto por color
        alo_desc = (
            "El hoodie insignia de MUTE. Tela pesada con caída estructurada, "
            "capucha forrada y logo bordado. Hecho para durar años."
        )
        alo_colors = [
            ("Black", "#1a1a1a", True, "Bestseller"),
            ("Navy", "#1b2a4a", False, ""),
            ("Espresso", "#4b352a", False, ""),
            ("Grey", "#8a8a8a", False, ""),
        ]
        for i, (cname, hexc, feat, badge) in enumerate(alo_colors, start=1):
            self._product(
                name=f"Hoodie Alo · {cname}",
                category=Category.HOODIE_ALO,
                price=2500,
                fabric="Algodón peinado 380 g/m², interior french terry afelpado.",
                description=alo_desc,
                badge=badge,
                featured=feat,
                colors=[(cname, hexc)],
                features=HOODIE_FEATURES,
                sort_order=i,
            )

        self._product(
            name="Crewneck Navy",
            category=Category.CREWNECK,
            price=2000,
            fabric="Algodón peinado 380 g/m², interior afelpado.",
            description=(
                "La sudadera de cuello redondo de MUTE en navy profundo. "
                "Misma tela premium del hoodie, en silueta limpia y atemporal."
            ),
            badge="Nuevo",
            featured=False,
            colors=[("Navy", "#1b2a4a")],
            features=CREWNECK_FEATURES,
            sort_order=5,
        )

        # Hoodie Essentials — un producto por color
        ess_colors = [("Negra", "#1a1a1a"), ("Gris", "#8a8a8a"), ("Blanca", "#f2f0eb")]
        ess_hoodie_desc = (
            "El básico esencial: cómodo, versátil y a buen precio. "
            "El hoodie de diario que combina con todo."
        )
        for i, (cname, hexc) in enumerate(ess_colors, start=6):
            self._product(
                name=f"Hoodie Essentials · {cname}",
                category=Category.HOODIE_ESSENTIALS,
                price=1500,
                fabric="Algodón/poliéster 320 g/m², interior suave.",
                description=ess_hoodie_desc,
                badge="",
                featured=False,
                colors=[(cname, hexc)],
                features=HOODIE_FEATURES[:4],
                sort_order=i,
            )

        # Playera Essentials — un producto por color
        playera_desc = (
            "La playera esencial de MUTE. Algodón con cuerpo, corte regular "
            "y cuello que no se vence."
        )
        for i, (cname, hexc) in enumerate(ess_colors, start=9):
            self._product(
                name=f"Playera Essentials · {cname}",
                category=Category.PLAYERA_ESSENTIALS,
                price=1200,
                fabric="100% algodón 220 g/m², peso medio.",
                description=playera_desc,
                badge="",
                featured=False,
                colors=[(cname, hexc)],
                features=PLAYERA_FEATURES,
                sort_order=i,
            )

        self.stdout.write(self.style.SUCCESS("¡Productos cargados correctamente!"))

    def _product(self, name, category, price, fabric, description, badge,
                 featured, colors, features, sort_order):
        product, _ = Product.objects.update_or_create(
            name=name,
            defaults={
                "category": category,
                "price": price,
                "fabric": fabric,
                "description": description,
                "badge": badge,
                "is_featured": featured,
                "is_active": True,
                "sort_order": sort_order,
            },
        )

        for i, (color_name, hex_code) in enumerate(colors):
            color, _ = ProductColor.objects.update_or_create(
                product=product, name=color_name,
                defaults={"hex_code": hex_code, "sort_order": i},
            )
            for size in SIZES:
                ProductVariant.objects.update_or_create(
                    product=product, color=color, size=size,
                    defaults={"stock": DEFAULT_STOCK},
                )

        for i, (icon, title, desc) in enumerate(features):
            ProductFeature.objects.update_or_create(
                product=product, title=title,
                defaults={"icon": icon, "description": desc, "sort_order": i},
            )

        self.stdout.write(f"  ✓ {name} — ${price:,.0f} ({len(colors)} colores)")
