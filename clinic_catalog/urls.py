# clinic_catalog/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SpecialtyViewSet, CatalogItemViewSet

router = DefaultRouter()
router.register(r'specialties', SpecialtyViewSet)
router.register(r'catalog-items', CatalogItemViewSet)

urlpatterns = [
    path('', include(router.urls)),
]