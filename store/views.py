"""Vistas de la tienda MUTE."""
import json

from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .cart import Cart
from .forms import CheckoutForm
from .models import Order, OrderStatus, PaymentMethod, Product, ProductVariant
from .pricing import build_totals, money
from . import payments
from . import services


# --------------------------------------------------------------------------
# Catálogo
# --------------------------------------------------------------------------
def home(request):
    products = Product.objects.filter(is_active=True).prefetch_related(
        "images", "colors"
    )
    featured = products.filter(is_featured=True).first() or products.first()
    context = {
        "products": products,
        "featured": featured,
    }
    return render(request, "store/home.html", context)


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.prefetch_related(
            "colors__variants", "colors__gallery", "images", "features", "variants"
        ),
        slug=slug,
        is_active=True,
    )

    # Mapa color -> talla -> {variant_id, stock} para el selector
    variant_map = {}
    for variant in product.variants.all():
        variant_map.setdefault(str(variant.color_id), {})[variant.size] = {
            "id": variant.id,
            "stock": variant.stock,
        }

    # Mapa color -> [urls de fotos] para la galería (principal + extras)
    images_by_color = {}
    for c in product.colors.all():
        urls = [c.image.url] if c.image else []
        urls += [g.image.url for g in c.gallery.all()]
        images_by_color[str(c.id)] = urls

    related = (
        Product.objects.filter(is_active=True, category=product.category)
        .exclude(id=product.id)[:4]
    )

    context = {
        "product": product,
        "variant_map_json": json.dumps(variant_map),
        "images_by_color_json": json.dumps(images_by_color),
        "sizes": ["XS", "S", "M", "L", "XL", "XXL"],
        "breakdown": product.price_breakdown,
        "related": related,
    }
    return render(request, "store/product_detail.html", context)


# --------------------------------------------------------------------------
# Carrito
# --------------------------------------------------------------------------
@require_POST
def cart_add(request):
    cart = Cart(request)
    variant_id = request.POST.get("variant_id")
    quantity = int(request.POST.get("quantity", 1))
    variant = get_object_or_404(ProductVariant, id=variant_id)

    if variant.stock <= 0:
        return JsonResponse(
            {"ok": False, "error": "Sin inventario disponible."}, status=400
        )

    cart.add(variant, quantity=quantity)
    return JsonResponse({
        "ok": True,
        "cart_count": len(cart),
        "message": f"{variant.product.name} agregado al carrito.",
    })


@require_POST
def cart_update(request):
    cart = Cart(request)
    variant_id = request.POST.get("variant_id")
    quantity = int(request.POST.get("quantity", 1))
    cart.update(variant_id, quantity)
    return _cart_state(cart)


@require_POST
def cart_remove(request):
    cart = Cart(request)
    variant_id = request.POST.get("variant_id")
    cart.remove(variant_id)
    return _cart_state(cart)


def _cart_state(cart):
    """Devuelve el estado completo del carrito en JSON (para el carrito lateral)."""
    items = []
    for item in cart:
        items.append({
            "variant_id": item["variant"].id,
            "name": gettext(item["product"].name),
            "color": gettext(item["color"].name),
            "color_hex": item["color"].hex_code,
            "size": item["size"],
            "url": item["product"].get_absolute_url(),
            "image": item["image"].url if item["image"] else None,
            "unit_price": float(item["unit_price"]),
            "line_total": float(item["line_total"]),
            "quantity": item["quantity"],
        })
    return JsonResponse({
        "ok": True,
        "items": items,
        "cart_count": len(cart),
        "subtotal": float(cart.subtotal),
        "iva": float(cart.iva),
    })


def cart_json(request):
    """Estado del carrito por GET (para hidratar el carrito lateral)."""
    return _cart_state(Cart(request))


def cart_detail(request):
    cart = Cart(request)
    return render(request, "store/cart.html", {"cart": cart})


# --------------------------------------------------------------------------
# Cálculo de envío en vivo (AJAX)
# --------------------------------------------------------------------------
def calculate_shipping(request):
    """Recalcula totales según el país (envío gratis MX, $300 internacional)."""
    cart = Cart(request)
    country = request.GET.get("country", "MX")
    totals = build_totals(cart.subtotal, country)
    return JsonResponse({
        "subtotal": float(totals["subtotal"]),
        "iva": float(totals["iva"]),
        "base": float(totals["base"]),
        "shipping": float(totals["shipping"]),
        "total": float(totals["total"]),
        "free_shipping": totals["free_shipping"],
        "iva_rate": totals["iva_rate"],
    })


