# platform_contracts/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SubscriptionViewSet, FeatureOverrideViewSet, UsageQuotaViewSet,
    InvoiceViewSet, InvoiceItemViewSet
)

router = DefaultRouter()
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
router.register(r'feature-overrides', FeatureOverrideViewSet, basename='featureoverride')
router.register(r'usage-quotas', UsageQuotaViewSet, basename='usagequota')
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'invoice-items', InvoiceItemViewSet, basename='invoiceitem')

urlpatterns = [
    path('', include(router.urls)),
]