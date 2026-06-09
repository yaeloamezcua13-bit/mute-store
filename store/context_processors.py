"""Variables disponibles en todas las plantillas."""
import re

from django.conf import settings

from .cart import Cart


def cart(request):
    cart_obj = Cart(request)
    return {
        "cart": cart_obj,
        "cart_count": len(cart_obj),
        "cart_subtotal": cart_obj.subtotal,
    }


def store_settings(request):
    digits = re.sub(r"\D", "", settings.STORE_PHONE)  # solo números
    wa = digits if digits.startswith("52") else f"52{digits}"  # WhatsApp intl
    national = digits[2:] if digits.startswith("52") else digits
    phone_display = f"+52 {national}"  # como se muestra: +52 9988416700
    return {
        "store_name": settings.STORE_NAME,
        "store_phone": phone_display,
        "store_phone_wa": wa,
        "store_phone_tel": f"+{wa}",
        "store_instagram": settings.STORE_INSTAGRAM,
        "store_email": settings.STORE_EMAIL,
        "free_shipping_country": settings.FREE_SHIPPING_COUNTRY,
        "international_shipping_cost": settings.INTERNATIONAL_SHIPPING_COST,
        "iva_rate_pct": int(round(settings.IVA_RATE * 100)),
    }
