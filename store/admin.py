"""Panel de administración de la tienda MUTE."""
from django.contrib import admin
from django.db.models import Sum
from django.utils.html import format_html

from .models import (
    Order,
    OrderItem,
    Product,
    ProductColor,
    ProductFeature,
    ProductImage,
    ProductVariant,
)


class ProductColorInline(admin.TabularInline):
    model = ProductColor
    extra = 1


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductFeatureInline(admin.TabularInline):
    model = ProductFeature
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name", "category", "price", "total_stock_display",
        "is_active", "is_featured", "sort_order",
    )
    list_editable = ("is_active", "is_featured", "sort_order")
    list_filter = ("category", "is_active", "is_featured")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [
        ProductColorInline,
        ProductVariantInline,
        ProductImageInline,
        ProductFeatureInline,
    ]

    @admin.display(description="Inventario total")
    def total_stock_display(self, obj):
        return obj.total_stock


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = (
        "product_name", "color", "size", "unit_price", "quantity", "line_total",
    )
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number", "full_name", "status_badge", "total",
        "country_name", "payment_method", "created_at",
    )
    list_filter = ("status", "payment_method", "country", "created_at")
    search_fields = ("order_number", "full_name", "email", "phone")
    readonly_fields = (
        "order_number", "subtotal", "iva_amount", "shipping_cost", "total",
        "base_amount", "payment_reference", "paid_at", "created_at", "updated_at",
    )
    inlines = [OrderItemInline]
    list_per_page = 50
    date_hierarchy = "created_at"
    fieldsets = (
        ("Pedido", {"fields": ("order_number", "status", "created_at", "updated_at")}),
        ("Cliente", {"fields": ("full_name", "email", "phone")}),
        ("Envío", {"fields": (
            "address_line", "city", "state", "postal_code",
            "country", "country_name",
        )}),
        ("Importes", {"fields": (
            "subtotal", "iva_amount", "base_amount", "shipping_cost", "total",
        )}),
        ("Pago", {"fields": ("payment_method", "payment_reference", "paid_at")}),
        ("Notas", {"fields": ("notes",)}),
    )

    @admin.display(description="Estado")
    def status_badge(self, obj):
        colors = {
            "pending": "#b8860b", "paid": "#1a7f37", "processing": "#0969da",
            "shipped": "#8250df", "delivered": "#1a7f37", "cancelled": "#cf222e",
        }
        color = colors.get(obj.status, "#57606a")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:10px;font-size:11px;">{}</span>',
            color, obj.get_status_display(),
        )

    def changelist_view(self, request, extra_context=None):
        """Muestra el total vendido en la parte superior de la lista."""
        extra_context = extra_context or {}
        qs = self.get_queryset(request).filter(
            status__in=["paid", "processing", "shipped", "delivered"]
        )
        extra_context["ventas_total"] = qs.aggregate(t=Sum("total"))["t"] or 0
        extra_context["ventas_count"] = qs.count()
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(ProductColor)
class ProductColorAdmin(admin.ModelAdmin):
    list_display = ("product", "name", "hex_code", "sort_order")
    list_filter = ("product",)


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("product", "color", "size", "stock", "sku")
    list_editable = ("stock",)
    list_filter = ("product", "size")
    search_fields = ("sku",)
