import math

# Instagram color palette with refined categories for the new algorithm
INSTAGRAM_PALETTE = {
    1: [
        {"name": "White color", "hex": "#FFFFFF", "rgb": (255, 255, 255), "category": "neutral"},
        {"name": "Blue color", "hex": "#3897F0", "rgb": (56, 151, 240), "category": "vibrant"},
        {"name": "Green color", "hex": "#4DC752", "rgb": (77, 199, 82), "category": "vibrant"},
        {"name": "Yellow color", "hex": "#FFDC4C", "rgb": (255, 220, 76), "category": "vibrant"},
        {"name": "Orange color", "hex": "#FF9900", "rgb": (255, 153, 0), "category": "vibrant"},
        {"name": "Orange-red color", "hex": "#FF4C4C", "rgb": (255, 76, 76), "category": "vibrant"},
        {"name": "Red-purple color", "hex": "#974CFF", "rgb": (151, 76, 255), "category": "vibrant"},
        {"name": "Purple color", "hex": "#C300F5", "rgb": (195, 0, 245), "category": "vibrant"},
        {"name": "Red color", "hex": "#F5004F", "rgb": (245, 0, 79), "category": "vibrant"}
    ],
    2: [
        {"name": "Red-pink color", "hex": "#FF4D97", "rgb": (255, 77, 151), "category": "vibrant"},
        {"name": "Pink color", "hex": "#FF99CC", "rgb": (255, 153, 204), "category": "pastel"},
        {"name": "Beige color", "hex": "#F5DEB3", "rgb": (245, 222, 179), "category": "pastel"},
        {"name": "Pale orange color", "hex": "#F0A078", "rgb": (240, 160, 120), "category": "pastel"},
        {"name": "Light brown color", "hex": "#AF8760", "rgb": (175, 135, 96), "category": "neutral"},
        {"name": "Brown color", "hex": "#795548", "rgb": (121, 85, 72), "category": "neutral"},
        {"name": "Dark gray 3 color", "hex": "#444444", "rgb": (68, 68, 68), "category": "neutral"},
        {"name": "Dark gray 2 color", "hex": "#222222", "rgb": (34, 34, 34), "category": "neutral"},
        {"name": "Dark gray 1 color", "hex": "#000000", "rgb": (0, 0, 0), "category": "neutral"}
    ],
    3: [
        {"name": "Medium gray 3 color", "hex": "#AAAAAA", "rgb": (170, 170, 170), "category": "neutral"},
        {"name": "Medium gray 2 color", "hex": "#888888", "rgb": (136, 136, 136), "category": "neutral"},
        {"name": "Medium gray 1 color", "hex": "#666666", "rgb": (102, 102, 102), "category": "neutral"},
        {"name": "Light gray 3 color", "hex": "#CCCCCC", "rgb": (204, 204, 204), "category": "pastel"}
    ],
}

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb_tuple):
    return '#%02x%02x%02x' % rgb_tuple

def rgb_to_hsl(r, g, b):
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    mx, mn = max(r, g, b), min(r, g, b)
    l = (mx + mn) / 2.0
    if mx == mn:
        h = s = 0
    else:
        d = mx - mn
        s = d / (2.0 - mx - mn) if l > 0.5 else d / (mx + mn)
        if mx == r: h = (g - b) / d + (6 if g < b else 0)
        elif mx == g: h = (b - r) / d + 2
        else: h = (r - g) / d + 4
        h /= 6
    return h * 360, s, l

def rgb_to_lab(r, g, b):
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    r = ((r + 0.055) / 1.055) ** 2.4 if r > 0.04045 else r / 12.92
    g = ((g + 0.055) / 1.055) ** 2.4 if g > 0.04045 else g / 12.92
    b = ((b + 0.055) / 1.055) ** 2.4 if b > 0.04045 else b / 12.92
    r, g, b = r * 100, g * 100, b * 100
    x = r * 0.4124 + g * 0.3576 + b * 0.1805
    y = r * 0.2126 + g * 0.7152 + b * 0.0722
    z = r * 0.0193 + g * 0.1192 + b * 0.9505
    x /= 95.047
    y /= 100.000
    z /= 108.883
    x = x ** (1/3) if x > 0.008856 else (7.787 * x) + (16 / 116)
    y = y ** (1/3) if y > 0.008856 else (7.787 * y) + (16 / 116)
    z = z ** (1/3) if z > 0.008856 else (7.787 * z) + (16 / 116)
    return (116 * y) - 16, 500 * (x - y), 200 * (y - z)

