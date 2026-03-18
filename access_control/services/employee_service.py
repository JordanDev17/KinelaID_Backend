import logging

from users_hub.models import Usuario, Rol

from .image_service import ImageService
from .face_service import FaceService


logger = logging.getLogger(__name__)


class EmployeeService:
    """
    Servicio encargado de registrar empleados
    con biometría facial.
    """

    @staticmethod
    def registrar_empleado(nombre, identificacion, rol_id, foto_b64):

        # ==========================
        # DECODIFICAR IMAGEN
        # ==========================

        image = ImageService.decode_base64_image(foto_b64)

        if image is None:
            return None, "Imagen inválida"

        # ==========================
        # DETECTAR ROSTRO
        # ==========================

        embeddings = FaceService.detectar_y_codificar(image)

        if not embeddings:
            return None, "No se detectó rostro"

        if len(embeddings) > 1:
            return None, "Solo una persona frente a la cámara"

        embedding = embeddings[0]

        # ==========================
        # VALIDAR DUPLICIDAD
        # ==========================

        usuario_existente, dist = FaceService.buscar_coincidencia(
            embedding
        )

        if usuario_existente:

            return None, f"Este rostro ya pertenece a {usuario_existente.nombre_completo}"

        # ==========================
        # OBTENER ROL
        # ==========================

        try:
            rol = Rol.objects.get(rol_id=rol_id)

        except Rol.DoesNotExist:
            return None, "Rol inválido"

        # ==========================
        # CREAR USUARIO
        # ==========================

        usuario = Usuario.objects.create(

            nombre_completo=nombre,
            identificacion=identificacion,
            rol=rol,
            face_embedding=embedding.tolist()

        )

        logger.info(f"Usuario biométrico creado {usuario.usuario_id}")

        return usuario, None