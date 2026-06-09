"""Modelos de datos de la tienda MUTE."""
from decimal import Decimal
import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


SIZE_CHOICES = [
    ("XS", "XS"),
    ("S", "S"),
    ("M", "M"),
    ("L", "L"),
    ("XL", "XL"),
    ("XXL", "XXL"),
]


class Category(models.TextChoices):
    HOODIE_ALO = "hoodie_alo", "Hoodie Alo Accolade"
    CREWNECK = "crewneck", "Crewneck"
    HOODIE_ESSENTIALS = "hoodie_essentials", "Hoodie Essentials"
    PLAYERA_ESSENTIALS = "playera_essentials", "Playera Essentials"


class Product(models.Model):
    """Una línea de producto (con varios colores y tallas)."""

    name = models.CharField("Nombre", max_length=120)
    slug = models.SlugField("Slug", max_length=140, unique=True, blank=True)
    category = models.CharField(
        "Categoría", max_length=40, choices=Category.choices
    )
    description = models.TextField("Descripción", blank=True)
    fabric = models.CharField(
        "Tela / material", max_length=200, blank=True,
        help_text="Ej. Algodón peinado 380gsm, interior afelpado.",
    )
    price = models.DecimalField(
        "Precio (IVA incluido)", max_digits=10, decimal_places=2
    )
    badge = models.CharField(
        "Etiqueta", max_length=30, blank=True,
        help_text="Ej. Bestseller, Nuevo, Edición limitada.",
    )
    is_active = models.BooleanField("Activo", default=True)
    is_featured = models.BooleanField("Destacado", default=False)
    sort_order = models.PositiveIntegerField("Orden", default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("store:product_detail", args=[self.slug])

    @property
    def primary_image(self):
        img = self.images.filter(is_primary=True).first() or self.images.first()
        return img

    @property
    def price_breakdown(self):
        """Desglosa el IVA contenido en el precio (precio ya incluye IVA)."""
        rate = Decimal(str(settings.IVA_RATE))
        base = (self.price / (Decimal("1") + rate)).quantize(Decimal("0.01"))
        iva = (self.price - base).quantize(Decimal("0.01"))
        return {"base": base, "iva": iva, "total": self.price}

    @property
    def total_stock(self):
        return sum(v.stock for v in self.variants.all())


class ProductColor(models.Model):
    """Color disponible de un producto, con su propia imagen."""

    product = models.ForeignKey(
        Product, related_name="colors", on_delete=models.CASCADE
    )
    name = models.CharField("Color", max_length=40)
    hex_code = models.CharField(
        "Código HEX", max_length=7, default="#1a1a1a",
        help_text="Ej. #000000",
    )
    image = models.ImageField(
        "Imagen del color", upload_to="products/colors/", blank=True, null=True
    )
    sort_order = models.PositiveIntegerField("Orden", default=0)

    class Meta:
        verbose_name = "Color de producto"
        verbose_name_plural = "Colores de producto"
        ordering = ["sort_order", "name"]
        unique_together = ("product", "name")

    def __str__(self):
        return f"{self.product.name} — {self.name}"


class ProductVariant(models.Model):
    """Combinación color + talla con su inventario."""

    product = models.ForeignKey(
        Product, related_name="variants", on_delete=models.CASCADE
    )
    color = models.ForeignKey(
        ProductColor, related_name="variants", on_delete=models.CASCADE
    )
    size = models.CharField("Talla", max_length=4, choices=SIZE_CHOICES)
    stock = models.PositiveIntegerField("Inventario", default=0)
    sku = models.CharField("SKU", max_length=40, blank=True, unique=True)

    class Meta:
        verbose_name = "Variante (color + talla)"
        verbose_name_plural = "Variantes (color + talla)"
        ordering = ["color__sort_order", "size"]
        unique_together = ("product", "color", "size")

    def __str__(self):
        return f"{self.product.name} — {self.color.name} — {self.size}"

    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = f"{slugify(self.product.name)[:12]}-{slugify(self.color.name)[:6]}-{self.size}".upper()
        super().save(*args, **kwargs)

    @property
    def in_stock(self):
        return self.stock > 0


class ProductImage(models.Model):
    """Imágenes de galería del producto."""

    product = models.ForeignKey(
        Product, related_name="images", on_delete=models.CASCADE
    )
    color = models.ForeignKey(
        ProductColor, related_name="gallery", null=True, blank=True,
        on_delete=models.CASCADE,
    )
    image = models.ImageField("Imagen", upload_to="products/gallery/")
    alt_text = models.CharField("Texto alternativo", max_length=140, blank=True)
    is_primary = models.BooleanField("Principal", default=False)
    sort_order = models.PositiveIntegerField("Orden", default=0)

    class Meta:
        verbose_name = "Imagen de producto"
        verbose_name_plural = "Imágenes de producto"
        ordering = ["-is_primary", "sort_order"]

    def __str__(self):
        return f"Imagen de {self.product.name}"


class ProductFeature(models.Model):
    """Característica destacada para el showcase deslizable (tela, logo, capucha, cuello)."""

    product = models.ForeignKey(
        Product, related_name="features", on_delete=models.CASCADE
    )
    title = models.CharField("Título", max_length=60)
    description = models.TextField("Descripción", blank=True)
    image = models.ImageField(
        "Imagen", upload_to="products/features/", blank=True, null=True
    )
    icon = models.CharField(
        "Icono (emoji o nombre)", max_length=20, blank=True,
        help_text="Ej. 🧵, 🏷️, 🧥",
    )
    sort_order = models.PositiveIntegerField("Orden", default=0)

    class Meta:
        verbose_name = "Característica destacada"
        verbose_name_plural = "Características destacadas"
        ordering = ["sort_order"]

    def __str__(self):
        return f"{self.product.name} — {self.title}"


# ==========================================================================
# Pedidos
# ==========================================================================
class OrderStatus(models.TextChoices):
    PENDING = "pending", "Pendiente de pago"
    PAID = "paid", "Pagado"
    PROCESSING = "processing", "En preparación"
    SHIPPED = "shipped", "Enviado"
    DELIVERED = "delivered", "Entregado"
    CANCELLED = "cancelled", "Cancelado"


class PaymentMethod(models.TextChoices):
    STRIPE = "stripe", "Stripe (tarjeta)"
    MERCADOPAGO = "mercadopago", "MercadoPago"
    SIMULATED = "simulated", "Simulado (prueba)"


def generate_order_number():
    return f"MUTE-{uuid.uuid4().hex[:8].upper()}"


class Order(models.Model):
    """Pedido realizado por un cliente. Se guarda automáticamente en la BD."""

    order_number = models.CharField(
        "Número de orden", max_length=20, unique=True,
        default=generate_order_number, editable=False,
    )
    status = models.CharField(
        "Estado", max_length=20, choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
    )

    # Datos del cliente
    full_name = models.CharField("Nombre completo", max_length=120)
    email = models.EmailField("Correo")
    phone = models.CharField("Teléfono", max_length=30, blank=True)

    # Dirección de envío
    address_line = models.CharField("Dirección", max_length=200)
    city = models.CharField("Ciudad", max_length=80)
    state = models.CharField("Estado / Provincia", max_length=80, blank=True)
    postal_code = models.CharField("Código postal", max_length=20)
    country = models.CharField("País (código)", max_length=2, default="MX")
    country_name = models.CharField("País", max_length=80, default="México")

    # Importes (todos en MXN)
    subtotal = models.DecimalField("Subtotal (IVA incl.)", max_digits=10, decimal_places=2)
    iva_amount = models.DecimalField("IVA incluido", max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField("Envío", max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField("Total", max_digits=10, decimal_places=2)

    # Pago
    payment_method = models.CharField(
        "Método de pago", max_length=20, choices=PaymentMethod.choices, blank=True
    )
    payment_reference = models.CharField(
        "Referencia de pago", max_length=200, blank=True
    )
    paid_at = models.DateTimeField("Pagado el", null=True, blank=True)

    notes = models.TextField("Notas internas", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order_number} — {self.full_name}"

    @property
    def is_paid(self):
        return self.status in (
            OrderStatus.PAID, OrderStatus.PROCESSING,
            OrderStatus.SHIPPED, OrderStatus.DELIVERED,
        )

    @property
    def item_count(self):
        return sum(i.quantity for i in self.items.all())

    @property
    def base_amount(self):
        """Subtotal sin IVA (base gravable)."""
        return self.subtotal - self.iva_amount


class OrderItem(models.Model):
    """Línea de un pedido. Guarda una 'foto' del producto al momento de compra."""

    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, blank=True
    )
    product_name = models.CharField("Producto", max_length=120)
    color = models.CharField("Color", max_length=40, blank=True)
    size = models.CharField("Talla", max_length=4, blank=True)
    unit_price = models.DecimalField("Precio unitario", max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField("Cantidad", default=1)
    line_total = models.DecimalField("Total línea", max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Artículo del pedido"
        verbose_name_plural = "Artículos del pedido"

    def __str__(self):
        return f"{self.quantity}× {self.product_name} ({self.color}/{self.size})"
