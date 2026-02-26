from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UsuarioViewSet, RolViewSet

# Creamos el router y registramos nuestras vistas
router = DefaultRouter()
router.register(r'empleados', UsuarioViewSet)
router.register(r'roles', RolViewSet)

urlpatterns = [
    path('', include(router.urls)),
]