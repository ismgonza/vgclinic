# platform_accounts/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AccountViewSet, 
    AccountUserViewSet, 
    AccountOwnerViewSet,
    AccountInvitationViewSet,
    InvitationAcceptanceView
)

router = DefaultRouter()
router.register(r'', AccountViewSet, basename='account')  # Keep your original setup
router.register(r'owners', AccountOwnerViewSet)
router.register(r'account-users', AccountUserViewSet)
router.register(r'invitations', AccountInvitationViewSet)

# Separate pattern for invitation acceptance (no auth required)
invitation_acceptance = InvitationAcceptanceView.as_view({
    'get': 'validate_token',
    'post': 'accept'
})

urlpatterns = [
    # PUBLIC URLs FIRST (no authentication required)
    path('accept-invitation/<str:token>/', invitation_acceptance, name='accept-invitation-token'),
    path('accept-invitation/', invitation_acceptance, name='accept-invitation'),
    
    # AUTHENTICATED URLs SECOND 
    path('', include(router.urls)),
]