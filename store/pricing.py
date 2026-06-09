"""Cálculos de dinero, IVA y envío (centralizados)."""
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings


def money(value):
    """Redondea a 2 decimales como Decimal."""
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def split_iva(amount_with_iva):
    """
    Dado un importe que YA incluye IVA, devuelve la base gravable y el IVA.
    Ej. $2500 con IVA 16% -> base $2155.17, iva $344.83
    """
    rate = Decimal(str(settings.IVA_RATE))
    total = money(amount_with_iva)
    base = money(total / (Decimal("1") + rate))
    iva = money(total - base)
    return {"base": base, "iva": iva, "total": total}


def calculate_shipping(country_code, subtotal=None):
    """
    Envío gratis en el país base (México); costo fijo para el resto.
    """
    if (country_code or "").upper() == settings.FREE_SHIPPING_COUNTRY.upper():
        return money(0)
    return money(settings.INTERNATIONAL_SHIPPING_COST)


def build_totals(subtotal, country_code):
    """
    Construye el desglose completo para el checkout.
    subtotal = suma de líneas (precios ya incluyen IVA).
    """
    subtotal = money(subtotal)
    iva_parts = split_iva(subtotal)
    shipping = calculate_shipping(country_code, subtotal)
    total = money(subtotal + shipping)
    return {
        "subtotal": subtotal,        # productos con IVA incluido
        "base": iva_parts["base"],   # base gravable (sin IVA)
        "iva": iva_parts["iva"],     # IVA contenido (16%)
        "shipping": shipping,        # costo de envío
        "total": total,              # total a pagar
        "iva_rate": int(round(settings.IVA_RATE * 100)),
        "free_shipping": shipping == 0,
    }
