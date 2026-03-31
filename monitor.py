"""
KinelaID Monitor — firmware simulado
=====================================
Dependencias:
    pip install opencv-python mediapipe requests numpy

Controles:
    [R]  Registrar empleado
    [A]  Verificar acceso
    [Q]  Salir
"""

import cv2
import base64
import requests
import time
import threading
import math
import numpy as np

# ── Intentar importar MediaPipe (face mesh) ─────────────────────────────────
try:
    import mediapipe as mp
    _MP_AVAILABLE = True
    _mp_face_mesh = mp.solutions.face_mesh
    _face_mesh    = _mp_face_mesh.FaceMesh(
        static_image_mode=False,
        max_num_faces=4,
        refine_landmarks=True,   # habilita iris landmarks (468+10)
        min_detection_confidence=0.5,
        min_tracking_confidence=0.45,
    )
    print("[mesh] MediaPipe disponible — malla facial activada")
except ImportError:
    _MP_AVAILABLE = False
    _face_mesh    = None
    print("[mesh] MediaPipe no encontrado — instala con: pip install mediapipe")

# ======================================================
# CONFIGURACIÓN
# ======================================================

BASE_URL     = "http://127.0.0.1:8000/api"
STREAM_URL   = f"{BASE_URL}/cameras/stream/0/"
API_ACCESS   = f"{BASE_URL}/access/verificar-live/"
API_REGISTER = f"{BASE_URL}/access/registrar-empleado/"
API_ROLES    = f"{BASE_URL}/users/roles/"
API_AREAS    = f"{BASE_URL}/audit/areas/"

RECONNECT_DELAY = 2
MSG_TIMEOUT     = 5        # segundos que permanece el mensaje en pantalla
JPEG_QUALITY    = 90

# ── Paleta BGR ──────────────────────────────────────────────────────────────
C_CYAN    = (255, 220,   0)   # amarillo-cyan  → zona de captura / UI
C_WHITE   = (255, 255, 255)
C_DARK    = ( 18,  18,  18)
C_GREEN   = (  0, 220, 100)
C_RED     = (  0,  60, 220)
C_AMBER   = (  0, 180, 255)

# ── Conexiones de malla ─────────────────────────────────────────────────────
# Subconjuntos de conexiones para una malla elegante sin saturar la pantalla
_MESH_CONTOURS = (
    frozenset([(10,338),(338,297),(297,332),(332,284),(284,251),(251,389),
               (389,356),(356,454),(454,323),(323,361),(361,288),(288,397),
               (397,365),(365,379),(379,378),(378,400),(400,377),(377,152),
               (152,148),(148,176),(176,149),(149,150),(150,136),(136,172),
               (172,58),(58,132),(132,93),(93,234),(234,127),(127,162),
               (162,21),(21,54),(54,103),(103,67),(67,109),(109,10)])   # oval cara
)

if _MP_AVAILABLE:
    from mediapipe.python.solutions.face_mesh_connections import (
        FACEMESH_TESSELATION,
        FACEMESH_CONTOURS,
        FACEMESH_IRISES,
    )

# ======================================================
# ESTADO GLOBAL DE UI
# ======================================================

ui_state = {
    "mensaje":    "Listo",
    "sub":        "",
    "color":      (180, 180, 180),
    "procesando": False,
    "timestamp":  0.0,
    "confianza":  None,
    "usuario":    None,
    "faces":      0,           # cantidad de rostros detectados
}
_ui_lock = threading.Lock()

def set_ui(mensaje: str, sub: str = "", color=C_WHITE,
           confianza=None, usuario=None):
    with _ui_lock:
        ui_state.update({
            "mensaje":   mensaje,
            "sub":       sub,
            "color":     color,
            "timestamp": time.time(),
            "confianza": confianza,
            "usuario":   usuario,
        })

def set_procesando(val: bool):
    with _ui_lock:
        ui_state["procesando"] = val

def set_faces(n: int):
    with _ui_lock:
        ui_state["faces"] = n

# ======================================================
# UTILIDADES
# ======================================================

