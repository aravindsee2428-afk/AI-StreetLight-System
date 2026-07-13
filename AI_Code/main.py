import cv2
from ultralytics import YOLO
import serial
import time

# ==============================
# ESP32 SERIAL SETTINGS
# ==============================
COM_PORT = "COM5"      # Change if your ESP32 is on another COM port
BAUD_RATE = 115200

esp = serial.Serial(COM_PORT, BAUD_RATE)
time.sleep(2)

# ==============================
# LOAD YOLO MODEL
# ==============================
model = YOLO("yolov8n.pt")

# ==============================
# IP WEBCAM URL
# ==============================
url = "http://192.168.1.6:8080/video"

cap = cv2.VideoCapture(url)

previous_brightness = -1

print("AI Street Lighting Started...")

while True:

    ret, frame = cap.read()

    if not ret:
        print("Camera Error")
        break

    # Run YOLO
    results = model(frame, verbose=False)

    person_count = 0

    for result in results:

        boxes = result.boxes

        for box in boxes:

            cls = int(box.cls[0])

            # PERSON CLASS = 0
            if cls == 0:

                person_count += 1

                x1, y1, x2, y2 = map(int, box.xyxy[0])

                confidence = float(box.conf[0])

                cv2.rectangle(frame,
                              (x1, y1),
                              (x2, y2),
                              (0,255,0),
                              2)

                cv2.putText(frame,
                            f"Person {confidence:.2f}",
                            (x1, y1-10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (0,255,0),
                            2)

    # ======================================
    # AI BRIGHTNESS DECISION
    # ======================================

    if person_count == 0:
        brightness = 20

    elif person_count == 1:
        brightness = 40

    elif person_count == 2:
        brightness = 60

    elif person_count == 3:
        brightness = 80

    else:
        brightness = 100

    # ======================================
    # SEND TO ESP32 ONLY WHEN VALUE CHANGES
    # ======================================

    if brightness != previous_brightness:

        esp.write((str(brightness) + "\n").encode())

        print(f"Brightness Sent : {brightness}")

        previous_brightness = brightness

    # ======================================
    # DISPLAY
    # ======================================

    cv2.putText(frame,
                f"People : {person_count}",
                (20,40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255,0,0),
                2)

    cv2.putText(frame,
                f"Brightness : {brightness}%",
                (20,80),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0,0,255),
                2)

    cv2.imshow("AI Smart Street Lighting", frame)

    key = cv2.waitKey(1)

    if key == 27:
        break

cap.release()
cv2.destroyAllWindows()

esp.close()