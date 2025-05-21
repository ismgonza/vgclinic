# platform_contracts/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ContractViewSet, FeatureOverrideViewSet, UsageQuotaViewSet
)

router = DefaultRouter()
router.register(r'', ContractViewSet)
router.register(r'overrides', FeatureOverrideViewSet)
router.register(r'quotas', UsageQuotaViewSet)

urlpatterns = [
    path('', include(router.urls)),
]