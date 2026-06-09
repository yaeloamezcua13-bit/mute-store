"""Formularios de la tienda."""
from django import forms
from django.utils.translation import gettext_lazy as _

from .models import PaymentMethod
from .shipping import COUNTRIES


class CheckoutForm(forms.Form):
    full_name = forms.CharField(
        label="Nombre completo", max_length=120,
        widget=forms.TextInput(attrs={"placeholder": _("Tu nombre")}),
    )
    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={"placeholder": _("tucorreo@ejemplo.com")}),
    )
    phone = forms.CharField(
        label="Teléfono", max_length=30, required=False,
        widget=forms.TextInput(attrs={"placeholder": _("10 dígitos")}),
    )
    address_line = forms.CharField(
        label="Dirección (calle y número)", max_length=200,
        widget=forms.TextInput(attrs={"placeholder": _("Calle, número, colonia")}),
    )
    city = forms.CharField(
        label="Ciudad", max_length=80,
        widget=forms.TextInput(attrs={"placeholder": _("Ciudad")}),
    )
    state = forms.CharField(
        label="Estado / Provincia", max_length=80, required=False,
        widget=forms.TextInput(attrs={"placeholder": _("Estado")}),
    )
    postal_code = forms.CharField(
        label="Código postal", max_length=20,
        widget=forms.TextInput(attrs={
            "placeholder": _("Ej. 77500"),
            "data-shipping-trigger": "postal",
        }),
    )
    country = forms.ChoiceField(
        label="País", choices=COUNTRIES, initial="MX",
        widget=forms.Select(attrs={"data-shipping-trigger": "country"}),
    )
    payment_method = forms.ChoiceField(
        label="Método de pago",
        choices=[
            (PaymentMethod.STRIPE, "Tarjeta (Stripe)"),
            (PaymentMethod.MERCADOPAGO, "MercadoPago"),
        ],
        widget=forms.RadioSelect,
        initial=PaymentMethod.STRIPE,
    )

    def clean_postal_code(self):
        cp = self.cleaned_data["postal_code"].strip()
        country = self.data.get("country", "MX")
        if country == "MX" and not (cp.isdigit() and len(cp) == 5):
            raise forms.ValidationError(
                _("El código postal de México debe tener 5 dígitos.")
            )
        return cp
