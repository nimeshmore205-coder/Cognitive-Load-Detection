import cv2
import numpy as np

# Eye landmark indices (MediaPipe standard)
LEFT_EYE_IDX = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_IDX = [362, 385, 387, 263, 373, 380]

def draw_eye_contours(frame, face_landmarks):
    """
    Draws left and right eye contours on the frame.
    """
    h, w, _ = frame.shape

    left_eye_points = []
    right_eye_points = []

    for idx in LEFT_EYE_IDX:
        lm = face_landmarks[idx]
        x, y = int(lm.x * w), int(lm.y * h)
        left_eye_points.append((x, y))

    for idx in RIGHT_EYE_IDX:
        lm = face_landmarks[idx]
        x, y = int(lm.x * w), int(lm.y * h)
        right_eye_points.append((x, y))

    # Draw contours
    cv2.polylines(frame, [cv2.convexHull(
        np.array(left_eye_points))], True, (255, 0, 0), 1)

    cv2.polylines(frame, [cv2.convexHull(
        np.array(right_eye_points))], True, (255, 0, 0), 1)

    return frame, left_eye_points, right_eye_points
