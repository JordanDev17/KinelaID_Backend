from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UsuarioViewSet, RolViewSet


# =====================================================
# ROUTER DRF
# =====================================================
router = DefaultRouter()

# CRUD de empleados
router.register(r'empleados', UsuarioViewSet)

# CRUD de roles
router.register(r'roles', RolViewSet)


# =====================================================
# URLS
# =====================================================
urlpatterns = [
    path('', include(router.urls)),
]