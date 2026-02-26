from django.contrib import admin
from django.urls import path, include 
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('users_hub.urls')),
    path('api/access/', include('access_control.urls')),
    path('api/audit/', include('audit_log.urls')),
    path('api/auth-interfaz/', include('interface_auth.urls')),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)