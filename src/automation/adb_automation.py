import subprocess
import time

from .adb_utils import run_adb_command, get_screen_dump, find_button_coordinates, tap_coordinates, swipe_coordinates, find_color_button_by_properties
from src.utils.color_utils import INSTAGRAM_PALETTE # Import the palette

# Global state for current color selection
current_page = 1
current_color_index = 0

# Palette bounds and swipe coordinates
PALETTE_BOUNDS_X_START = 352
PALETTE_BOUNDS_X_END = 981
PALETTE_BOUNDS_Y_START = 2088
PALETTE_BOUNDS_Y_END = 2221
PALETTE_Y_CENTER = (PALETTE_BOUNDS_Y_START + PALETTE_BOUNDS_Y_END) // 2

SWIPE_NEXT_PAGE = "800 2150 400 2150 500"
SWIPE_PREV_PAGE = "400 2150 800 2150 500"

def select_color(target_page, target_index):
    global current_page, current_color_index

    if target_page == current_page and target_index == current_color_index:
        print(f"Cor já selecionada: Página {target_page}, Índice {target_index}. Pulando seleção.")
        return

    # Navigate to the target page
    while current_page != target_page:
        if target_page > current_page:
            print(f"Deslizando para a próxima página (atual: {current_page})...")
            swipe_coordinates(*map(int, SWIPE_NEXT_PAGE.split()))
            current_page += 1
        else: # target_page < current_page
            print(f"Deslizando para a página anterior (atual: {current_page})...")
            swipe_coordinates(*map(int, SWIPE_PREV_PAGE.split()))
            current_page -= 1
        time.sleep(1) # Wait 1 second after changing page

    # Get fresh screen dump to find the color button dynamically
    xml_data = get_screen_dump()
    if not xml_data:
        print("🚨 Erro: Não foi possível obter o dump da tela para selecionar a cor.")
        return

    # Get the content-desc for the target color from the palette
    color_info = INSTAGRAM_PALETTE.get(target_page, [])[target_index]
    target_content_desc = color_info["name"]

    # Find the color button using its content-desc and index
    color_coords = find_color_button_by_properties(xml_data, target_content_desc, target_index)

    if color_coords:
        tap_coordinates(color_coords[0], color_coords[1])
        time.sleep(0.5) # Wait 0.5 seconds after clicking a color
        current_color_index = target_index
        print(f"✅ Cor atualizada para Página {current_page}, Índice {current_color_index}.")
    else:
        print(f"❌ Não foi possível encontrar a cor '{target_content_desc}' (Página {target_page}, Índice {target_index}).")


def run_adb_automation():
    print("🚀 Iniciando servidor ADB...")
    run_adb_command("adb start-server")
    time.sleep(1)

    target_more_resource_id = (
        "com.instagram.android:id/row_thread_composer_button_overflow"
    )
    target_more_content_desc = "More"

    xml_data_initial = get_screen_dump()

    if xml_data_initial:
        more_coords = find_button_coordinates(
            xml_data_initial,
            resource_id=target_more_resource_id,
            content_desc=target_more_content_desc,
        )

        if more_coords:
            tap_coordinates(more_coords[0], more_coords[1])
            time.sleep(2)

            xml_data_menu_open = get_screen_dump()

            if xml_data_menu_open:
                target_draw_resource_id = "com.instagram.android:id/context_menu_item"
                target_draw_content_desc = "Draw"

                draw_coords = find_button_coordinates(
                    xml_data_menu_open,
                    resource_id=target_draw_resource_id,
                    content_desc=target_draw_content_desc,
                )

                if draw_coords:
                    tap_coordinates(draw_coords[0], draw_coords[1])
                    time.sleep(2)

                    xml_data_draw_screen = get_screen_dump()

                    if xml_data_draw_screen:
                        # --- NEW: Adjust slider first ---
                        slider_center_x = 45
                        swipe_start_y = 850
                        swipe_end_y = 1550  # This is for minimum thickness
                        swipe_duration = 500

                        swipe_coordinates(  # Adjusts slider
                            slider_center_x,
                            swipe_start_y,
                            slider_center_x,
                            swipe_end_y,
                            swipe_duration,
                        )
                        print("✅ Espessura ajustada para o mais fino.")
                        time.sleep(1)  # Give app time to register swipe

                        # --- THEN: Select Sharpie Brush ---
                        target_sharpie_content_desc = "Sharpie Brush"

                        sharpie_coords = find_button_coordinates(
                            xml_data_draw_screen,
                            content_desc=target_sharpie_content_desc,
                        )

                        if sharpie_coords:
                            tap_coordinates(sharpie_coords[0], sharpie_coords[1])
                            time.sleep(1)
                            print("✅ Pincel Sharpie selecionado.")
                            return True
                        else:
                            print("❌ Não foi possível encontrar o 'Sharpie Brush'.")
                    else:
                        print("❌ Falha ao obter dump da tela de desenho.")
                else:
                    print("❌ Não foi possível encontrar o botão 'Draw'.")
            else:
                print("❌ Falha ao obter dump da tela após clicar em 'More'.")
        else:
            print("❌ Não foi possível encontrar o botão 'More'.")
    else:
        print("❌ Falha ao obter o dump inicial da tela.")

    return False


if __name__ == "__main__":
    if run_adb_automation():
        print("\n✅ Automação ADB concluída! Iniciando automação de desenho no desktop...")
        try:
            subprocess.run(["python3", "-m", "src.automation.draw_automation"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"🚨 Erro ao executar src/automation/draw_automation.py: {e}")
        except FileNotFoundError:
            try:
                subprocess.run(["python", "src/automation/draw_automation.py"], check=True)
            except:
                print(
                    "🚨 Erro: O comando 'python3' ou 'python' não foi reconhecido para executar src/automation/draw_automation.py."
                )
    else:
        print("\n❌ Automação ADB falhou. A Automação de Desenho não será iniciada.")