def delta_e_ciede2000(lab1, lab2):
    L1, a1, b1 = lab1
    L2, a2, b2 = lab2
    C1 = math.sqrt(a1**2 + b1**2)
    C2 = math.sqrt(a2**2 + b2**2)
    C_bar = (C1 + C2) / 2
    G = 0.5 * (1 - math.sqrt(C_bar**7 / (C_bar**7 + 25**7)))
    a1_prime = (1 + G) * a1
    a2_prime = (1 + G) * a2
    C1_prime = math.sqrt(a1_prime**2 + b1**2)
    C2_prime = math.sqrt(a2_prime**2 + b2**2)
    h1_prime = math.degrees(math.atan2(b1, a1_prime)) % 360
    h2_prime = math.degrees(math.atan2(b2, a2_prime)) % 360
    delta_L_prime = L2 - L1
    delta_C_prime = C2_prime - C1_prime
    delta_h_prime = 0
    if C1_prime * C2_prime != 0:
        if abs(h1_prime - h2_prime) <= 180:
            delta_h_prime = h2_prime - h1_prime
        elif h2_prime <= h1_prime:
            delta_h_prime = h2_prime - h1_prime + 360
        else:
            delta_h_prime = h2_prime - h1_prime - 360
    delta_H_prime = 2 * math.sqrt(C1_prime * C2_prime) * math.sin(math.radians(delta_h_prime) / 2)
    L_bar_prime = (L1 + L2) / 2
    C_bar_prime = (C1_prime + C2_prime) / 2
    h_bar_prime = 0
    if C1_prime * C2_prime != 0:
        if abs(h1_prime - h2_prime) <= 180:
            h_bar_prime = (h1_prime + h2_prime) / 2
        elif (h1_prime + h2_prime) < 360:
            h_bar_prime = (h1_prime + h2_prime + 360) / 2
        else:
            h_bar_prime = (h1_prime + h2_prime - 360) / 2
    T = 1 - 0.17 * math.cos(math.radians(h_bar_prime - 30)) + 0.24 * math.cos(math.radians(2 * h_bar_prime)) + 0.32 * math.cos(math.radians(3 * h_bar_prime + 6)) - 0.20 * math.cos(math.radians(4 * h_bar_prime - 63))
    delta_theta = 30 * math.exp(-(((h_bar_prime - 275) / 25)**2))
    R_C = 2 * math.sqrt(C_bar_prime**7 / (C_bar_prime**7 + 25**7))
    S_L = 1 + ((0.015 * (L_bar_prime - 50)**2) / math.sqrt(20 + (L_bar_prime - 50)**2))
    S_C = 1 + 0.045 * C_bar_prime
    S_H = 1 + 0.015 * C_bar_prime * T
    R_T = -math.sin(math.radians(2 * delta_theta)) * R_C
    kL, kC, kH = 1, 1, 1
    delta_E = math.sqrt((delta_L_prime / (kL * S_L))**2 + (delta_C_prime / (kC * S_C))**2 + (delta_H_prime / (kH * S_H))**2 + R_T * (delta_C_prime / (kC * S_C)) * (delta_H_prime / (kH * S_H)))
    return delta_E

_PALETTE_LAB_CACHE = None

def _initialize_lab_cache():
    global _PALETTE_LAB_CACHE
    if _PALETTE_LAB_CACHE is None:
        _PALETTE_LAB_CACHE = {}
        print("Initializing LAB color cache for the palette...")
        for page_index, colors in INSTAGRAM_PALETTE.items():
            _PALETTE_LAB_CACHE[page_index] = []
            for color in colors:
                _PALETTE_LAB_CACHE[page_index].append(rgb_to_lab(*color["rgb"]))
        print("✅ LAB cache initialized.")

def get_nearest_palette_color(r, g, b):
    if _PALETTE_LAB_CACHE is None:
        _initialize_lab_cache()

    input_lab = rgb_to_lab(r, g, b)
    h, s, l = rgb_to_hsl(r, g, b)

    search_palette = []
    for page_index, colors in INSTAGRAM_PALETTE.items():
        for color_index, color in enumerate(colors):
            search_palette.append((page_index, color_index, color))

    candidates = []
    for page_index, color_index, color in search_palette:
        palette_lab = _PALETTE_LAB_CACHE[page_index][color_index]
        de = delta_e_ciede2000(input_lab, palette_lab)
        
        penalty = 0.0
        category = color.get("category", "").lower()

        if s >= 0.15 and category == 'neutral':
            penalty = 12.0
        if s < 0.15 and category in ('neutral', 'pastel'):
            penalty -= 4.0
            
        score = de + penalty
        candidates.append((score, de, page_index, color_index, color))

    candidates.sort(key=lambda x: x[0])

    # print(f"\nPIXEL ({r},{g},{b}) -> HSL({h:.2f},{s:.2f},{l:.2f}), LAB({input_lab[0]:.2f},{input_lab[1]:.2f},{input_lab[2]:.2f})")
    top3 = candidates[:3]
    # print("TOP3:", [(c[4]['name'], f"ΔE={c[1]:.2f}", f"score={c[0]:.2f}") for c in top3])

    best_score, best_de, best_page_index, best_color_index, best_color = candidates[0]

    if best_color.get("category", "").lower() == 'neutral' and s > 0.2:
        if len(candidates) > 1 and (candidates[1][0] - best_score) < 8:
            if candidates[1][4].get("category", "").lower() != 'neutral':
                best_score, best_de, best_page_index, best_color_index, best_color = candidates[1]

    # print("CHOSEN:", best_color['name'], f"ΔE={best_de:.2f}", f"score={best_score:.2f}")

    return {
        "page_index": best_page_index,
        "color_index": best_color_index,
        "name": best_color['name'],
        "hex_value": best_color['hex'],
        "rgb_value": best_color['rgb'],
        "delta_e": best_de
    }

def run_color_tests():
    print("\n--- Running Color Tests ---")
    
    tests = {
        "Test A (Yellow)": (250, 240, 100),
        "Test B (Light Yellow)": (245, 220, 80),
        "Test C (Light Gray)": (200, 200, 200),
    }
    
    for test_name, rgb in tests.items():
        print(f"\n--- {test_name} ---")
        get_nearest_palette_color(*rgb)
        
    print("\n--- Color Tests Finished ---")

if __name__ == '__main__':
    run_color_tests()

