# clinic_catalog/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, CatalogItemViewSet, PackageViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'items', CatalogItemViewSet, basename='catalogitem')
router.register(r'packages', PackageViewSet, basename='package')

urlpatterns = [
    path('', include(router.urls)),
]