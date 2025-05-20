# clinic_patients/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PatientViewSet, MedicalHistoryViewSet

router = DefaultRouter()
router.register(r'patients', PatientViewSet)
router.register(r'medical-histories', MedicalHistoryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]