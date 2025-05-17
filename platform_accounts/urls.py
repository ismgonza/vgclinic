from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AccountViewSet, AccountUserViewSet, AccountInvitationViewSet

router = DefaultRouter()
router.register(r'accounts', AccountViewSet, basename='account')
router.register(r'members', AccountUserViewSet, basename='account-user')
router.register(r'invitations', AccountInvitationViewSet, basename='account-invitation')

urlpatterns = [
    path('', include(router.urls)),
]