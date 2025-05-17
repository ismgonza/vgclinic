# platform_accounts/admin.py
from django.contrib import admin
from .models import Account, AccountUser, AccountInvitation

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'status', 'owner', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'slug', 'email')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(AccountUser)
class AccountUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'account', 'role', 'is_active', 'joined_at')
    list_filter = ('role', 'is_active', 'joined_at')
    search_fields = ('user__email', 'account__name')

@admin.register(AccountInvitation)
class AccountInvitationAdmin(admin.ModelAdmin):
    list_display = ('email', 'account', 'role', 'status', 'created_at', 'expires_at')
    list_filter = ('status', 'role', 'created_at')
    search_fields = ('email', 'account__name')
    readonly_fields = ('invitation_code',)