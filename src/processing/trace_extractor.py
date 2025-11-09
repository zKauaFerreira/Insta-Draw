import json
import os

import cv2
import numpy as np
from PIL import Image

def extract_and_normalize_traces(original_image, blur_val, edges_val, threshold_val, traces_file_path="data/traces.json"):
    """
    Processes the original image to extract raw, normalized traces and their bounding box.
    Saves the traces to a JSON file.
    Returns a tuple (success_status, message).
    """
    if original_image is None:
        return False, "Nenhuma imagem original fornecida."

    arr = np.array(original_image)
    try:
        gray = cv2.cvtColor(arr, cv2.COLOR_RGBA2GRAY)
    except Exception:
        gray = cv2.cvtColor(arr[..., :3], cv2.COLOR_RGB2GRAY)

    if blur_val > 0:
        if blur_val % 2 == 0:
            blur_val += 1
        gray = cv2.GaussianBlur(gray, (blur_val, blur_val), 0)

    upper = int(edges_val)
    lower = int(threshold_val)
    edges = cv2.Canny(gray, lower, upper)

    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return False, "Nenhum traço foi encontrado com as configurações atuais."

    all_raw_points = []
    raw_processed_traces = []

    for contour in contours:
        coords = contour.squeeze().tolist()
        if not isinstance(coords[0], list):  # Handle single point contours
            coords = [coords]
        
        for p in coords:
            all_raw_points.append(p)
        
        raw_processed_traces.append({"path": coords})
    
    if not all_raw_points:
        return False, "Nenhum traço foi encontrado com as configurações atuais."

    min_x = min(p[0] for p in all_raw_points)
    min_y = min(p[1] for p in all_raw_points)
    max_x = max(p[0] for p in all_raw_points)
    max_y = max(p[1] for p in all_raw_points)

    raw_bbox_width = max_x - min_x
    raw_bbox_height = max_y - min_y

    if raw_bbox_width == 0 or raw_bbox_height == 0:
        return False, "A caixa delimitadora dos traços é zero. Não é possível escalar."

    normalized_traces = []
    for trace in raw_processed_traces:
        normalized_path = []
        for p in trace["path"]:
            normalized_path.append([p[0] - min_x, p[1] - min_y])
        normalized_traces.append({"path": normalized_path})

    traces_data_to_save = {
        "raw_bbox_width": raw_bbox_width,
        "raw_bbox_height": raw_bbox_height,
        "traces": normalized_traces
    }

    try:
        with open(traces_file_path, "w") as f:
            json.dump(traces_data_to_save, f, indent=4)
        return True, f"Traços brutos normalizados salvos em {traces_file_path}."
    except Exception as e:
        return False, f"Erro ao salvar traços: {e}"
