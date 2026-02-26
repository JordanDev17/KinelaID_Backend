import face_recognition
import numpy as np
import base64

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.files.base import ContentFile

from audit_log.models import Area, RegistroAcceso, PermisoArea
from users_hub.models import Usuario
from .serializers import AccesoLiveSerializer


class ProcesarLiveView(APIView):
    """
    Vista optimizada para el procesamiento biométrico en tiempo real.
    Valida identidad, permisos de área y registra auditoría completa.
    """

    def post(self, request):
        # ==========================================
        # 1. VALIDACIÓN MEDIANTE SERIALIZER
        # ==========================================
        serializer = AccesoLiveSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        foto_b64 = serializer.validated_data['foto']
        area_id = serializer.validated_data['area_id']

        try:
            # ==========================================
            # 2. PROCESAMIENTO DE IMAGEN IA
            # ==========================================
            # Decodificación de la imagen enviada por el Monitor
            format, imgstr = foto_b64.split(';base64,')
            data = ContentFile(base64.b64decode(imgstr), name="verify.jpg")
            image = face_recognition.load_image_file(data)
            
            # Localización y extracción de huella facial (Embedding)
            face_locations = face_recognition.face_locations(image)
            embeddings = face_recognition.face_encodings(image, face_locations)

            # Recuperamos el objeto área (ya validado por el serializer)
            area = Area.objects.get(area_id=area_id)

            # ==========================================
            # 3. CASO: NO SE DETECTA ROSTRO
            # ==========================================
            if not embeddings:
                RegistroAcceso.objects.create(
                    area=area,
                    permitido=False,
                    estado="DENEGADO_RECONOCIMIENTO",
                    motivo_denegacion="No se detectó rostro en la captura"
                )
                return Response({
                    "status": "DENIED", 
                    "mensaje": "Rostro no visible o fuera de encuadre"
                }, status=status.HTTP_403_FORBIDDEN)

            vec_query = embeddings[0]
            
            # Optimizamos la consulta trayendo el rol de una vez
            usuarios = Usuario.objects.exclude(face_embedding__isnull=True).select_related('rol')
            
            mejor_match = None
            min_dist = 0.5  # Umbral de tolerancia biométrica

            # Búsqueda del match más cercano
            for usuario in usuarios:
                dist = face_recognition.face_distance([np.array(usuario.face_embedding)], vec_query)[0]
                if dist < min_dist:
                    min_dist = dist
                    mejor_match = usuario

            # ==========================================
            # 4. CASO: USUARIO NO REGISTRADO (DESCONOCIDO)
            # ==========================================
            if not mejor_match:
                RegistroAcceso.objects.create(
                    area=area,
                    permitido=False,
                    estado="DENEGADO_DESCONOCIDO",
                    motivo_denegacion="Rostro no coincide con ningún empleado"
                )
                return Response({
                    "status": "DENIED", 
                    "mensaje": "Identidad no encontrada"
                }, status=status.HTTP_403_FORBIDDEN)

            # ==========================================
            # 5. VALIDACIÓN DE MATRIZ DE PERMISOS
            # ==========================================
            tiene_permiso = PermisoArea.objects.filter(
                rol=mejor_match.rol,
                area=area,
                puede_acceder=True
            ).exists()

            if not tiene_permiso:
                RegistroAcceso.objects.create(
                    usuario=mejor_match,
                    rol=mejor_match.rol,
                    area=area,
                    permitido=False,
                    estado="DENEGADO_PERMISO",
                    motivo_denegacion=f"El rol {mejor_match.rol.nombre} no tiene acceso a esta área"
                )
                return Response({
                    "status": "DENIED", 
                    "mensaje": "Usuario identificado pero sin privilegios para esta zona"
                }, status=status.HTTP_403_FORBIDDEN)

            # ==========================================
            # 6. ACCESO APROBADO (ÉXITO TOTAL)
            # ==========================================
            RegistroAcceso.objects.create(
                usuario=mejor_match,
                rol=mejor_match.rol,
                area=area,
                permitido=True, # Sincronizado para estadísticas correctas
                estado="APROBADO"
            )

            return Response({
                "status": "SUCCESS",
                "user": mejor_match.nombre_completo,
                "rol": mejor_match.rol.nombre,
                "area": area.nombre,
                "confidence": round(1 - min_dist, 2)
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "error": "Error interno en el motor biométrico",
                "detalle": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)