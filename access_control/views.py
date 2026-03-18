import cv2
import logging
import face_recognition
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from audit_log.models import Area
from .serializers import AccesoLiveSerializer
from .services.image_service import ImageService
from .services.face_service import FaceService
from .services.access_service import AccessService
from .services.employee_service import EmployeeService
from .ia_engine import FaceEngine

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class RegistrarEmpleadoView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            nombre = request.data.get("nombre_completo")
            identificacion = request.data.get("identificacion")
            rol_id = request.data.get("rol")
            foto_b64 = request.data.get("foto_registro")

            if not all([nombre, identificacion, rol_id, foto_b64]):
                return Response({"error": "Datos incompletos"}, status=status.HTTP_400_BAD_REQUEST)

            usuario, error = EmployeeService.registrar_empleado(nombre, identificacion, rol_id, foto_b64)

            if error:
                return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                "status": "SUCCESS",
                "usuario_id": usuario.usuario_id,
                "nombre": usuario.nombre_completo,
                "embedding_generado": True
            })
        except Exception as e:
            logger.exception("Error registrando empleado")
            return Response({"error": "Error interno", "detalle": str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class ProcesarLiveView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AccesoLiveSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        foto_b64 = serializer.validated_data["foto"]
        area_id = serializer.validated_data["area_id"]

        try:
            image = ImageService.decode_base64_image(foto_b64)
            if image is None:
                return Response({"status": "DENIED", "mensaje": "Imagen inválida"}, status=403)

            # 1. Calidad
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            blur = cv2.Laplacian(gray, cv2.CV_64F).var()
            if blur < 40:
                return Response({"status": "DENIED", "mensaje": "Imagen muy borrosa"}, status=403)

            # 2. IA Biometría
            embeddings = FaceService.detectar_y_codificar(image)
            if not embeddings:
                return Response({"status": "DENIED", "mensaje": "Rostro no detectado"}, status=403)

            # 3. Liveness (Anti-spoofing)
            landmarks = face_recognition.face_landmarks(image)
            es_real, _ = FaceEngine.validar_liveness_y_calidad(image, landmarks[0]) if landmarks else (False, 0)
            
            if not es_real:
                return Response({"status": "DENIED", "mensaje": "Intento de suplantación detectado"}, status=403)

            # 4. Decisión de Acceso (Biometría + Permisos de Rol)
            ip_origen = request.META.get("REMOTE_ADDR")
            permitido, resultado, confianza = AccessService.procesar_acceso(area_id, embeddings, ip_origen)

            if not permitido:
                return Response({
                    "status": "DENIED", 
                    "mensaje": str(resultado) # Devuelve el motivo (ej. Rol no autorizado)
                }, status=403)

            # 'resultado' es el objeto Usuario
            usuario = resultado
            area_obj = Area.objects.get(area_id=area_id)

            return Response({
                "status": "SUCCESS",
                "confidence": confianza,
                "area": area_obj.nombre,
                "user_data": {
                    "id": usuario.usuario_id,
                    "nombre": usuario.nombre_completo,
                    "identificacion": usuario.identificacion,
                    "rol": usuario.rol.nombre,
                    "email": usuario.email,
                    "foto": usuario.foto_perfil_path.url if usuario.foto_perfil_path else None
                }
            })

        except Exception as e:
            logger.exception("Error crítico en motor biométrico")
            return Response({"error": "Fallo en motor biométrico", "detalle": str(e)}, status=500)