# clinic_catalog/admin.py
from django.contrib import admin
from .models import Specialty, CatalogItem

@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'account', 'is_active')
    list_filter = ('is_active', 'account')
    search_fields = ('name', 'code', 'description')
    ordering = ('account', 'name')

@admin.register(CatalogItem)
class CatalogItemAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'specialty', 'price', 'is_variable_price', 'is_active')
    list_filter = ('is_active', 'specialty', 'is_variable_price', 'account')
    search_fields = ('code', 'name', 'description')
    ordering = ('account', 'specialty', 'name')
    fieldsets = (
        (None, {
            'fields': ('account', 'specialty')
        }),
        ('Item Details', {
            'fields': ('code', 'name', 'description')
        }),
        ('Pricing', {
            'fields': ('price', 'is_variable_price')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )