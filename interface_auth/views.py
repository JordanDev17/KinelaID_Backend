import face_recognition
import numpy as np
import base64
from django.core.files.base import ContentFile
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny


from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
from .models import InterfazUsuario
from .serializers import InterfazUsuarioSerializer,InterfazUsuarioListSerializer, InterfazUsuarioWriteSerializer
import logging
logger = logging.getLogger(__name__)

class LoginStepOneView(APIView):
    """Paso 1: Validación de Credenciales"""
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        try:
            user = InterfazUsuario.objects.get(username=username, is_active=True)
            if not check_password(password, user.password):
                return Response({"error": "Credenciales incorrectas"}, status=401)
            
            # Si es Gerente o Administrador, enviamos SUCCESS de una vez
            # Si no, pedimos el SEGUNDO FACTOR (Rostro)
            rol = user.perfil.rol.nombre
            if rol in ['Gerente',]:
                serializer = InterfazUsuarioSerializer(user)
                return Response({
                    "status": "SUCCESS", 
                    "user_data": serializer.data,
                    "message": f"Bienvenido {rol}"
                })

            return Response({
                "status": "FACE_2FA_REQUIRED",
                "user_id": user.id,
                "message": "Se requiere verificación facial para este rol."
            })
        except InterfazUsuario.DoesNotExist:
            return Response({"error": "Usuario no registrado"}, status=404)

# users_hub/views.py

class LoginStepTwoFaceView(APIView):
    def post(self, request):
        user_id = request.data.get('user_id')
        # Importante: Verifica si tu Angular envía 'foto' o 'foto_base64'
        foto_b64 = request.data.get('foto') 

        try:
            user_interfaz = InterfazUsuario.objects.get(id=user_id)
            usuario_perfil = user_interfaz.perfil 
            
            format, imgstr = foto_b64.split(';base64,')
            data = ContentFile(base64.b64decode(imgstr), name="2fa_login.jpg")
            image = face_recognition.load_image_file(data)
            encodings = face_recognition.face_encodings(image)
            
            if not encodings:
                return Response({"error": "No se detectó rostro"}, status=400)
            
            # COMPARACIÓN REAL
            distancia = face_recognition.face_distance([np.array(usuario_perfil.face_embedding)], encodings[0])[0]
            confianza = float(round(1 - distancia, 4)) # Convertimos a float nativo para JSON
            
            es_valido = distancia < 0.5 

            # LOGS VISIBLES EN TERMINAL (Usamos print para debugging rápido)
            print("\n" + "🚀" * 15)
            print(f" IDENTIDAD VERIFICADA: {usuario_perfil.nombre_completo}")
            print(f" DISTANCIA CALCULADA: {distancia:.4f}")
            print(f" PORCENTAJE DE MATCH: {confianza * 100:.2f}%")
            print(f" ESTADO: {'ACCESO CONCEDIDO ✅' if es_valido else 'ACCESO DENEGADO ❌'}")
            print("🚀" * 15 + "\n")

            if es_valido:
                serializer = InterfazUsuarioSerializer(user_interfaz)
                return Response({
                    "status": "SUCCESS",
                    "user_data": serializer.data,
                    "confidence": confianza  # <-- Asegúrate de que esta clave sea 'confidence'
                })
            
            return Response({"error": "No coincide la biometría"}, status=403)
            
        except Exception as e:
            print(f"❌ ERROR CRÍTICO EN 2FA: {str(e)}")
            return Response({"error": str(e)}, status=500)
    """Paso 2: 2FA Biométrico con Logs de IA y cálculo de confianza"""
    def post(self, request):
        user_id = request.data.get('user_id')
        foto_b64 = request.data.get('foto')

        try:
            # 1. Obtener usuario y su embedding registrado
            user_interfaz = InterfazUsuario.objects.get(id=user_id)
            usuario_real = user_interfaz.perfil  # Relación con el modelo Usuario
            
            # 2. Procesar imagen de la webcam
            format, imgstr = foto_b64.split(';base64,')
            data = ContentFile(base64.b64decode(imgstr), name="2fa_login.jpg")
            image = face_recognition.load_image_file(data)
            
            encodings = face_recognition.face_encodings(image)
            
            if not encodings:
                logger.warning(f"Intento de login fallido: Rostro no detectado para usuario {user_interfaz.username}")
                return Response({"error": "No se detectó rostro"}, status=400)
            
            # 3. Cálculo de Distancia y Match (Igual que en ProcesarLiveView)
            encoding_en_vivo = encodings[0]
            encoding_db = np.array(usuario_real.face_embedding)
            
            # Calculamos la distancia (menor distancia = mayor similitud)
            distancia = face_recognition.face_distance([encoding_db], encoding_en_vivo)[0]
            confianza = round(1 - distancia, 4)
            umbral = 0.5 # Tu min_dist
            
            es_valido = distancia < umbral

            # ==========================================
            # LOGS DE DEPURACIÓN EN CONSOLA DJANGO
            # ==========================================
            print(f"\n" + "="*50)
            print(f" LOG DE ACCESO BIOMÉTRICO - KINELAID")
            print(f"="*50)
            print(f"USUARIO    : {usuario_real.nombre_completo}")
            print(f"ROL        : {usuario_real.rol.nombre}")
            print(f"DISTANCIA  : {round(distancia, 4)}")
            print(f"CONFIANZA  : {round(confianza * 100, 2)}%")
            print(f"RESULTADO  : {'✅ APROBADO' if es_valido else '❌ DENEGADO'}")
            print(f"="*50 + "\n")

            if es_valido:
                serializer = InterfazUsuarioSerializer(user_interfaz)
                return Response({
                    "status": "SUCCESS",
                    "user_data": serializer.data,
                    "confidence": confianza
                })
            
            return Response({"error": "La identidad biométrica no coincide"}, status=403)
            
        except Exception as e:
            logger.error(f"Error en 2FA: {str(e)}")
            return Response({"error": "Error interno en el motor de IA"}, status=500)
    """Paso 2: 2FA Biométrico (El rostro es el código)"""
    def post(self, request):
        user_id = request.data.get('user_id')
        foto_b64 = request.data.get('foto')

        try:
            user = InterfazUsuario.objects.get(id=user_id)
            # Decodificar imagen de la webcam
            format, imgstr = foto_b64.split(';base64,')
            data = ContentFile(base64.b64decode(imgstr), name="2fa_login.jpg")
            image = face_recognition.load_image_file(data)
            
            # Obtener embedding de la captura actual
            encodings = face_recognition.face_encodings(image)
            
            if not encodings:
                return Response({"error": "No se detectó rostro"}, status=400)
            
            # Comparar con el embedding guardado en el perfil
            match = face_recognition.compare_faces(
                [np.array(user.perfil.face_embedding)], 
                encodings[0], 
                tolerance=0.5 # Umbral estricto para 2FA
            )

            if match[0]:
                serializer = InterfazUsuarioSerializer(user)
                return Response({
                    "status": "SUCCESS",
                    "user_data": serializer.data
                })
            
            return Response({"error": "La identidad biométrica no coincide"}, status=403)
            
        except Exception as e:
            return Response({"error": str(e)}, status=500)
        
