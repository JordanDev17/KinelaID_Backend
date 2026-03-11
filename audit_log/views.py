import csv
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny
import csv
from django.http import HttpResponse
from django.utils import timezone



from .models import Area, RegistroAcceso, PermisoArea
from .serializers import AreaSerializer, RegistroAccesoSerializer, PermisoAreaSerializer

class AreaViewSet(viewsets.ModelViewSet):
    queryset = Area.objects.all()
    serializer_class = AreaSerializer
    permission_classes = [AllowAny]

class RegistroAccesoViewSet(viewsets.ModelViewSet):
    queryset = RegistroAcceso.objects.select_related('usuario', 'area', 'rol').all()
    serializer_class = RegistroAccesoSerializer
    permission_classes = [AllowAny]
    
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['area', 'permitido', 'estado', 'rol']
    search_fields = ['usuario__nombre_completo', 'usuario__identificacion', 'motivo_denegacion']
    ordering_fields = ['fecha_hora']

    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        total = self.get_queryset().count()
        exitosos = self.get_queryset().filter(permitido=True).count()
        fallidos = total - exitosos
        
        # Evitar errores matemáticos si no hay datos
        tasa_exito = (exitosos / total * 100) if total > 0 else 0
        
        return Response({
            "total_eventos": total,
            "exitosos": exitosos,
            "fallidos": fallidos,
            "tasa_exito": round(tasa_exito, 2),
            "label": "Resumen de Operaciones Biométricas"
        }, status=status.HTTP_200_OK) # ERROR CORREGIDO AQUÍ

    @action(detail=False, methods=['get'])
    def exportar_csv(self, request):
        queryset = self.filter_queryset(self.get_queryset())

        # Hora actual en Colombia
        ahora = timezone.localtime(timezone.now())
        timestamp = ahora.strftime("%Y%m%d_%H%M%S")

        nombre_archivo = f"auditoria_kinelaid_{timestamp}.csv"

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'

        writer = csv.writer(response)
        writer.writerow(['Fecha', 'Usuario', 'Área', 'Resultado', 'Motivo'])

        for log in queryset:
            fecha_local = timezone.localtime(log.fecha_hora)

            writer.writerow([
                fecha_local.strftime("%Y-%m-%d %H:%M:%S"),
                log.usuario.nombre_completo if log.usuario else "DESCONOCIDO",
                log.area.nombre,
                "PERMITIDO" if log.permitido else "DENEGADO",
                log.motivo_denegacion or "N/A"
            ])

        return response
    
class PermisoAreaViewSet(viewsets.ModelViewSet):
    """
    CRUD de permisos por zona.
    
    Uso desde Angular:
      GET  /api/audit/permisosarea/?area=1   → permisos de la zona 1
      POST /api/audit/permisosarea/          → crear permiso (si no existe)
      PATCH /api/audit/permisosarea/3/       → actualizar puede_acceder
    
    El unique_together ('rol', 'area') garantiza que no haya
    entradas duplicadas. Si el frontend intenta crear uno que ya
    existe, Django retorna 400 con el mensaje del constraint.
    Angular lo maneja: si permiso_id > 0 usa PATCH, sino POST.
    """
    queryset             = PermisoArea.objects.select_related('rol', 'area').all()
    serializer_class     = PermisoAreaSerializer
    permission_classes   = [AllowAny]
    filter_backends      = [DjangoFilterBackend]
    filterset_fields     = ['area', 'rol', 'puede_acceder']
    