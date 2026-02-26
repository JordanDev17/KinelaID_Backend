from django.contrib import admin
from .models import Camara


@admin.register(Camara)
class CamaraAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ip', 'area', 'activa', 'fecha_registro')
    list_filter = ('area', 'activa')
    search_fields = ('nombre', 'ip')
