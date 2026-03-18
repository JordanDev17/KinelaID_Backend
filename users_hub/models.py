# =========================
# IMPORTS
# =========================
from django.db import models


# =====================================================
# MODELO: ROL
# =====================================================
# Representa los diferentes roles del sistema
# Ejemplo: Administrador, Empleado, Visitante
class Rol(models.Model):

    # ID autoincremental
    rol_id = models.AutoField(primary_key=True)

    # Nombre del rol (único para evitar duplicados)
    nombre = models.CharField(max_length=50, unique=True)

    # Descripción opcional
    descripcion = models.TextField(null=True, blank=True)

    # Representación legible
    def __str__(self):
        return self.nombre


# =====================================================
# MODELO: USUARIO
# =====================================================
# Este modelo SOLO almacena información.
# La biometría se genera en access_control.
class Usuario(models.Model):

    # Identificador único
    usuario_id = models.AutoField(primary_key=True)

    # Relación con Rol
    rol = models.ForeignKey(
        Rol,
        on_delete=models.CASCADE,
        related_name='usuarios'
    )

    # Nombre completo
    nombre_completo = models.CharField(max_length=255)

    # Identificación única
    identificacion = models.CharField(max_length=50, unique=True)

    # Email opcional
    email = models.EmailField(
        max_length=100,
        null=True,
        blank=True,
        unique=True
    )

    # Estado del usuario
    activo = models.BooleanField(default=True)

    # =====================================================
    # IMÁGENES
    # =====================================================

    # Imagen base del rostro (opcional)
    # Puede usarse para auditoría o reentrenamiento
    foto_path_base = models.ImageField(
        upload_to='rostros/entrenamiento/',
        null=True,
        blank=True
    )

    # Imagen de perfil opcional
    foto_perfil_path = models.ImageField(
        upload_to='rostros/perfil/',
        null=True,
        blank=True
    )

    # =====================================================
    # VECTOR BIOMÉTRICO
    # =====================================================

    # Embedding facial generado por el motor biométrico
    # Normalmente 128 valores flotantes
    face_embedding = models.JSONField(
        null=True,
        blank=True
    )

    # Fecha de creación automática
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre_completo