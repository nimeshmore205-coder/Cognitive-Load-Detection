import numpy as np

def euclidean_dist(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))

def calculate_ear(eye_points):
    """
    eye_points: list of 6 (x, y) tuples in order
    Returns: EAR value
    """
    # Vertical distances
    v1 = euclidean_dist(eye_points[1], eye_points[5])
    v2 = euclidean_dist(eye_points[2], eye_points[4])

    # Horizontal distance
    h = euclidean_dist(eye_points[0], eye_points[3])

    ear = (v1 + v2) / (2.0 * h)
    return ear
