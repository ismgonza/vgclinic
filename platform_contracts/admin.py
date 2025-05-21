# platform_contracts/admin.py
from django.contrib import admin
from .models import Contract

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('contract_number', 'contract_type', 'get_target_name', 'plan', 'status', 'start_date', 'end_date', 'is_trial')
    list_filter = ('contract_type', 'status', 'is_trial', 'auto_renew', 'start_date')
    search_fields = ('contract_number', 'account__account_name', 'user__email', 'plan__name', 'notes')
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Contract Details', {
            'fields': ('contract_number', 'plan', 'contract_type')
        }),
        ('Target', {
            'fields': ('account', 'user'),
            'description': 'Set either account or user based on contract type'
        }),
        ('Status and Dates', {
            'fields': ('status', 'is_trial', 'start_date', 'end_date')
        }),
        ('Billing', {
            'fields': ('price_override', 'billing_period', 'auto_renew')
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_by', 'created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'contract_number')  # Make contract_number read-only
    inlines = []
    
    def get_target_name(self, obj):
        if obj.contract_type == 'account':
            return obj.account.account_name if obj.account else 'Unknown Account'
        else:
            return str(obj.user) if obj.user else 'Unknown User'
    get_target_name.short_description = 'Target'
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating a new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
