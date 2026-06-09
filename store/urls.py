from django.urls import path

from . import views

app_name = "store"

urlpatterns = [
    path("", views.home, name="home"),
    path("producto/<slug:slug>/", views.product_detail, name="product_detail"),

    # Carrito
    path("carrito/", views.cart_detail, name="cart_detail"),
    path("carrito/json/", views.cart_json, name="cart_json"),
    path("carrito/agregar/", views.cart_add, name="cart_add"),
    path("carrito/actualizar/", views.cart_update, name="cart_update"),
    path("carrito/eliminar/", views.cart_remove, name="cart_remove"),

    # Envío (AJAX)
    path("envio/calcular/", views.calculate_shipping, name="calculate_shipping"),

    # Checkout y pago
    path("checkout/", views.checkout, name="checkout"),
    path("pago/exito/<str:order_number>/", views.payment_success, name="payment_success"),
    path("pago/cancelado/<str:order_number>/", views.payment_cancel, name="payment_cancel"),

    # Webhooks
    path("webhooks/stripe/", views.stripe_webhook, name="stripe_webhook"),
    path("webhooks/mercadopago/", views.mercadopago_webhook, name="mercadopago_webhook"),
]
