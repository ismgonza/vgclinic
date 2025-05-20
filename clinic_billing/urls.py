# clinic_billing/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PatientAccountViewSet, TreatmentChargeViewSet, 
    TransactionViewSet, PaymentAllocationViewSet
)

router = DefaultRouter()
router.register(r'accounts', PatientAccountViewSet)
router.register(r'charges', TreatmentChargeViewSet)
router.register(r'transactions', TransactionViewSet)
router.register(r'allocations', PaymentAllocationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]