# platform_accounts/admin.py
from django.contrib import admin
from .models import Account, AccountOwner, AccountUser

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('account_name', 'account_email', 'account_status', 'is_platform_account', 'account_created_at')
    list_filter = ('account_status', 'is_platform_account')
    search_fields = ('account_name', 'account_email')
    date_hierarchy = 'account_created_at'

@admin.register(AccountOwner)
class AccountOwnerAdmin(admin.ModelAdmin):
    list_display = ('user', 'account', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'account__account_name')
    date_hierarchy = 'created_at'

@admin.register(AccountUser)
class AccountUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'account', 'role', 'specialty', 'is_active_in_account', 'created_at')
    list_filter = ('role', 'is_active_in_account', 'specialty', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'account__account_name')
    date_hierarchy = 'created_at'