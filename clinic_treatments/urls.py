# clinic_treatments/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TreatmentViewSet, TreatmentNoteViewSet, TreatmentDetailViewSet

router = DefaultRouter()
router.register(r'treatments', TreatmentViewSet)
router.register(r'treatment-notes', TreatmentNoteViewSet)
router.register(r'treatment-details', TreatmentDetailViewSet)

urlpatterns = [
    path('', include(router.urls)),
]