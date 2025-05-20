# clinic_locations/admin.py
from django.contrib import admin
from .models import Branch, Room

class RoomInline(admin.TabularInline):
    model = Room
    extra = 1

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'account', 'province', 'phone', 'email', 'is_active')
    list_filter = ('is_active', 'province', 'account')
    search_fields = ('name', 'email', 'phone', 'address')
    ordering = ('account', 'name')
    
    fieldsets = (
        (None, {
            'fields': ('account', 'name', 'is_active')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone')
        }),
        ('Location', {
            'fields': (
                ('province', 'canton', 'district'),
                'address'
            )
        }),
    )
    
    inlines = [RoomInline]

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'branch', 'is_active', 'is_private')
    list_filter = ('is_active', 'is_private', 'branch')
    search_fields = ('name',)
    ordering = ('branch', 'name')