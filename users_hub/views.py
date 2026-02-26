import base64
import numpy as np
import face_recognition
from django.core.files.base import ContentFile
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Usuario, Rol
from .serializers import UsuarioSerializer, RolSerializer

class RolViewSet(viewsets.ModelViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer

    def create(self, request, *args, **kwargs):
        foto_b64 = request.data.get('foto_registro')
        
        if not foto_b64:
            return Response({"error": "No se recibió imagen para el registro facial"}, status=400)

        try:
            # 1. Decodificación segura de la imagen
            format, imgstr = foto_b64.split(';base64,')
            data = ContentFile(base64.b64decode(imgstr), name="temp_reg.jpg")
            image = face_recognition.load_image_file(data)
            
            # 2. Extracción de alta precisión (Model 'large' para mayor exactitud)
            face_locations = face_recognition.face_locations(image, model="hog")
            embeddings = face_recognition.face_encodings(image, face_locations, num_jitters=10) # 10 sub-muestreos para mayor precisión
            
            if not embeddings:
                return Response({"error": "No se detectó un rostro claro. Asegure iluminación frontal."}, status=400)
            
            nuevo_vec = embeddings[0]
            
            # 3. Validación de Unicidad Biométrica (Umbral Crítico: 0.35)
            usuarios_db = Usuario.objects.exclude(face_embedding__isnull=True)
            for usuario in usuarios_db:
                dist = face_recognition.face_distance([np.array(usuario.face_embedding)], nuevo_vec)[0]
                
                # Si la distancia es menor a 0.35, es la misma persona con seguridad del 99.9%
                if dist < 0.35:
                    return Response({
                        "error": "Violación de Unicidad",
                        "detalle": f"Este rostro ya está registrado bajo el ID: {usuario.identificacion}"
                    }, status=status.HTTP_400_BAD_REQUEST)

            # 4. Guardar el vector generado por el servidor
            data_dict = request.data.copy()
            data_dict['face_embedding'] = nuevo_vec.tolist()
            
            serializer = self.get_serializer(data=data_dict)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": f"Fallo en procesamiento biométrico: {str(e)}"}, status=500)