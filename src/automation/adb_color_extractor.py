import subprocess
import time
import os
from PIL import Image
import json

from .adb_utils import run_adb_command, get_screen_dump, tap_coordinates, swipe_coordinates, find_color_button_by_properties
from .adb_automation import select_color, run_adb_automation # Import select_color and run_adb_automation
from src.utils.color_utils import INSTAGRAM_PALETTE

def take_screenshot_and_pull(local_path="data/screenshot.png"):
    """
    Takes a screenshot on the device, pulls it to the host, and then deletes it from the device.
    Returns True on success, False otherwise.
    """
    device_path = "/sdcard/screenshot.png"
    # print(f"📸 Tirando screenshot no dispositivo e salvando em {device_path}...")
    if run_adb_command(f"adb shell screencap -p {device_path}") is None:
        print("🚨 Erro ao tirar screenshot.")
        return False
    
    # print(f"⬇️ Puxando screenshot para {local_path}...")
    if run_adb_command(f"adb pull {device_path} {local_path}") is None:
        print("🚨 Erro ao puxar screenshot.")
        return False
    
    # print(f"🗑️ Removendo screenshot do dispositivo...")
    if run_adb_command(f"adb shell rm {device_path}") is None:
        print("🚨 Erro ao remover screenshot do dispositivo.")
        # Continue anyway, as the screenshot is already pulled
    
    return True

def get_pixel_color_from_image(image_path, x, y):
    """
    Opens an image and returns the RGB color of the pixel at (x, y).
    """
    try:
        with Image.open(image_path) as img:
            rgb = img.getpixel((x, y))
            # Ensure it's an RGB tuple, not RGBA if alpha is present
            if isinstance(rgb) and len(rgb) == 4:
                return rgb[:3]
            return rgb
    except FileNotFoundError:
        print(f"🚨 Erro: Imagem não encontrada em {image_path}")
        return None
    except Exception as e:
        print(f"🚨 Erro ao ler pixel da imagem: {e}")
        return None

def save_extracted_colors_to_json(colors_data, file_path="data/extracted_adb_colors.json"):
    """Saves the extracted color data to a JSON file."""
    try:
        with open(file_path, "w") as f:
            json.dump(colors_data, f, indent=4)
        print(f"✅ Cores extraídas salvas em {file_path}")
    except Exception as e:
        print(f"🚨 Erro ao salvar cores extraídas em JSON: {e}")

def extract_instagram_palette_colors_via_adb():
    """
    Automates the process of extracting all colors from each page of the Instagram palette
    by taking a single screenshot per page and analyzing the color coordinates.
    """
    print("--- Iniciando extração de cores da paleta do Instagram via ADB ---")

    # 1. Setup Instagram drawing screen
    if not run_adb_automation():
        print("❌ Falha ao configurar a tela de desenho do Instagram. Abortando.")
        return

    extracted_colors = []

    for page_index in sorted(INSTAGRAM_PALETTE.keys()):
        print(f"\n--- Processando Página de Cores {page_index} ---")

        # 2. Navigate to the correct page by selecting the first color
        # This ensures we are on the right page before taking a screenshot
        select_color(page_index, 0)
        time.sleep(1)  # Wait for UI to settle

        # 3. Take a single screenshot for the entire page
        screenshot_path = f"data/palette_page_{page_index}.png"
        if not take_screenshot_and_pull(screenshot_path):
            print(f"❌ Falha ao tirar screenshot para a página {page_index}. Pulando página.")
            continue

        # 4. Get the UI layout dump for the current screen
        xml_data = get_screen_dump()
        if not xml_data:
            print(f"❌ Falha ao obter o dump da UI para a página {page_index}. Pulando página.")
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
            continue

        # 5. Iterate through each color on the current page to find its coordinates and extract its color
        for color_index, color_info in enumerate(INSTAGRAM_PALETTE[page_index]):
            target_content_desc = color_info["name"]
            
            # Find the coordinates of the color button in the UI dump
            color_coords = find_color_button_by_properties(xml_data, target_content_desc, color_index)

            if color_coords:
                # Extract the pixel color from the screenshot at the found coordinates
                pixel_rgb = get_pixel_color_from_image(screenshot_path, color_coords[0], color_coords[1])
                if pixel_rgb:
                    print(f"✅ Cor '{color_info['name']}' encontrada em {color_coords}. RGB: {pixel_rgb}")
                    extracted_colors.append({
                        "page_index": page_index,
                        "color_index": color_index,
                        "name": color_info["name"],
                        "adb_rgb": pixel_rgb,
                        "palette_rgb": color_info["rgb"]
                    })
                else:
                    print(f"❌ Falha ao extrair RGB para a cor '{color_info['name']}' da imagem.")
            else:
                print(f"❌ Não foi possível encontrar as coordenadas para a cor '{color_info['name']}' na página {page_index}.")

        # 6. Clean up the page screenshot
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)

    print("\n--- Extração de cores concluída ---")
    save_extracted_colors_to_json(extracted_colors)

if __name__ == "__main__":
    # Ensure the 'data' directory exists
    os.makedirs("data", exist_ok=True)
    extract_instagram_palette_colors_via_adb()
