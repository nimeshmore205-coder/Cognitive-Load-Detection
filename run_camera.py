import cv2
from src.face_detection.face_mesh import get_frame_with_metrics

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ Camera not accessible")
    exit()

print("✅ Camera started. Press ESC to exit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = get_frame_with_metrics(frame)
    cv2.imshow("Cognitive Load Detection", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
