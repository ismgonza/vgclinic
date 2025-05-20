# platform_services/admin.py
from django.contrib import admin
from .models import Feature, Service, Plan

@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'category', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'code', 'description')
    ordering = ('category', 'ui_order', 'name')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'description', 'category')
        }),
        ('Display', {
            'fields': ('icon', 'ui_order', 'is_active')
        }),
    )

class FeatureInline(admin.TabularInline):
    model = Service.features.through
    extra = 1
    verbose_name = "Service Feature"
    verbose_name_plural = "Service Features"

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code', 'description')
    ordering = ('ui_order', 'name')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'description')
        }),
        ('Display', {
            'fields': ('icon', 'ui_order', 'is_active')
        }),
    )
    
    inlines = [FeatureInline]
    exclude = ('features',)

class ServiceInline(admin.TabularInline):
    model = Plan.services.through
    extra = 1
    verbose_name = "Plan Service"
    verbose_name_plural = "Plan Services"

class PlanFeatureInline(admin.TabularInline):
    model = Plan.features.through
    extra = 1
    verbose_name = "Additional Feature"
    verbose_name_plural = "Additional Features"

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'plan_type', 'base_price', 'billing_period', 'is_active')
    list_filter = ('plan_type', 'billing_period', 'is_active')
    search_fields = ('name', 'code', 'description')
    ordering = ('ui_order', 'base_price', 'name')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'description', 'plan_type')
        }),
        ('Pricing', {
            'fields': ('base_price', 'billing_period')
        }),
        ('Quotas and Limits', {
            'fields': ('max_users', 'max_locations')
        }),
        ('Display', {
            'fields': ('ui_order', 'is_active')
        }),
    )
    
    inlines = [ServiceInline, PlanFeatureInline]
    exclude = ('services', 'features')