class InterfazUsuarioViewSet(viewsets.ModelViewSet):
    """
    CRUD de cuentas de acceso al panel de administración.
    
    GET  /api/auth-interfaz/usuarios/     → lista (sin contraseña)
    POST /api/auth-interfaz/usuarios/     → crear cuenta + hashear contraseña
    PUT  /api/auth-interfaz/usuarios/{id}/ → actualizar (contraseña opcional)
    PATCH /api/auth-interfaz/usuarios/{id}/ → actualizar parcial (ej: is_active)
    DELETE /api/auth-interfaz/usuarios/{id}/ → eliminar
    """
    queryset           = InterfazUsuario.objects.select_related('perfil', 'perfil__rol').all()
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        # En lectura: serializer seguro sin contraseña
        # En escritura: serializer que acepta password
        if self.action in ('list', 'retrieve'):
            return InterfazUsuarioListSerializer
        return InterfazUsuarioWriteSerializer

    def perform_create(self, serializer):
        # Hashear contraseña antes de guardar
        password = self.request.data.get('password', '')
        serializer.save(password=make_password(password) if password else '')

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True  # Siempre parcial para no romper si no viene password
        instance = self.get_object()
        data     = request.data.copy()

        if 'password' in data and data['password']:
            data['password'] = make_password(data['password'])
        elif 'password' in data:
            # Si viene vacío, ignorar y mantener la contraseña actual
            del data['password']

        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)