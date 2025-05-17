# clinic_catalog/admin.py
from django.contrib import admin
from .models import Category, CatalogItem, Package, PackageItem

class SubcategoryInline(admin.TabularInline):
    model = Category
    fk_name = 'parent'
    extra = 1
    fields = ('name', 'description', 'is_active', 'display_order')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'account', 'parent', 'is_active', 'display_order')
    list_filter = ('is_active', 'account')
    search_fields = ('name', 'description')
    inlines = [SubcategoryInline]
    fieldsets = (
        (None, {
            'fields': ('account', 'name', 'description', 'parent', 'is_active', 'display_order'),
        }),
    )


class PackageItemInline(admin.TabularInline):
    model = PackageItem
    extra = 1
    fields = ('item', 'quantity')
    raw_id_fields = ('item',)


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ('catalog_item', 'discount_type', 'discount_value')
    search_fields = ('catalog_item__name', 'catalog_item__code')
    inlines = [PackageItemInline]
    fields = ('catalog_item', 'discount_type', 'discount_value')
    raw_id_fields = ('catalog_item',)


@admin.register(CatalogItem)
class CatalogItemAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'account', 'category', 'item_type', 'price', 'is_active')
    list_filter = ('is_active', 'item_type', 'account', 'category')
    search_fields = ('code', 'name', 'description')
    fieldsets = (
        (None, {
            'fields': ('account', 'code', 'name', 'description', 'category', 'item_type'),
        }),
        ('Pricing', {
            'fields': ('price', 'variable_price', 'tax_rate'),
        }),
        ('Status', {
            'fields': ('is_active',),
        }),
    )