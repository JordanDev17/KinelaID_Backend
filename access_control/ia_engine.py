import face_recognition
import cv2
import numpy as np

class FaceEngine:
    @staticmethod
    def validar_liveness_y_calidad(frame_rgb, landmarks):
        """
        Analiza si el rostro es real y si la calidad es apta para extraer vectores.
        """
        # 1. Validación de Parpadeo (Ojos abiertos/cerrados)
        ojo_izq = landmarks['left_eye']
        ojo_der = landmarks['right_eye']
        
        def eye_aspect_ratio(eye):
            # Calculamos la distancia vertical vs horizontal
            v1 = np.linalg.norm(np.array(eye[1]) - np.array(eye[5]))
            v2 = np.linalg.norm(np.array(eye[2]) - np.array(eye[4]))
            h = np.linalg.norm(np.array(eye[0]) - np.array(eye[3]))
            return (v1 + v2) / (2.0 * h)

        ear = (eye_aspect_ratio(ojo_izq) + eye_aspect_ratio(ojo_der)) / 2.0
        
        # Un EAR bajo (< 0.2) indica ojos cerrados/parpadeo
        es_real = ear > 0.15 
        
        return es_real, ear

    @staticmethod
    def extraer_vector_seguro(frame_rgb, box):
        # Extraer el embedding solo si el rostro está bien definido
        embeddings = face_recognition.face_encodings(frame_rgb, [box])
        return embeddings[0] if embeddings else None