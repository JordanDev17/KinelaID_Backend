import logging
import cv2
import face_recognition
from users_hub.models import Usuario, Rol
from .image_service import ImageService
from .face_service import FaceService
from ..ia_engine import FaceEngine

logger = logging.getLogger(__name__)

class EmployeeService:

    BLUR_MIN = 40  # Consistente con ProcesarLiveView

    @staticmethod
    def registrar_empleado(nombre, identificacion, rol_id, foto_b64):

        # ── 1. DECODIFICAR IMAGEN ─────────────────────────────────────────
        image = ImageService.decode_base64_image(foto_b64)
        if image is None:
            return None, "Imagen inválida"

        # ── 2. CALIDAD (blur) ─────────────────────────────────────────────
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        blur = cv2.Laplacian(gray, cv2.CV_64F).var()
        if blur < EmployeeService.BLUR_MIN:
            return None, "Imagen muy borrosa, intente con mejor iluminación"

        # ── 3. DETECTAR ROSTRO ────────────────────────────────────────────
        embeddings = FaceService.detectar_y_codificar(image)
        if not embeddings:
            return None, "No se detectó rostro"
        if len(embeddings) > 1:
            return None, "Solo debe haber una persona frente a la cámara"

        embedding = embeddings[0]

        # ── 4. LIVENESS (anti-spoofing) ───────────────────────────────────
        landmarks = face_recognition.face_landmarks(image)
        if not landmarks:
            return None, "No se pudieron detectar puntos faciales"

        es_real, ear = FaceEngine.validar_liveness_y_calidad(image, landmarks[0])
        if not es_real:
            return None, "Posible suplantación detectada, por favor mire a la cámara"

        # ── 5. DUPLICIDAD BIOMÉTRICA (umbral más amplio para registro) ────
        usuario_existente, dist = FaceService.buscar_coincidencia(
            embedding,
            umbral=FaceService.UMBRAL_REGISTRO  # 0.60 en vez de 0.45
        )
        if usuario_existente:
            return None, f"Este rostro ya está registrado como '{usuario_existente.nombre_completo}'"

        # ── 6. UNICIDAD POR IDENTIFICACIÓN ───────────────────────────────
        if Usuario.objects.filter(identificacion=identificacion).exists():
            return None, f"Ya existe un usuario con identificación '{identificacion}'"

        # ── 7. OBTENER ROL ────────────────────────────────────────────────
        try:
            rol = Rol.objects.get(rol_id=rol_id)
        except Rol.DoesNotExist:
            return None, "Rol inválido"

        # ── 8. CREAR USUARIO ──────────────────────────────────────────────
        usuario = Usuario.objects.create(
            nombre_completo=nombre,
            identificacion=identificacion,
            rol=rol,
            face_embedding=embedding.tolist()
        )

        logger.info(f"Usuario biométrico creado: {usuario.usuario_id} — EAR={ear:.3f} Blur={blur:.1f}")
        return usuario, None