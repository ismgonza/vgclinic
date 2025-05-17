from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('platform_users.urls')),
    path('api/accounts/', include('platform_accounts.urls')),
    path('api/services/', include('platform_services.urls')),
    path('api/contracts/', include('platform_contracts.urls')),
    path('api/clinic/locations/', include('clinic_locations.urls')),
    path('api/clinic/catalog/', include('clinic_catalog.urls')),
    path('api/clinic/staff/', include('clinic_staff.urls')),
]