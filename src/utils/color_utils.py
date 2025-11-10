import math

# Instagram color palette with HEX and RGB values
INSTAGRAM_PALETTE = {
    1: [ # Página 1: Cores Vibrantes (Ordem padrão: Branco, Azul, Verde, Amarelo...)
        {"name": "White color", "hex": "#FFFFFF", "rgb": (255, 255, 255)},
        {"name": "Blue color", "hex": "#3897F0", "rgb": (56, 151, 240)},
        {"name": "Green color", "hex": "#4DC752", "rgb": (77, 199, 82)},
        {"name": "Yellow color", "hex": "#FFDC4C", "rgb": (255, 220, 76)},
        {"name": "Orange color", "hex": "#FF9900", "rgb": (255, 153, 0)},
        {"name": "Orange-red color", "hex": "#FF4C4C", "rgb": (255, 76, 76)},
        {"name": "Red-purple color", "hex": "#974CFF", "rgb": (151, 76, 255)},
        {"name": "Purple color", "hex": "#C300F5", "rgb": (195, 0, 245)},
        {"name": "Red color", "hex": "#F5004F", "rgb": (245, 0, 79)}
    ],
    2: [ # Página 2: Tons de Pele/Neutros (Ordem visual na Imagem 3)
        {"name": "Red-pink color", "hex": "#FF4D97", "rgb": (255, 77, 151)},
        {"name": "Pink color", "hex": "#FF99CC", "rgb": (255, 153, 204)},
        {"name": "Beige color", "hex": "#F5DEB3", "rgb": (245, 222, 179)},
        {"name": "Pale orange color", "hex": "#F0A078", "rgb": (240, 160, 120)},
        {"name": "Light brown color", "hex": "#AF8760", "rgb": (175, 135, 96)},
        {"name": "Brown color", "hex": "#795548", "rgb": (121, 85, 72)},
        {"name": "Dark gray 3 color", "hex": "#444444", "rgb": (68, 68, 68)},
        {"name": "Dark gray 2 color", "hex": "#222222", "rgb": (34, 34, 34)},
        {"name": "Dark gray 1 color", "hex": "#000000", "rgb": (0, 0, 0)}
    ],
    3: [ # Página 3: Tons de Cinza (Ordem visual na Imagem 2)
        {"name": "Medium gray 3 color", "hex": "#AAAAAA", "rgb": (170, 170, 170)},
        {"name": "Medium gray 2 color", "hex": "#888888", "rgb": (136, 136, 136)},
        {"name": "Medium gray 1 color", "hex": "#666666", "rgb": (102, 102, 102)},
        {"name": "Light gray 3 color", "hex": "#CCCCCC", "rgb": (204, 204, 204)}
    ],
}

def hex_to_rgb(hex_color):
    """Converts a HEX color string to an RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb_tuple):
    """Converts an RGB tuple to a HEX color string."""
    return '#%02x%02x%02x' % rgb_tuple

def rgb_to_hsv(r, g, b):
    """Converts an RGB color to HSV. Returns H, S, V in range [0, 1]."""
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    mx = max(r, g, b)
    mn = min(r, g, b)
    df = mx - mn
    if mx == mn:
        h = 0
    elif mx == r:
        h = (60 * ((g - b) / df) + 360) % 360
    elif mx == g:
        h = (60 * ((b - r) / df) + 120) % 360
    elif mx == b:
        h = (60 * ((r - g) / df) + 240) % 360
    
    s = 0 if mx == 0 else df / mx
    v = mx
    return h / 360.0, s, v

def get_nearest_palette_color(r, g, b):
    """
    Finds the nearest color in the Instagram palette using the "Redmean" distance formula.
    Returns (page_index, color_index, hex_value, rgb_value).
    """
    min_distance = float('inf')
    nearest_color_info = None

    for page_index, colors in INSTAGRAM_PALETTE.items():
        for color_index, palette_color in enumerate(colors):
            pr, pg, pb = palette_color["rgb"]

            # Calculate differences
            dr = r - pr
            dg = g - pg
            db = b - pb

            # Calculate Euclidean distance in RGB space
            distance_sq = dr**2 + dg**2 + db**2

            if distance_sq < min_distance:
                min_distance = distance_sq
                nearest_color_info = {
                    "page_index": page_index,
                    "color_index": color_index,
                    "hex_value": palette_color["hex"],
                    "rgb_value": palette_color["rgb"],
                    "name": palette_color["name"]
                }
    
    # Debug print for the chosen nearest color
    if nearest_color_info:
        print(f"DEBUG: Input RGB: ({r}, {g}, {b}), Nearest Palette Color: {nearest_color_info['hex_value']} (Name: {nearest_color_info['name']}, Page: {nearest_color_info['page_index']}, Index: {nearest_color_info['color_index']}), Min Distance: {math.sqrt(min_distance):.2f}")
    else:
        print(f"DEBUG: Input RGB: ({r}, {g}, {b}), No nearest color found.")
    
    return nearest_color_info
