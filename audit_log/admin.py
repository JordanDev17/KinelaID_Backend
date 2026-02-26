from django.contrib import admin
from .models import Area, PermisoArea, RegistroAcceso


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ubicacion', 'camara_ip')
    search_fields = ('nombre',)


@admin.register(PermisoArea)
class PermisoAreaAdmin(admin.ModelAdmin):
    list_display = ('rol', 'area', 'puede_acceder', 'fecha_modificacion')
    list_filter = ('rol', 'area')


@admin.register(RegistroAcceso)
class RegistroAccesoAdmin(admin.ModelAdmin):
    list_display = ('fecha_hora', 'usuario', 'area', 'estado', 'motivo_denegacion')
    list_filter = ('estado', 'area')
