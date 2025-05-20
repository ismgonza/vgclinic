# clinic_patients/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PatientViewSet, PatientAccountViewSet, MedicalHistoryViewSet

router = DefaultRouter()
router.register(r'patients', PatientViewSet, basename='patient')
router.register(r'patient-accounts', PatientAccountViewSet, basename='patient-account')
router.register(r'medical-histories', MedicalHistoryViewSet, basename='medical-history')

urlpatterns = [
    path('', include(router.urls)),
]