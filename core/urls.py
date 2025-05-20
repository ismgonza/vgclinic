# core/urls.py (update with platform_services and platform_contracts)
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static
from .api import schema_view
from .dashboard import dashboard_stats, account_list
from platform_users.serializers import CustomTokenObtainPairView


urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Dashboard APIs
    path('api/clinic/dashboard/stats/', dashboard_stats, name='dashboard-stats'),
    path('api/platform/accounts/list/', account_list, name='account-list'),
    
    # Authentication
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
   
    # API Documentation
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # Platform APIs
    path('api/users/', include('platform_users.urls')),
    path('api/accounts/', include('platform_accounts.urls')),
    path('api/services/', include('platform_services.urls')),
    path('api/contracts/', include('platform_contracts.urls')),
    
    # Clinic APIs
    path('api/clinic/patients/', include('clinic_patients.urls')),
    path('api/clinic/catalog/', include('clinic_catalog.urls')),
    path('api/clinic/locations/', include('clinic_locations.urls')),
    path('api/clinic/treatments/', include('clinic_treatments.urls')),
    path('api/clinic/billing/', include('clinic_billing.urls')),
]

# Add static and media serving for development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)