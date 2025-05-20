# platform_accounts/admin.py
from django.contrib import admin
from .models import Account, Role, AccountUser

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('account_name', 'account_email', 'account_status', 'is_platform_account', 'account_created_at')
    list_filter = ('account_status', 'is_platform_account')
    search_fields = ('account_name', 'account_email')
    date_hierarchy = 'account_created_at'

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'role_name')

@admin.register(AccountUser)
class AccountUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'account', 'role', 'is_active_in_account')
    list_filter = ('role', 'is_active_in_account')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'account__account_name')