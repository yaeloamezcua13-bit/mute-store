"""
Integración de pagos: Stripe Checkout y MercadoPago Checkout Pro.

Si no hay llaves configuradas, la tienda opera en MODO SIMULADO:
crea la orden y muestra la confirmación sin cobrar realmente.
"""
from decimal import Decimal

from django.conf import settings
from django.urls import reverse


def stripe_enabled():
    return bool(settings.STRIPE_SECRET_KEY)


def mercadopago_enabled():
    return bool(settings.MERCADOPAGO_ACCESS_TOKEN)


def _abs(request, name, *args):
    return request.build_absolute_uri(reverse(name, args=args))


def _cents(amount):
    return int((Decimal(str(amount)) * 100).quantize(Decimal("1")))


# --------------------------------------------------------------------------
# Stripe
# --------------------------------------------------------------------------
def create_stripe_session(order, request):
    """Crea una sesión de Stripe Checkout y devuelve la URL de pago."""
    import stripe

    stripe.api_key = settings.STRIPE_SECRET_KEY

    line_items = []
    for item in order.items.all():
        line_items.append({
            "price_data": {
                "currency": settings.CURRENCY.lower(),
                "product_data": {
                    "name": f"{item.product_name} — {item.color} / {item.size}",
                },
                "unit_amount": _cents(item.unit_price),  # IVA incluido
            },
            "quantity": item.quantity,
        })

    if order.shipping_cost and order.shipping_cost > 0:
        line_items.append({
            "price_data": {
                "currency": settings.CURRENCY.lower(),
                "product_data": {"name": "Envío internacional"},
                "unit_amount": _cents(order.shipping_cost),
            },
            "quantity": 1,
        })

    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=line_items,
        customer_email=order.email,
        metadata={"order_number": order.order_number},
        success_url=_abs(request, "store:payment_success", order.order_number)
        + "?provider=stripe&session_id={CHECKOUT_SESSION_ID}",
        cancel_url=_abs(request, "store:payment_cancel", order.order_number),
    )
    order.payment_reference = session.id
    order.save(update_fields=["payment_reference"])
    return session.url


# --------------------------------------------------------------------------
# MercadoPago
# --------------------------------------------------------------------------
def create_mercadopago_preference(order, request):
    """Crea una preferencia de MercadoPago y devuelve la URL de pago."""
    import mercadopago

    sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)

    items = []
    for item in order.items.all():
        items.append({
            "title": f"{item.product_name} — {item.color} / {item.size}",
            "quantity": item.quantity,
            "unit_price": float(item.unit_price),
            "currency_id": settings.CURRENCY,
        })
    if order.shipping_cost and order.shipping_cost > 0:
        items.append({
            "title": "Envío internacional",
            "quantity": 1,
            "unit_price": float(order.shipping_cost),
            "currency_id": settings.CURRENCY,
        })

    preference_data = {
        "items": items,
        "payer": {"name": order.full_name, "email": order.email},
        "external_reference": order.order_number,
        "back_urls": {
            "success": _abs(request, "store:payment_success", order.order_number)
            + "?provider=mercadopago",
            "failure": _abs(request, "store:payment_cancel", order.order_number),
            "pending": _abs(request, "store:payment_success", order.order_number)
            + "?provider=mercadopago",
        },
        "statement_descriptor": settings.STORE_NAME,
    }
    # auto_return exige una URL pública: MercadoPago rechaza localhost/127.0.0.1
    host = request.get_host()
    if not ("127.0.0.1" in host or "localhost" in host):
        preference_data["auto_return"] = "approved"

    result = sdk.preference().create(preference_data)
    preference = result["response"]
    order.payment_reference = str(preference.get("id", ""))
    order.save(update_fields=["payment_reference"])
    # init_point = producción (cobro real), sandbox_init_point = pruebas (sin cobro)
    if settings.MERCADOPAGO_SANDBOX:
        return preference.get("sandbox_init_point") or preference.get("init_point")
    return preference.get("init_point") or preference.get("sandbox_init_point")