def frame_to_base64(frame: np.ndarray) -> str:
    """Normaliza brillo/contraste antes de codificar para mejorar embeddings."""
    # CLAHE en canal L (luminancia)
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    frame_norm = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)

    _, buf = cv2.imencode(".jpg", frame_norm, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    return f"data:image/jpeg;base64,{base64.b64encode(buf).decode()}"

def seleccionar_opcion(lista: list, label: str) -> dict:
    print(f"\n--- SELECCIONE {label} ---")
    for i, item in enumerate(lista, 1):
        print(f"[{i}] {item.get('nombre', 'Sin nombre')}")
    while True:
        try:
            idx = int(input(f"Seleccione número (1-{len(lista)}): ")) - 1
            if 0 <= idx < len(lista):
                return lista[idx]
        except Exception:
            pass
        print("Opción inválida, intente de nuevo.")

def put_text_shadow(img, text, pos, scale, color, thickness=1, shadow_offset=1):
    """Texto con sombra para mejor legibilidad."""
    sx, sy = pos[0] + shadow_offset, pos[1] + shadow_offset
    cv2.putText(img, text, (sx, sy), cv2.FONT_HERSHEY_SIMPLEX,
                scale, (0, 0, 0), thickness + 1, cv2.LINE_AA)
    cv2.putText(img, text, pos, cv2.FONT_HERSHEY_SIMPLEX,
                scale, color, thickness, cv2.LINE_AA)

# ======================================================
# FACE MESH — dibujo en capa separada
# ======================================================

def _draw_connections(canvas: np.ndarray, lm_px: list, connections,
                      color, thickness: int = 1, alpha: float = 1.0):
    """Dibuja un conjunto de conexiones sobre el canvas."""
    if alpha < 1.0:
        overlay = canvas.copy()
        for (a, b) in connections:
            if a < len(lm_px) and b < len(lm_px):
                cv2.line(overlay, lm_px[a], lm_px[b], color, thickness, cv2.LINE_AA)
        cv2.addWeighted(overlay, alpha, canvas, 1 - alpha, 0, canvas)
    else:
        for (a, b) in connections:
            if a < len(lm_px) and b < len(lm_px):
                cv2.line(canvas, lm_px[a], lm_px[b], color, thickness, cv2.LINE_AA)

def apply_face_mesh(frame: np.ndarray, results) -> tuple[np.ndarray, int]:
    """
    Dibuja la malla facial sobre el frame.
    Retorna (frame_con_malla, num_rostros).
    """
    if results is None or not results.multi_face_landmarks:
        return frame, 0

    h, w = frame.shape[:2]
    output = frame.copy()
    n_faces = len(results.multi_face_landmarks)

    for face_lm in results.multi_face_landmarks:
        # Convertir landmarks normalizados a píxeles
        lm_px = [
            (int(p.x * w), int(p.y * h))
            for p in face_lm.landmark
        ]

        # ── Capa 1: teselación (malla fina, muy transparente) ───────────────
        _draw_connections(
            output, lm_px, FACEMESH_TESSELATION,
            color=(0, 220, 180),   # cyan-verde
            thickness=1,
            alpha=0.18,
        )

        # ── Capa 2: contornos (silueta facial, cejas, nariz, labios) ────────
        _draw_connections(
            output, lm_px, FACEMESH_CONTOURS,
            color=(0, 240, 200),
            thickness=1,
            alpha=0.55,
        )

        # ── Capa 3: iris ─────────────────────────────────────────────────────
        _draw_connections(
            output, lm_px, FACEMESH_IRISES,
            color=(0, 200, 255),   # cyan brillante
            thickness=1,
            alpha=0.75,
        )

        # ── Puntos clave en vértices de landmarks principales ────────────────
        key_pts = [1, 4, 6, 10, 33, 133, 152, 172, 263, 362, 389, 454]
        for idx in key_pts:
            if idx < len(lm_px):
                cv2.circle(output, lm_px[idx], 2, (0, 255, 200), -1, cv2.LINE_AA)

        # ── ID del rostro (esquina del bounding box) ─────────────────────────
        xs = [p[0] for p in lm_px]
        ys = [p[1] for p in lm_px]
        bx1, by1 = max(0, min(xs) - 10), max(0, min(ys) - 10)
        bx2, by2 = min(w, max(xs) + 10), min(h, max(ys) + 10)

        # Rectángulo del bounding box con esquinas decorativas
        _draw_bbox_hud(output, bx1, by1, bx2, by2)

    return output, n_faces


def _draw_bbox_hud(img, x1, y1, x2, y2, color=(0, 220, 180), size=14):
    """Dibuja las 4 esquinas estilo HUD alrededor del rostro."""
    t = 2
    # TL
    cv2.line(img, (x1, y1), (x1 + size, y1), color, t, cv2.LINE_AA)
    cv2.line(img, (x1, y1), (x1, y1 + size), color, t, cv2.LINE_AA)
    # TR
    cv2.line(img, (x2, y1), (x2 - size, y1), color, t, cv2.LINE_AA)
    cv2.line(img, (x2, y1), (x2, y1 + size), color, t, cv2.LINE_AA)
    # BL
    cv2.line(img, (x1, y2), (x1 + size, y2), color, t, cv2.LINE_AA)
    cv2.line(img, (x1, y2), (x1, y2 - size), color, t, cv2.LINE_AA)
    # BR
    cv2.line(img, (x2, y2), (x2 - size, y2), color, t, cv2.LINE_AA)
    cv2.line(img, (x2, y2), (x2, y2 - size), color, t, cv2.LINE_AA)

# ======================================================
# REGISTRO (hilo separado)
# ======================================================

def registrar_empleado(frame: np.ndarray):
    set_procesando(True)
    set_ui("Procesando registro...", color=C_AMBER)

    print("\n══════════════════════════════")
    print("  REGISTRO DE EMPLEADO")
    print("══════════════════════════════")
    nombre         = input("Nombre completo   : ")
    identificacion = input("Identificación    : ")

    try:
        roles = requests.get(API_ROLES, timeout=5).json()
        rol   = seleccionar_opcion(roles, "ROL")

        payload = {
            "nombre_completo": nombre,
            "identificacion":  identificacion,
            "rol":             rol["rol_id"],
            "foto_registro":   frame_to_base64(frame),
        }
        res  = requests.post(API_REGISTER, json=payload, timeout=10)
        data = res.json()
        print("SERVER →", data)

        if res.status_code == 200 and data.get("status") == "SUCCESS":
            set_ui(
                "REGISTRO EXITOSO",
                sub=f"{data.get('nombre', '')}  ·  ID: {data.get('usuario_id', '')}",
                color=C_GREEN,
            )
        else:
            set_ui(
                "REGISTRO FALLIDO",
                sub=data.get("error", "Error desconocido"),
                color=C_RED,
            )
    except Exception as e:
        print("Error registro:", e)
        set_ui("Error de conexión", sub=str(e), color=C_RED)
    finally:
        set_procesando(False)

# ======================================================
# ACCESO (hilo separado)
# ======================================================

def verificar_acceso(frame: np.ndarray):
    set_procesando(True)
    set_ui("Verificando acceso...", color=C_AMBER)

    print("\n══════════════════════════════")
    print("  VERIFICACIÓN DE ACCESO")
    print("══════════════════════════════")
    try:
        areas = requests.get(API_AREAS, timeout=5).json()
        area  = seleccionar_opcion(areas, "ÁREA")

        payload = {"foto": frame_to_base64(frame), "area_id": area["area_id"]}
        res     = requests.post(API_ACCESS, json=payload, timeout=10)
        data    = res.json()
        print("SERVER →", data)

        if res.status_code == 200 and data.get("status") == "SUCCESS":
            ud = data.get("user_data", {})
            set_ui(
                "ACCESO APROBADO",
                sub=(
                    f"{ud.get('nombre', '')}  ·  {ud.get('rol', '')}"
                    f"  ·  Conf: {data.get('confidence', 0):.1%}"
                ),
                color=C_GREEN,
                confianza=data.get("confidence"),
                usuario=ud,
            )
        else:
            set_ui(
                "ACCESO DENEGADO",
                sub=data.get("mensaje", data.get("error", "Sin motivo")),
                color=C_RED,
            )
    except Exception as e:
        print("Error acceso:", e)
        set_ui("Error de conexión", sub=str(e), color=C_RED)
    finally:
        set_procesando(False)

# ======================================================
# OVERLAY PRINCIPAL
# ======================================================

_SPINNER = ["|", "/", "—", "\\"]

def draw_overlay(frame: np.ndarray) -> np.ndarray:
    display = frame.copy()
    h, w    = display.shape[:2]

    with _ui_lock:
        estado = dict(ui_state)

    # ── Zona de captura ────────────────────────────────────────────────────
    cx1, cy1 = w // 4,     h // 6
    cx2, cy2 = 3 * w // 4, 5 * h // 6

    # Área semitransparente dentro de la zona de captura
    overlay_zone = display.copy()
    cv2.rectangle(overlay_zone, (cx1, cy1), (cx2, cy2), (0, 240, 200), -1)
    cv2.addWeighted(overlay_zone, 0.04, display, 0.96, 0, display)

    # Borde y esquinas HUD
    cv2.rectangle(display, (cx1, cy1), (cx2, cy2), C_CYAN, 1, cv2.LINE_AA)
    _draw_bbox_hud(display, cx1, cy1, cx2, cy2, color=C_CYAN, size=20)

    put_text_shadow(display, "ZONA DE CAPTURA",
                    (cx1 + 8, cy1 - 10), 0.48, C_CYAN, thickness=1)

    # ── Indicador de rostros detectados ───────────────────────────────────
    n = estado["faces"]
    face_color = C_GREEN if n == 1 else (C_AMBER if n > 1 else C_RED)
    face_label = f"ROSTROS: {n}"
    put_text_shadow(display, face_label, (cx2 - 120, cy1 - 10),
                    0.45, face_color, thickness=1)

    # ── Barra de controles (inferior) ─────────────────────────────────────
    bar_h = 38
    cv2.rectangle(display, (0, h - bar_h), (w, h), C_DARK, -1)

    # Línea separadora superior del bar
    cv2.line(display, (0, h - bar_h), (w, h - bar_h), C_CYAN, 1, cv2.LINE_AA)

    controls = "[R] Registrar    [A] Verificar Acceso    [Q] Salir"
    put_text_shadow(display, controls, (16, h - 11), 0.50, C_WHITE, thickness=1)

    # Indicador mesh activo
    mesh_txt = "MESH: ON" if _MP_AVAILABLE else "MESH: OFF"
    mesh_col = C_GREEN if _MP_AVAILABLE else (100, 100, 100)
    put_text_shadow(display, mesh_txt, (w - 120, h - 11), 0.42, mesh_col, thickness=1)

    # ── Panel de estado (superior) ────────────────────────────────────────
    if estado["procesando"]:
        spinner = _SPINNER[int(time.time() * 6) % 4]
        cv2.rectangle(display, (0, 0), (w, 52), (28, 28, 28), -1)
        cv2.line(display, (0, 52), (w, 52), C_AMBER, 1, cv2.LINE_AA)
        cv2.rectangle(display, (0, 0), (5, 52), C_AMBER, -1)
        put_text_shadow(display, f"{spinner}  Procesando...",
                        (16, 34), 0.70, C_AMBER, thickness=2)

    elif time.time() - estado["timestamp"] < MSG_TIMEOUT:
        color = estado["color"]

        # Fondo con blend
        ov2 = display.copy()
        cv2.rectangle(ov2, (0, 0), (w, 62), C_DARK, -1)
        cv2.addWeighted(ov2, 0.65, display, 0.35, 0, display)

        # Línea inferior del panel
        cv2.line(display, (0, 62), (w, 62), color, 1, cv2.LINE_AA)

        # Barra lateral de color
        cv2.rectangle(display, (0, 0), (6, 62), color, -1)

        # Texto principal
        put_text_shadow(display, estado["mensaje"], (16, 28), 0.80, color, thickness=2)

        # Sub-texto
        if estado["sub"]:
            put_text_shadow(display, estado["sub"], (16, 52), 0.48, C_WHITE, thickness=1)

        # Barra de confianza
        if estado["confianza"] is not None:
            _draw_confidence_bar(display, estado["confianza"], w)

    # ── Timestamp + FPS hint ──────────────────────────────────────────────
    ts = time.strftime("%H:%M:%S")
    put_text_shadow(display, ts, (w - 80, 20), 0.45, (100, 200, 160), thickness=1)

    return display


def _draw_confidence_bar(img, confidence: float, frame_w: int):
    """Barra de confianza HUD en esquina superior derecha."""
    bar_w  = 180
    bar_h  = 14
    bx     = frame_w - bar_w - 20
    by     = 72
    filled = int(bar_w * min(max(confidence, 0.0), 1.0))

    # Track
    cv2.rectangle(img, (bx, by), (bx + bar_w, by + bar_h), (45, 45, 45), -1)
    cv2.rectangle(img, (bx, by), (bx + bar_w, by + bar_h), (70, 70, 70), 1)

    # Fill — gradiente de color según nivel
    if confidence >= 0.80:
        bar_color = C_GREEN
    elif confidence >= 0.60:
        bar_color = C_AMBER
    else:
        bar_color = C_RED

    cv2.rectangle(img, (bx, by), (bx + filled, by + bar_h), bar_color, -1)

    # Etiqueta
    put_text_shadow(img, f"CONFIANZA: {confidence:.1%}",
                    (bx, by + bar_h + 16), 0.42, C_WHITE, thickness=1)

# ======================================================
# STREAM PRINCIPAL
# ======================================================

def conectar_stream():
    # Usamos la URL que apunta a video_stream_view de tu Django
    # STREAM_URL debe ser: http://127.0.0.1:8000/api/cameras/stream/0/
    print(f"[stream] Conectando al flujo MJPEG de KinelaID → {STREAM_URL}")
    
    # IMPORTANTE: Forzamos el backend a CAP_FFMPEG para manejar el stream HTTP
    cap = cv2.VideoCapture(STREAM_URL, cv2.CAP_FFMPEG)
    
    if not cap.isOpened():
        print("[stream] ERROR: El stream de Django no está disponible.")
        return None
        
    # Reducimos el buffer al mínimo para evitar lag
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    print("[stream] Conectado exitosamente al servidor.")
    return cap


def monitor_stream():
    cap = conectar_stream()
    if not cap:
        print("[stream] Abortando.")
        return

    print("\n══════════════════════════════════════════")
    print("  KinelaID Monitor — firmware v1.1")
    print("  [R] Registrar  [A] Acceso  [Q] Salir")
    print("══════════════════════════════════════════\n")

    set_ui("Listo — presiona [R] o [A]")

    # Contador FPS simple
    _fps_t = time.time()
    _fps_frames = 0
    _fps_display = 0.0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[stream] Frame perdido, reconectando...")
            cap.release()
            time.sleep(RECONNECT_DELAY)
            cap = conectar_stream()
            if not cap:
                return
            continue

        # ── Face Mesh ──────────────────────────────────────────────────────
        if _MP_AVAILABLE and _face_mesh:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb.flags.writeable = False
            results = _face_mesh.process(rgb)
            rgb.flags.writeable = True
            display_frame, n_faces = apply_face_mesh(frame.copy(), results)  # ← copia
        else:
            display_frame = frame.copy()
            n_faces = 0

        set_faces(n_faces)

        # ── Overlay UI ─────────────────────────────────────────────────────
        display = draw_overlay(display_frame)
        
        frozen = frame.copy()

        # FPS contador (esquina inferior derecha, sobre el bar)
        _fps_frames += 1
        if time.time() - _fps_t >= 1.0:
            _fps_display = _fps_frames / (time.time() - _fps_t)
            _fps_frames  = 0
            _fps_t       = time.time()

        h, w = display.shape[:2]
        put_text_shadow(display, f"{_fps_display:.0f} FPS",
                        (w - 80, h - 48), 0.42, (80, 160, 120), thickness=1)

        cv2.imshow("KinelaID Monitor", display)

        # ── Teclado ────────────────────────────────────────────────────────
        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

        if key in (ord("r"), ord("a")) and not ui_state["procesando"]:
            frozen = frame.copy()
            target = registrar_empleado if key == ord("r") else verificar_acceso
            threading.Thread(target=target, args=(frozen,), daemon=True).start()

    cap.release()
    cv2.destroyAllWindows()
    if _face_mesh:
        _face_mesh.close()
    print("\n[kinelaid] Monitor cerrado.")


# ======================================================
# MAIN
# ======================================================

if __name__ == "__main__":
    print("\n KinelaID Monitor  — iniciando...\n")
    monitor_stream()