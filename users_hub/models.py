# Importo models desde Django, que es la base para definir
# las tablas de la base de datos usando clases Python
from django.db import models


# =========================
# MODELO: ROL
# =========================
# Este modelo representa los roles del sistema (ej: Administrador, Empleado, Visitante)
# Los uso para controlar qué puede hacer cada usuario dentro del sistema
class Rol(models.Model):

    # Django crea un ID automáticamente, pero yo lo defino explícitamente
    # para tener más control y claridad en la base de datos
    rol_id = models.AutoField(primary_key=True)

    # Nombre del rol (ej: "Administrador")
    # Lo marco como único para evitar roles duplicados
    nombre = models.CharField(max_length=50, unique=True)

    # Descripción opcional del rol
    # null=True -> puede guardarse como NULL en la BD
    # blank=True -> el formulario permite dejarlo vacío
    descripcion = models.TextField(null=True, blank=True)

    # Este método define cómo se mostrará el rol
    # cuando lo vea en el admin de Django o en la consola
    def __str__(self):
        return self.nombre


# =========================
# MODELO: USUARIO
# =========================
# Este modelo representa a las personas que tendrán acceso
# al sistema mediante reconocimiento facial
class Usuario(models.Model):

    # Identificador único del usuario
    # Lo defino manualmente para mantener consistencia
    usuario_id = models.AutoField(primary_key=True)

    # Relación con el modelo Rol
    # Cada usuario tiene un rol
    # on_delete=models.CASCADE -> si se elimina el rol, se eliminan sus usuarios
    # related_name='usuarios' -> me permite acceder desde Rol a sus usuarios
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE, related_name='usuarios')

    # Nombre completo del usuario (como aparecerá en reportes y registros)
    nombre_completo = models.CharField(max_length=255)

    # Identificación única (cédula, carnet, etc.)
    # La hago única para evitar duplicados
    identificacion = models.CharField(max_length=50, unique=True)

    # Correo electrónico del usuario
    # Puede ser nulo, pero si existe debe ser único
    email = models.EmailField(max_length=100, null=True, unique=True)

    # Indica si el usuario está activo en el sistema
    # Me sirve para bloquear accesos sin borrar registros
    activo = models.BooleanField(default=True)

    # =========================
    # MANEJO DE IMÁGENES
    # =========================

    # Imagen base del rostro del usuario
    # Esta imagen se usa para entrenar o generar el embedding facial
    # Se guarda en la carpeta: media/rostros/entrenamiento/
    foto_path_base = models.ImageField(upload_to='rostros/entrenamiento/',        null=True,
        blank=True)

    # Imagen de perfil del usuario
    # Es opcional y solo se usa para visualización
    foto_perfil_path = models.ImageField(
        upload_to='rostros/perfil/',
        null=True,
        blank=True
    )

    # =========================
    # RECONOCIMIENTO FACIAL
    # =========================

    # Aquí guardo el vector facial (embedding) generado por la IA
    # Normalmente es un arreglo de números que representa el rostro
    # Uso JSONField porque es flexible y fácil de serializar
    face_embedding = models.JSONField(null=True, blank=True)

    # Fecha en la que se creó el usuario
    # Django la asigna automáticamente al guardar el registro
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    
   

    # Define cómo se muestra el usuario en el admin o en logs
    def __str__(self):
        return self.nombre_completo
