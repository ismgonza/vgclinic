# platform_contracts/admin.py
from django.contrib import admin
from .models import Subscription, FeatureOverride, UsageQuota, Invoice, InvoiceItem

class FeatureOverrideInline(admin.TabularInline):
    model = FeatureOverride
    extra = 0

class UsageQuotaInline(admin.TabularInline):
    model = UsageQuota
    extra = 0

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('account', 'plan', 'status', 'start_date', 'end_date', 'is_paid')
    list_filter = ('status', 'is_paid', 'auto_renew', 'billing_period')
    search_fields = ('account__name', 'plan__name', 'notes')
    date_hierarchy = 'start_date'
    inlines = [FeatureOverrideInline, UsageQuotaInline]
    fieldsets = (
        (None, {
            'fields': ('account', 'plan', 'status'),
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date', 'trial_end', 'canceled_at'),
        }),
        ('Billing', {
            'fields': ('is_paid', 'next_billing_date', 'billing_period', 'price_override'),
        }),
        ('Additional Information', {
            'fields': ('auto_renew', 'cancellation_reason', 'notes'),
        }),
        ('Payment Provider', {
            'fields': ('payment_provider', 'external_id'),
            'classes': ('collapse',),
        }),
    )

@admin.register(FeatureOverride)
class FeatureOverrideAdmin(admin.ModelAdmin):
    list_display = ('subscription', 'feature_code', 'override_type', 'created_by', 'created_at', 'expires_at')
    list_filter = ('override_type', 'created_at')
    search_fields = ('subscription__account__name', 'feature_code', 'reason')

@admin.register(UsageQuota)
class UsageQuotaAdmin(admin.ModelAdmin):
    list_display = ('subscription', 'quota_type', 'current_usage', 'limit', 'percentage_used', 'is_exceeded')
    list_filter = ('quota_type', 'reset_date')
    search_fields = ('subscription__account__name',)

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'subscription', 'status', 'issue_date', 'due_date', 'total_amount')
    list_filter = ('status', 'issue_date', 'due_date')
    search_fields = ('invoice_number', 'subscription__account__name', 'notes')
    inlines = [InvoiceItemInline]
    date_hierarchy = 'issue_date'
    fieldsets = (
        (None, {
            'fields': ('subscription', 'invoice_number', 'status'),
        }),
        ('Amounts', {
            'fields': ('amount', 'tax_amount', 'total_amount'),
        }),
        ('Dates', {
            'fields': ('issue_date', 'due_date', 'paid_date'),
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'payment_reference', 'notes'),
        }),
    )