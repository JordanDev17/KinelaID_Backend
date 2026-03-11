from django.contrib import admin
from .models import Camara

@admin.register(Camara)
class CamaraAdmin(admin.ModelAdmin):
    # Columnas que verás en la lista
    list_display = ('nombre', 'hardware_index', 'area', 'is_activa', 'stream_url')
    # Filtros laterales
    list_filter = ('is_activa', 'area')
    # Buscador
    search_fields = ('nombre', 'descripcion')