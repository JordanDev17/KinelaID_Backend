import csv
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny

from .models import Area, RegistroAcceso
from .serializers import AreaSerializer, RegistroAccesoSerializer

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
        """Endpoint pulido para el Dashboard del Frontend"""
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
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="auditoria_kinelaid.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Fecha', 'Usuario', 'Área', 'Resultado', 'Motivo'])

        for log in queryset:
            writer.writerow([
                log.fecha_hora.strftime("%Y-%m-%d %H:%M"),
                log.usuario.nombre_completo if log.usuario else "DESCONOCIDO",
                log.area.nombre,
                "PERMITIDO" if log.permitido else "DENEGADO",
                log.motivo_denegacion or "N/A"
            ])
        return response