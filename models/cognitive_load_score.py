def clamp(value, min_val=0.0, max_val=1.0):
    return max(min(value, max_val), min_val)

def compute_cognitive_load(
    avg_ear,
    blink_rate,
    baseline_ear,
    baseline_blink_rate
):
    """
    Returns:
    - cognitive load score (0–100)
    - label: Low / Medium / High
    """

    # Avoid division by zero
    if baseline_ear <= 0 or baseline_blink_rate <= 0:
        return 0.0, "Low"

    # Normalized deviations
    ear_dev = clamp((baseline_ear - avg_ear) / baseline_ear)
    blink_dev = clamp((baseline_blink_rate - blink_rate) / baseline_blink_rate)

    # Weighted cognitive load score
    load_score = (0.6 * ear_dev + 0.4 * blink_dev) * 100

    # Classification
    if load_score < 35:
        label = "Low"
    elif load_score < 65:
        label = "Medium"
    else:
        label = "High"

    return round(load_score, 1), label