# --------------------------------------------------------------------------
# Checkout
# --------------------------------------------------------------------------
def checkout(request):
    cart = Cart(request)
    if cart.is_empty:
        messages.info(request, "Tu carrito está vacío.")
        return redirect("store:home")

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = services.create_order_from_cart(cart, form.cleaned_data)
            method = form.cleaned_data["payment_method"]
            try:
                if method == PaymentMethod.STRIPE and payments.stripe_enabled():
                    return redirect(payments.create_stripe_session(order, request))
                if (method == PaymentMethod.MERCADOPAGO
                        and payments.mercadopago_enabled()):
                    return redirect(
                        payments.create_mercadopago_preference(order, request)
                    )
            except Exception as exc:  # noqa: BLE001
                messages.error(
                    request,
                    "Hubo un problema al iniciar el pago. Intenta de nuevo. "
                    f"({exc})",
                )
                return redirect("store:checkout")

            # Modo simulado (sin llaves configuradas)
            return redirect(
                f"/pago/exito/{order.order_number}/?provider=simulated"
            )
    else:
        form = CheckoutForm()

    totals = build_totals(cart.subtotal, "MX")
    context = {
        "cart": cart,
        "form": form,
        "totals": totals,
        "stripe_enabled": payments.stripe_enabled(),
        "mercadopago_enabled": payments.mercadopago_enabled(),
    }
    return render(request, "store/checkout.html", context)


def payment_success(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    provider = request.GET.get("provider", "")

    if not order.is_paid:
        if provider == "stripe" and payments.stripe_enabled():
            _verify_stripe(request, order)
        elif provider == "mercadopago" and payments.mercadopago_enabled():
            _verify_mercadopago(request, order)
        elif provider == "simulated":
            services.mark_order_paid(order, PaymentMethod.SIMULATED)

    Cart(request).clear()
    return render(request, "store/order_confirmation.html", {
        "order": order,
        "simulated": provider == "simulated",
    })


def _verify_stripe(request, order):
    import stripe

    stripe.api_key = settings.STRIPE_SECRET_KEY
    session_id = request.GET.get("session_id")
    if not session_id:
        return
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status == "paid":
            services.mark_order_paid(
                order, PaymentMethod.STRIPE, reference=session.payment_intent
            )
    except Exception:
        pass


def _verify_mercadopago(request, order):
    """Confirma con la API de MercadoPago que el pago fue aprobado (no confía
    en los parámetros de la URL, que se pueden falsificar)."""
    import mercadopago

    payment_id = request.GET.get("payment_id") or request.GET.get("collection_id")
    if not payment_id:
        return
    try:
        sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
        payment = sdk.payment().get(payment_id)["response"]
        if payment.get("status") == "approved":
            services.mark_order_paid(
                order, PaymentMethod.MERCADOPAGO, reference=str(payment_id)
            )
    except Exception:
        pass


def payment_cancel(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    return render(request, "store/payment_cancel.html", {"order": order})


# --------------------------------------------------------------------------
# Webhooks (confirmación robusta del pago)
# --------------------------------------------------------------------------
@csrf_exempt
def stripe_webhook(request):
    import stripe

    payload = request.body
    sig = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        if secret:
            event = stripe.Webhook.construct_event(payload, sig, secret)
        else:
            event = json.loads(payload)
    except Exception:
        return HttpResponse(status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        order_number = session.get("metadata", {}).get("order_number")
        if order_number:
            order = Order.objects.filter(order_number=order_number).first()
            if order:
                services.mark_order_paid(
                    order, PaymentMethod.STRIPE,
                    reference=session.get("payment_intent", ""),
                )
    return HttpResponse(status=200)


@csrf_exempt
def mercadopago_webhook(request):
    """Notificación de MercadoPago. Confirma el pago consultando la API."""
    import mercadopago

    topic = request.GET.get("type") or request.GET.get("topic")
    data_id = request.GET.get("data.id") or request.GET.get("id")
    if topic == "payment" and data_id:
        sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
        try:
            payment = sdk.payment().get(data_id)["response"]
            if payment.get("status") == "approved":
                ref = payment.get("external_reference")
                order = Order.objects.filter(order_number=ref).first()
                if order:
                    services.mark_order_paid(
                        order, PaymentMethod.MERCADOPAGO, reference=str(data_id)
                    )
        except Exception:
            pass
    return HttpResponse(status=200)
