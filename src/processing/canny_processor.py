import cv2
import numpy as np
from PIL import Image

def process_image_for_preview(original_image, blur_val, edges_val, threshold_val, traces_only_var, brightness_val):
    """
    Generates a preview image by converting the original image to traces and blending.
    Returns a PIL Image.
    """
    if original_image is None:
        return None

    arr = np.array(original_image)  # shape HxWx4
    try:
        gray = cv2.cvtColor(arr, cv2.COLOR_RGBA2GRAY)
    except Exception:
        gray = cv2.cvtColor(arr[..., :3], cv2.COLOR_RGB2GRAY)

    if blur_val > 0:
        if blur_val % 2 == 0:  # Gaussian blur kernel size must be odd
            blur_val += 1
        gray = cv2.GaussianBlur(gray, (blur_val, blur_val), 0)

    upper = int(edges_val)
    lower = int(threshold_val)

    edges = cv2.Canny(gray, lower, upper)

    if traces_only_var:
        traces = cv2.bitwise_not(edges)
        combined = cv2.cvtColor(traces, cv2.COLOR_GRAY2RGBA)
        combined[:, :, 3] = 255  # Make sure alpha is fully opaque
    else:
        edges_inv = cv2.bitwise_not(edges)
        edges_rgba = cv2.cvtColor(edges_inv, cv2.COLOR_GRAY2RGBA)

        brightness = float(brightness_val)
        brightness = max(0.1, min(3.0, brightness))

        base = arr.copy().astype(np.uint8)
        edges_rgba = edges_rgba.astype(np.uint8)

        boosted = cv2.convertScaleAbs(base[..., :3], alpha=brightness, beta=0)
        alpha = (
            base[..., 3:4]
            if base.shape[2] == 4
            else np.full((base.shape[0], base.shape[1], 1), 255, dtype=np.uint8)
        )
        combined_rgb = cv2.addWeighted(boosted, 0.85, edges_rgba[..., :3], 0.45, 0)
        combined = np.dstack([combined_rgb, alpha])

    return Image.fromarray(combined)
