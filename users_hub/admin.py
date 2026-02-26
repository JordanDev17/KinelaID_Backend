from django.contrib import admin
from .models import Usuario, Rol
from interface_auth.models import InterfazUsuario # Importamos el modelo aquí

# Definimos el Inline aquí mismo
class InterfazUsuarioInline(admin.StackedInline):
    model = InterfazUsuario
    can_delete = False
    verbose_name_plural = 'Configuración de Acceso a Panel (Staff)'
    fk_name = 'perfil'
    extra = 0 # No mostrar formularios vacíos de más

@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'rol', 'activo', 'fecha_creacion')
    list_filter = ('rol', 'activo')
    search_fields = ('nombre_completo', 'identificacion')
    # Aquí inyectamos el formulario del login dentro del usuario
    inlines = [InterfazUsuarioInline]