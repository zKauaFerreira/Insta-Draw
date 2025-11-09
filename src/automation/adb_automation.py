import subprocess
import time

from .adb_utils import run_adb_command, get_screen_dump, find_button_coordinates, tap_coordinates, swipe_coordinates


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
