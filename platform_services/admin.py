# platform_services/admin.py
from django.contrib import admin
from .models import Feature, Service, Plan

@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'category', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'code', 'description')
    prepopulated_fields = {'code': ('name',)}
    ordering = ('category', 'ui_order', 'name')


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code', 'description')
    prepopulated_fields = {'code': ('name',)}
    filter_horizontal = ('features',)


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'base_price', 'billing_period', 'is_free', 'is_active', 'is_public')
    list_filter = ('is_active', 'is_public', 'is_free', 'is_featured', 'billing_period')
    search_fields = ('name', 'code', 'description')
    prepopulated_fields = {'code': ('name',)}
    filter_horizontal = ('services', 'features')
    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'description', 'is_active'),
        }),
        ('Features and Services', {
            'fields': ('services', 'features'),
        }),
        ('Pricing', {
            'fields': ('is_free', 'base_price', 'billing_period'),
        }),
        ('Limits', {
            'fields': ('max_users', 'max_locations', 'max_storage_gb'),
        }),
        ('Display Options', {
            'fields': ('is_public', 'is_featured', 'ui_order'),
        }),
    )