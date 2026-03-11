import cv2

for i in range(10):

    cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)

    if cap.isOpened():

        ret, frame = cap.read()

        if ret:
            print(f"CAMARA FUNCIONAL -> index {i}")
        else:
            print(f"CAMARA ABRE PERO NO ENVIA FRAME -> index {i}")

        cap.release()

    else:
        print(f"No existe cámara -> index {i}")