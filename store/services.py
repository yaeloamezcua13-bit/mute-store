"""Lógica de negocio: crear pedidos, marcar pagados, inventario y correos."""
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from .models import Order, OrderItem, OrderStatus
from .pricing import build_totals
from .shipping import country_name


def create_order_from_cart(cart, data):
    """Crea un pedido (y sus líneas) a partir del carrito y los datos del form."""
    country = data["country"]
    totals = build_totals(cart.subtotal, country)

    order = Order.objects.create(
        full_name=data["full_name"],
        email=data["email"],
        phone=data.get("phone", ""),
        address_line=data["address_line"],
        city=data["city"],
        state=data.get("state", ""),
        postal_code=data["postal_code"],
        country=country,
        country_name=country_name(country),
        subtotal=totals["subtotal"],
        iva_amount=totals["iva"],
        shipping_cost=totals["shipping"],
        total=totals["total"],
        payment_method=data.get("payment_method", ""),
        status=OrderStatus.PENDING,
    )

    for item in cart:
        OrderItem.objects.create(
            order=order,
            product=item["product"],
            product_name=item["product"].name,
            color=item["color"].name,
            size=item["size"],
            unit_price=item["unit_price"],
            quantity=item["quantity"],
            line_total=item["line_total"],
        )
    return order


def mark_order_paid(order, method, reference=""):
    """Marca el pedido como pagado, descuenta inventario y envía confirmación."""
    if order.is_paid:
        return order

    order.status = OrderStatus.PAID
    order.payment_method = method or order.payment_method
    if reference:
        order.payment_reference = reference
    order.paid_at = timezone.now()
    order.save()

    _reduce_stock(order)
    send_order_confirmation(order)
    return order


def _reduce_stock(order):
    from .models import ProductVariant

    for item in order.items.select_related("product"):
        if not item.product:
            continue
        variant = ProductVariant.objects.filter(
            product=item.product, color__name=item.color, size=item.size
        ).first()
        if variant:
            variant.stock = max(0, variant.stock - item.quantity)
            variant.save(update_fields=["stock"])


def send_order_confirmation(order):
    """Envía un correo de confirmación (consola por defecto)."""
    try:
        subject = f"Confirmación de tu pedido {order.order_number} — {settings.STORE_NAME}"
        message = render_to_string("store/email/order_confirmation.txt", {"order": order})
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [order.email],
            fail_silently=True,
        )
    except Exception:
        # No bloquear el flujo de compra si el correo falla.
        pass
