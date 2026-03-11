# camera_hub/camera_manager.py

import cv2
import threading
import time
import logging

logger = logging.getLogger(__name__)


class CameraManager:

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CameraManager, cls).__new__(cls)

            cls._instance.cameras = {}
            cls._instance.frames = {}
            cls._instance.threads = {}

        return cls._instance

    # --------------------------------
    # Inicializar todas las cámaras
    # --------------------------------
    def initialize_all_cameras(self):

        from .models import Camara

        time.sleep(1)

        cams = Camara.objects.filter(is_activa=True)

        for cam in cams:

            idx = int(cam.hardware_index)

            if idx in self.cameras:
                continue

            cap = self._open_camera(idx)

            if cap is None:
                continue

            self.cameras[idx] = cap
            self.frames[idx] = None

            t = threading.Thread(
                target=self._capture_loop,
                args=(idx,),
                daemon=True
            )

            self.threads[idx] = t
            t.start()

            print(f"✓ Kinela ID: Cámara {idx} iniciada")

    # --------------------------------
    # Abrir cámara con fallback
    # --------------------------------
    def _open_camera(self, idx):

        backends = [
            cv2.CAP_MSMF,
            cv2.CAP_DSHOW,
            None
        ]

        for backend in backends:

            if backend is None:
                cap = cv2.VideoCapture(idx)
            else:
                cap = cv2.VideoCapture(idx, backend)

            if cap.isOpened():

                ret, frame = cap.read()

                if ret:
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    return cap

                cap.release()

        print(f"✗ Kinela ID: Cámara {idx} no funcional")

        return None

    # --------------------------------
    # Loop de captura (1 por cámara)
    # --------------------------------
    def _capture_loop(self, idx):

        cap = self.cameras[idx]

        fail_count = 0

        while True:

            cap.grab()
            success, frame = cap.retrieve()

            if success:

                self.frames[idx] = frame
                fail_count = 0

            else:

                fail_count += 1
                logger.warning(f"⚠ Frame perdido en cámara {idx}")

                if fail_count >= 30:

                    logger.error(f"⚠ Reiniciando cámara {idx}")

                    cap.release()

                    time.sleep(2)

                    new_cap = self._open_camera(idx)

                    if new_cap:

                        self.cameras[idx] = new_cap
                        cap = new_cap
                        fail_count = 0

                        print(f"✓ Cámara {idx} recuperada")

            time.sleep(0.01)

    # --------------------------------
    # Obtener frame actual
    # --------------------------------
    def get_frame(self, idx):

        return self.frames.get(idx)

    # --------------------------------
    # Obtener cámara
    # --------------------------------
    def get_camera(self, idx):

        return self.cameras.get(idx)


# Instancia global
camera_hub_instance = CameraManager()