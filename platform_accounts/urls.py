# platform_accounts/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AccountViewSet, AccountUserViewSet, AccountOwnerViewSet

router = DefaultRouter()
router.register(r'', AccountViewSet, basename='account')
router.register(r'owners', AccountOwnerViewSet)
router.register(r'account-users', AccountUserViewSet)

urlpatterns = [
    path('', include(router.urls)),
]