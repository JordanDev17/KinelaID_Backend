import cv2
import threading
import time
import logging

logger = logging.getLogger(__name__)


class CameraManager:
    _instance = None
    _singleton_lock = threading.Lock()

    def __new__(cls):
        with cls._singleton_lock:
            if cls._instance is None:
                instance = super().__new__(cls)
                instance.cameras = {}        # idx -> cv2.VideoCapture
                instance.frames = {}         # idx -> último frame numpy
                instance.threads = {}        # idx -> Thread
                instance.running_flags = {}  # idx -> bool (señal de parada)
                instance._lock = threading.Lock()  # protege los dicts compartidos
                cls._instance = instance
        return cls._instance

    # ------------------------------------------------------------------
    # Inicialización desde base de datos
    # ------------------------------------------------------------------

    def initialize_all_cameras(self):
        """Lee la DB y arranca las cámaras marcadas como activas."""
        from .models import Camara

        time.sleep(0.5)  # Espera mínima para que Django ORM esté listo

        try:
            active_cams = Camara.objects.filter(is_activa=True)
        except Exception as e:
            logger.error(f"Error al leer DB de cámaras: {e}")
            return

        for cam in active_cams:
            idx = int(cam.hardware_index)
            if self.is_running(idx):
                logger.info(f"Cámara {idx} ya está corriendo, se omite.")
                continue
            self.start_camera(idx)

    # ------------------------------------------------------------------
    # Ciclo de vida de cada cámara
    # ------------------------------------------------------------------

    def start_camera(self, idx: int) -> bool:
        """Abre el hardware e inicia el hilo de captura. Retorna True si tuvo éxito."""
        if self.is_running(idx):
            logger.warning(f"start_camera({idx}): ya está en ejecución.")
            return True

        cap = self._open_camera(idx)
        if cap is None:
            logger.error(f"start_camera({idx}): no se pudo abrir la cámara.")
            return False

        with self._lock:
            self.cameras[idx] = cap
            self.frames[idx] = None
            self.running_flags[idx] = True

        thread = threading.Thread(
            target=self._capture_loop,
            args=(idx,),
            daemon=True,
            name=f"cam-{idx}",
        )
        with self._lock:
            self.threads[idx] = thread

        thread.start()
        logger.info(f"✓ Cámara {idx} iniciada (hilo: {thread.name})")
        return True

    def stop_camera(self, idx: int):
        """
        Señala al hilo que pare, espera que termine limpiamente
        y luego libera el hardware y limpia todos los diccionarios.
        """
        # 1. Señal de parada (ANTES del join para que el hilo la vea)
        with self._lock:
            self.running_flags[idx] = False

        # 2. Esperar que el hilo salga (timeout generoso para evitar
        #    que el join regrese mientras el hilo aún usa el cap)
        thread = self.threads.get(idx)
        if thread and thread.is_alive():
            thread.join(timeout=5.0)
            if thread.is_alive():
                logger.warning(
                    f"stop_camera({idx}): el hilo no terminó en 5 s; "
                    "puede haber una fuga de recurso."
                )

        # 3. Liberar hardware DESPUÉS de que el hilo haya salido
        with self._lock:
            cap = self.cameras.pop(idx, None)
            if cap is not None:
                try:
                    cap.release()
                except Exception as e:
                    logger.error(f"stop_camera({idx}): error al liberar cap: {e}")

            # Limpia TODOS los dicts para que initialize_all_cameras
            # pueda rearrancar esta cámara sin problema
            self.frames.pop(idx, None)
            self.threads.pop(idx, None)
            self.running_flags.pop(idx, None)

        logger.info(f"⚰ Cámara {idx} detenida y liberada.")

    def reset_all(self):
        """Para todas las cámaras y las reinicia según la DB."""
        indices = list(self.cameras.keys())
        logger.info(f"reset_all: deteniendo cámaras {indices}")
        for idx in indices:
            self.stop_camera(idx)

        time.sleep(1.0)  # Pausa para que el SO libere los descriptores

        logger.info("reset_all: reinicializando desde DB…")
        self.initialize_all_cameras()

    # ------------------------------------------------------------------
    # Hilo de captura
    # ------------------------------------------------------------------

    def _capture_loop(self, idx: int):
        """
        Bucle de captura para la cámara `idx`.
        - El hilo es el ÚNICO que lee/escribe el cap → no necesita lock interno.
        - Si hay demasiados fallos consecutivos intenta reabrir el hardware.
        - Sale limpiamente cuando running_flags[idx] se pone en False.
        """
        FAIL_THRESHOLD = 30
        fail_count = 0

        while self.running_flags.get(idx, False):
            cap = self.cameras.get(idx)

            # Cámara fue quitada externamente (raro pero posible)
            if cap is None or not cap.isOpened():
                time.sleep(0.1)
                fail_count += 1
                if fail_count > FAIL_THRESHOLD:
                    logger.error(f"Cámara {idx}: cap no disponible, saliendo del hilo.")
                    break
                continue

            # Captura
            try:
                grabbed = cap.grab()
                success, frame = cap.retrieve() if grabbed else (False, None)
            except Exception as e:
                logger.error(f"Cámara {idx}: excepción en captura: {e}")
                grabbed, success, frame = False, False, None

            if success and frame is not None:
                self.frames[idx] = frame
                fail_count = 0
            else:
                fail_count += 1
                if fail_count >= FAIL_THRESHOLD:
                    # Intenta reabrir el hardware SIN salir del hilo
                    restarted = self._restart_hardware_in_thread(idx, cap)
                    if not restarted:
                        break  # No se pudo recuperar → hilo termina
                    fail_count = 0

            time.sleep(0.01)  # ~100 fps máx; ajusta según necesidad

        # ---- Cleanup al salir ----
        # No tocamos self.cameras aquí: stop_camera() se encarga.
        logger.info(f"Hilo cámara {idx} terminado.")

    def _restart_hardware_in_thread(self, idx: int, old_cap) -> bool:
        """
        Llamado DESDE el hilo de captura para reabrir el hardware
        sin detener el hilo. Retorna True si tuvo éxito.
        """
        if not self.running_flags.get(idx, False):
            return False  # Ya nos pidieron parar

        logger.warning(f"Cámara {idx}: demasiados fallos, reintentando apertura…")

        try:
            old_cap.release()
        except Exception:
            pass

        # Poner None mientras reabrimos
        with self._lock:
            self.cameras[idx] = None

        # Espera antes de reintentar (verifica flag para no bloquear el stop)
        for _ in range(20):
            if not self.running_flags.get(idx, False):
                return False
            time.sleep(0.1)

        new_cap = self._open_camera(idx)
        if new_cap is not None:
            with self._lock:
                self.cameras[idx] = new_cap
            logger.info(f"✓ Cámara {idx}: hardware reabierto exitosamente.")
            return True
        else:
            logger.error(f"Cámara {idx}: no se pudo reabrir el hardware.")
            return False

    # ------------------------------------------------------------------
    # Apertura de hardware con fallback de backends
    # ------------------------------------------------------------------

    def _open_camera(self, idx: int):
        """Intenta abrir la cámara con varios backends. Retorna cap o None."""
        backends = [
            ("MSMF", cv2.CAP_MSMF),
            ("DSHOW", cv2.CAP_DSHOW),
            ("AUTO", None),
        ]
        for name, backend in backends:
            try:
                cap = (
                    cv2.VideoCapture(idx)
                    if backend is None
                    else cv2.VideoCapture(idx, backend)
                )
                if cap.isOpened():
                    ret, _ = cap.read()
                    if ret:
                        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                        logger.info(f"Cámara {idx} abierta con backend {name}.")
                        return cap
                    cap.release()
            except Exception as e:
                logger.warning(f"Backend {name} falló para cámara {idx}: {e}")
        return None

    # ------------------------------------------------------------------
    # Consultas de estado
    # ------------------------------------------------------------------

    def get_frame(self, idx: int):
        return self.frames.get(idx)

    def is_running(self, idx: int) -> bool:
        thread = self.threads.get(idx)
        return thread is not None and thread.is_alive()

    def status(self) -> dict:
        """Retorna un dict con el estado de cada cámara registrada."""
        all_idx = set(self.cameras) | set(self.threads)
        return {
            idx: {
                "thread_alive": self.is_running(idx),
                "has_frame": self.frames.get(idx) is not None,
                "flag": self.running_flags.get(idx, False),
            }
            for idx in sorted(all_idx)
        }


# Instancia singleton global
camera_hub_instance = CameraManager()