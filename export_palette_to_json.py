import json
from src.utils.color_utils import INSTAGRAM_PALETTE
import os

def export_instagram_palette_to_json(file_path="data/instagram_palette.json"):
    """
    Exports the INSTAGRAM_PALETTE to a JSON file.
    """
    export_data = []
    for page_index, colors in INSTAGRAM_PALETTE.items():
        for color_index, color_info in enumerate(colors):
            export_data.append({
                "page_index": page_index,
                "color_index": color_index,
                "name": color_info["name"],
                "hex": color_info["hex"],
                "rgb": color_info["rgb"]
            })
    
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as f:
            json.dump(export_data, f, indent=4)
        print(f"✅ Instagram palette exported to {file_path}")
    except Exception as e:
        print(f"🚨 Erro ao exportar paleta para JSON: {e}")

if __name__ == "__main__":
    export_instagram_palette_to_json()
