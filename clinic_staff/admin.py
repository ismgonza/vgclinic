# clinic_staff/admin.py
from django.contrib import admin
from .models import StaffSpecialty, StaffMember, StaffLocation, AvailabilitySchedule

class StaffLocationInline(admin.TabularInline):
    model = StaffLocation
    extra = 1
    fields = ('location', 'is_primary')

class AvailabilityScheduleInline(admin.TabularInline):
    model = AvailabilitySchedule
    extra = 1
    fields = ('location', 'day_of_week', 'start_time', 'end_time', 'is_available')

@admin.register(StaffMember)
class StaffMemberAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'get_account_name', 'job_title', 'staff_role', 'is_active')
    list_filter = ('is_active', 'staff_role', 'can_book_appointments', 'account_user__account')
    search_fields = (
        'account_user__user__first_name', 
        'account_user__user__last_name', 
        'account_user__user__email',
        'job_title'
    )
    inlines = [StaffLocationInline, AvailabilityScheduleInline]
    filter_horizontal = ('specialties',)
    
    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'Name'
    
    def get_account_name(self, obj):
        return obj.account_user.account.name
    get_account_name.short_description = 'Account'
    
    fieldsets = (
        (None, {
            'fields': ('account_user', 'job_title', 'staff_role', 'specialties')
        }),
        ('Professional Information', {
            'fields': ('license_number',)
        }),
        ('Contact and Status', {
            'fields': ('phone', 'is_active', 'can_book_appointments')
        }),
        ('Appearance', {
            'fields': ('appointment_color',)
        }),
    )

@admin.register(StaffSpecialty)
class StaffSpecialtyAdmin(admin.ModelAdmin):
    list_display = ('name', 'account', 'is_active')
    list_filter = ('is_active', 'account')
    search_fields = ('name', 'description')

@admin.register(StaffLocation)
class StaffLocationAdmin(admin.ModelAdmin):
    list_display = ('staff', 'location', 'is_primary')
    list_filter = ('is_primary', 'location', 'staff')
    search_fields = ('staff__account_user__user__first_name', 'staff__account_user__user__last_name', 'location__name')

@admin.register(AvailabilitySchedule)
class AvailabilityScheduleAdmin(admin.ModelAdmin):
    list_display = ('staff', 'location', 'get_day_display', 'start_time', 'end_time', 'is_available')
    list_filter = ('day_of_week', 'is_available', 'location', 'staff')
    search_fields = ('staff__account_user__user__first_name', 'staff__account_user__user__last_name', 'location__name')
    
    def get_day_display(self, obj):
        return obj.get_day_of_week_display()
    get_day_display.short_description = 'Day'