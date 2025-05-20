# clinic_billing/admin.py
from django.contrib import admin
from .models import PatientAccount, TreatmentCharge, Transaction, PaymentAllocation

@admin.register(PatientAccount)
class PatientAccountAdmin(admin.ModelAdmin):
    list_display = ('patient', 'current_balance')
    search_fields = ('patient__first_name', 'patient__last_name1', 'patient__id_number')
    readonly_fields = ('current_balance',)

class PaymentAllocationInline(admin.TabularInline):
    model = PaymentAllocation
    extra = 1

@admin.register(TreatmentCharge)
class TreatmentChargeAdmin(admin.ModelAdmin):
    list_display = ('id', 'treatment', 'amount', 'description', 'date_created')
    search_fields = ('treatment__patient__first_name', 'treatment__patient__last_name1', 'description')
    readonly_fields = ('date_created',)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'amount', 'transaction_type', 'payment_method', 'date')
    list_filter = ('transaction_type', 'payment_method', 'date')
    search_fields = ('patient__first_name', 'patient__last_name1', 'description', 'notes')
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'patient',
                ('amount', 'transaction_type'),
                'payment_method',
                'treatment_charge',
                'date',
            )
        }),
        ('Details', {
            'fields': (
                'description',
                'notes',
            )
        }),
    )
    
    inlines = [PaymentAllocationInline]

@admin.register(PaymentAllocation)
class PaymentAllocationAdmin(admin.ModelAdmin):
    list_display = ('id', 'transaction', 'treatment_charge', 'amount')
    list_filter = ('transaction__transaction_type',)
    search_fields = ('transaction__patient__first_name', 'transaction__patient__last_name1')