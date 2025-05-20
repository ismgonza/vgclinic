# platform_accounts/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AccountViewSet, RoleViewSet, AccountUserViewSet

router = DefaultRouter()
router.register(r'accounts', AccountViewSet)
router.register(r'roles', RoleViewSet)
router.register(r'account-users', AccountUserViewSet)

urlpatterns = [
    path('', include(router.urls)),
]