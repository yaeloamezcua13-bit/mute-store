"""Carrito de compras basado en la sesión del navegador."""
from decimal import Decimal

from .models import ProductVariant
from .pricing import money, split_iva

CART_SESSION_KEY = "cart"


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(CART_SESSION_KEY)
        if cart is None:
            cart = self.session[CART_SESSION_KEY] = {}
        self.cart = cart

    def save(self):
        self.session[CART_SESSION_KEY] = self.cart
        self.session.modified = True

    def add(self, variant, quantity=1, update=False):
        """Agrega una variante (color+talla) o actualiza su cantidad."""
        key = str(variant.id)
        if key not in self.cart:
            self.cart[key] = {"quantity": 0}
        if update:
            self.cart[key]["quantity"] = quantity
        else:
            self.cart[key]["quantity"] += quantity
        # Limita a stock disponible
        if self.cart[key]["quantity"] > variant.stock:
            self.cart[key]["quantity"] = variant.stock
        if self.cart[key]["quantity"] <= 0:
            self.remove(variant.id)
        else:
            self.save()

    def update(self, variant_id, quantity):
        key = str(variant_id)
        if key in self.cart:
            if quantity <= 0:
                self.remove(variant_id)
            else:
                self.cart[key]["quantity"] = quantity
                self.save()

    def remove(self, variant_id):
        key = str(variant_id)
        if key in self.cart:
            del self.cart[key]
            self.save()

    def clear(self):
        self.session[CART_SESSION_KEY] = {}
        self.session.modified = True

    def _variants(self):
        ids = [int(k) for k in self.cart.keys()]
        return ProductVariant.objects.filter(id__in=ids).select_related(
            "product", "color"
        )

    def __iter__(self):
        variants = {v.id: v for v in self._variants()}
        for key, item in list(self.cart.items()):
            vid = int(key)
            variant = variants.get(vid)
            if variant is None:
                # La variante ya no existe; la quitamos del carrito.
                self.remove(vid)
                continue
            quantity = item["quantity"]
            unit_price = variant.product.price
            yield {
                "variant": variant,
                "product": variant.product,
                "color": variant.color,
                "size": variant.size,
                "quantity": quantity,
                "unit_price": unit_price,
                "line_total": money(unit_price * quantity),
                "image": (
                    variant.color.image
                    or (variant.product.primary_image.image
                        if variant.product.primary_image else None)
                ),
            }

    def __len__(self):
        return sum(item["quantity"] for item in self.cart.values())

    @property
    def subtotal(self):
        return money(sum(item["line_total"] for item in self))

    @property
    def iva(self):
        return split_iva(self.subtotal)["iva"]

    @property
    def base(self):
        return split_iva(self.subtotal)["base"]

    @property
    def is_empty(self):
        return len(self) == 0
