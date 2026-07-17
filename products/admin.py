# products/admin.py
from django.contrib import admin

from .models import FunnelStep, Product, Sale


class FunnelStepInline(admin.TabularInline):
    model = FunnelStep
    extra = 1


class SaleInline(admin.TabularInline):
    model = Sale
    extra = 1
    fields = ("contact", "amount", "date", "funnel_step")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "product_type", "status", "price", "project", "sale_count", "total_revenue")
    list_filter = ("status", "product_type", "project")
    search_fields = ("name", "description")
    inlines = [FunnelStepInline, SaleInline]


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("product", "contact", "amount", "date", "funnel_step")
    list_filter = ("product", "date")
    search_fields = ("product__name", "contact__name", "notes")
    date_hierarchy = "date"


@admin.register(FunnelStep)
class FunnelStepAdmin(admin.ModelAdmin):
    list_display = ("product", "name", "position", "is_oto", "effective_price")
    list_filter = ("is_oto", "product")
