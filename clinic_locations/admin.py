# clinic_locations/admin.py
from django.contrib import admin
from .models import Location, Room

class RoomInline(admin.TabularInline):
    model = Room
    extra = 1

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'account', 'province', 'canton', 'phone', 'is_active')
    list_filter = ('province', 'canton', 'is_active', 'account')
    search_fields = ('name', 'email', 'phone', 'address')
    inlines = [RoomInline]
    fieldsets = (
        (None, {
            'fields': ('account', 'name', 'is_active'),
        }),
        ('Contact Information', {
            'fields': ('email', 'phone'),
        }),
        ('Address', {
            'fields': ('province', 'canton', 'district', 'address'),
        }),
    )

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'is_active', 'is_private')
    list_filter = ('is_active', 'is_private', 'location__account')
    search_fields = ('name', 'location__name')