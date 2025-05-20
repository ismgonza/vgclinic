# clinic_treatments/admin.py
from django.contrib import admin
from .models import Treatment, TreatmentNote, TreatmentDetail

class TreatmentNoteInline(admin.TabularInline):
    model = TreatmentNote
    extra = 1

class TreatmentDetailInline(admin.TabularInline):
    model = TreatmentDetail
    extra = 3

@admin.register(Treatment)
class TreatmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'catalog_item', 'patient', 'doctor', 'status', 'scheduled_date', 'completed_date')
    list_filter = ('status', 'specialty', 'scheduled_date', 'completed_date')
    search_fields = ('patient__first_name', 'patient__last_name1', 'patient__id_number', 'catalog_item__name', 'notes')
    date_hierarchy = 'scheduled_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                ('catalog_item', 'specialty'),
                'patient',
                'doctor',
                'notes',
            )
        }),
        ('Scheduling', {
            'fields': (
                'scheduled_date',
                'completed_date',
                'status',
            )
        }),
        ('Location', {
            'fields': ('location',)
        }),
        ('Treatment Plan', {
            'fields': (
                'parent_treatment',
                'phase_number',
            ),
            'classes': ('collapse',),
        }),
        ('Metadata', {
            'fields': (
                'created_by',
                ('created_at', 'updated_at'),
            ),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    inlines = [TreatmentNoteInline, TreatmentDetailInline]
    
    def save_model(self, request, obj, form, change):
        # Set created_by if it's a new object
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(TreatmentNote)
class TreatmentNoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'treatment', 'date', 'created_by')
    list_filter = ('date',)
    search_fields = ('treatment__patient__first_name', 'treatment__patient__last_name1', 'note')
    date_hierarchy = 'date'
    
    def save_model(self, request, obj, form, change):
        # Set created_by if it's a new object
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)