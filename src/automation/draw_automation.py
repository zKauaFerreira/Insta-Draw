import time

from pynput import keyboard

from src.utils.curve_utils import catmull_rom_spline
from src.utils.file_loader import load_drawing_area_coords, load_traces_data
from src.utils.mouse_utils import disable_mouse, enable_mouse

try:
    import pyautogui

    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    print("🚨 ERRO: A biblioteca 'pyautogui' não está instalada.")
    print("Por favor, instale-a com: pip install pyautogui")
    print("A automação de desenho no desktop não funcionará sem ela.")

try:
    from pynput import keyboard

    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    print("🚨 AVISO: A biblioteca 'pynput' não está instalada.")
    print(
        "Para habilitar o cancelamento com a tecla ESC, instale-a com: pip install pynput"
    )
    print(
        "Em sistemas Linux, pode ser necessário instalar dependências adicionais (ex: sudo apt-get install python3-tk python3-dev)."
    )
    print(
        "Além disso, em Linux, pode ser necessário executar o script com 'sudo' ou configurar permissões para o listener de teclado."
    )


# PyAutoGUI settings
if PYAUTOGUI_AVAILABLE:
    pyautogui.FAILSAFE = False  # Disable the failsafe to prevent accidental mouse movements from stopping the script
    # pyautogui.PAUSE will be set dynamically based on DRAWING_SPEED

# Global flag for cancellation
cancel_drawing = False


def on_press(key):
    global cancel_drawing
    if key == keyboard.Key.esc:
        print("\n🚨 Tecla ESC pressionada. Tentando cancelar o desenho...")
        cancel_drawing = True
        return False  # Stop listener


# --- Configuration for Drawing Speed ---
DRAWING_SPEED = {
    "slow": {"pause": 0.01, "duration": 0.15},
    "medium": {"pause": 0.005, "duration": 0.075},
    "fast": {"pause": 0.002, "duration": 0.02},
    "very_fast": {"pause": 0.001, "duration": 0.01},
}
# Default speed setting
CURRENT_SPEED = "medium"  # Changed default speed to medium for better app stability


def draw_strokes_with_pyautogui(
    traces_data,
    drawing_area_coords,
    speed_level=CURRENT_SPEED,
    strokes_per_chunk=50,
    chunk_break_time=3,
):
    """
    Desenha os traços na tela do desktop usando pyautogui, escalando-os para a área definida,
    mantendo a proporção e centralizando.

    Args:
        traces_data (dict): Dicionário com 'raw_bbox_width', 'raw_bbox_height' e 'traces'.
        drawing_area_coords (dict): Dicionário com x, y, width, height da área de desenho no desktop.
        speed_level (str): Nível de velocidade do desenho ('slow', 'medium', 'fast', 'very_fast').
        strokes_per_chunk (int): Número de traços a desenhar antes de uma pausa longa.
        chunk_break_time (int): Duração da pausa em segundos entre os chunks de traços.
    """
    if not PYAUTOGUI_AVAILABLE:
        print("PyAutoGUI não está disponível. Não é possível desenhar.")
        return

    raw_bbox_width = traces_data["raw_bbox_width"]
    raw_bbox_height = traces_data["raw_bbox_height"]
    traces = traces_data["traces"]

    if not traces:
        print("Nenhum traço para desenhar.")
        return

    if not drawing_area_coords:
        print("Coordenadas da área de desenho não definidas.")
        return

    # Desktop coordinates of the overlay area
    overlay_x = drawing_area_coords["x"]
    overlay_y = drawing_area_coords["y"]
    overlay_width = drawing_area_coords["width"]
    overlay_height = drawing_area_coords["height"]

    print(f"\n-------------------------------------------------")
    print(f"🖌️ INICIANDO AUTOMAÇÃO DE DESENHO NO DESKTOP:")
    print(
        f"  Área de desenho no desktop: X={overlay_x}, Y={overlay_y}, W={overlay_width}, H={overlay_height}"
    )
    print(f"  Tamanho original dos traços: {raw_bbox_width}x{raw_bbox_height}")
    print(f"  Número total de traços: {len(traces)}")
    print(f"  Velocidade de desenho: {speed_level}")
    print(
        f"  Pausas a cada {strokes_per_chunk} traços por {chunk_break_time} segundos."
    )
    print(f"-------------------------------------------------")

    # --- Scaling Logic: Maintain aspect ratio and center ---
    # Calculate scale factor to fit the raw traces into the overlay area
    scale_factor_x = overlay_width / raw_bbox_width
    scale_factor_y = overlay_height / raw_bbox_height

    # Use the minimum scale factor to maintain aspect ratio and fit within the target area
    final_scale = min(scale_factor_x, scale_factor_y)

    # Calculate dimensions of the drawing after scaling
    scaled_drawing_width = raw_bbox_width * final_scale
    scaled_drawing_height = raw_bbox_height * final_scale

    # Calculate offsets for centering the scaled drawing within the target area
    center_offset_x = (overlay_width - scaled_drawing_width) / 2
    center_offset_y = (overlay_height - scaled_drawing_height) / 2

    print(f"  Fatores de escala (X, Y): {scale_factor_x:.2f}, {scale_factor_y:.2f}")
    print(f"  Escala final (mantendo proporção): {final_scale:.2f}")
    print(
        f"  Tamanho do desenho escalado: {scaled_drawing_width:.0f}x{scaled_drawing_height:.0f}"
    )
    print(
        f"  Offsets de centralização: X={center_offset_x:.0f}, Y={center_offset_y:.0f}"
    )

    # Set pyautogui pause based on chosen speed
    pyautogui.PAUSE = DRAWING_SPEED[speed_level]["pause"]
    move_duration = DRAWING_SPEED[speed_level]["duration"]

    # IMPORTANT: User must ensure the mirrored Android screen is active and correctly positioned
    print(
        "\nATENÇÃO: Certifique-se de que a tela espelhada do Android esteja ATIVA e POSICIONADA"
    )
    print(
        f"corretamente na área definida ({overlay_x},{overlay_y}) - ({overlay_x + overlay_width},{overlay_y + overlay_height})"
    )
    print("O desenho começará IMEDIATAMENTE. Não mova o mouse durante o processo.")
    print("Pressione ESC no terminal para parar o script a qualquer momento.")
    time.sleep(2)  # Give a short moment for the user to read the warning

    disable_mouse()  # Desabilita o mouse antes de começar a desenhar
    try:
        strokes_drawn_in_chunk = 0
        for i, trace in enumerate(traces):
            if cancel_drawing:
                print("Desenho cancelado pelo usuário.")
                break

            # Introduce a break after a certain number of strokes
            if strokes_per_chunk > 0 and strokes_drawn_in_chunk >= strokes_per_chunk:
                pyautogui.mouseUp()  # Ensure mouse is up before the break
                print(
                    f"Pausa de {chunk_break_time} segundos para estabilização do aplicativo..."
                )
                time.sleep(chunk_break_time)
                strokes_drawn_in_chunk = 0  # Reset counter
                if cancel_drawing:  # Check cancellation again after long break
                    print("Desenho cancelado pelo usuário durante a pausa.")
                    break

            # Ensure mouse button is up before starting a new trace
            pyautogui.mouseUp()
            time.sleep(pyautogui.PAUSE * 2)  # Give a moment for mouseUp to register

            path = trace["path"]
            if not path:
                continue

            # Handle isolated points
            if len(path) == 1:
                p_norm_x, p_norm_y = path[0]
                desktop_x = int(overlay_x + center_offset_x + (p_norm_x * final_scale))
                desktop_y = int(overlay_y + center_offset_y + (p_norm_y * final_scale))
                pyautogui.moveTo(desktop_x, desktop_y, duration=move_duration)
                pyautogui.click()  # Simulate a small dot
                time.sleep(0.05)  # Small delay after a click
                strokes_drawn_in_chunk += 1
                continue

            # Apply Catmull-Rom spline interpolation for smoother curves
            # Generate more points for smoother drawing
            interpolated_path = catmull_rom_spline(
                path, num_segments=5
            )  # num_segments reduced to 5 for lower event load

            # Map the first point to desktop coordinates
            first_point_norm_x, first_point_norm_y = interpolated_path[0]
            desktop_x = int(
                overlay_x + center_offset_x + (first_point_norm_x * final_scale)
            )
            desktop_y = int(
                overlay_y + center_offset_y + (first_point_norm_y * final_scale)
            )

            # Move to the first point and press down the mouse button
            pyautogui.moveTo(desktop_x, desktop_y, duration=move_duration)
            pyautogui.mouseDown()

            # Drag to all subsequent points
            for j in range(1, len(interpolated_path)):
                if cancel_drawing:
                    break  # Break from inner loop if cancelled
                current_point_norm_x, current_point_norm_y = interpolated_path[j]
                desktop_x = int(
                    overlay_x + center_offset_x + (current_point_norm_x * final_scale)
                )
                desktop_y = int(
                    overlay_y + center_offset_y + (current_point_norm_y * final_scale)
                )

                # Use dragTo to simulate continuous drawing while mouse button is down
                pyautogui.dragTo(
                    desktop_x, desktop_y, duration=move_duration
                )  # duration changed to move_duration

            pyautogui.mouseUp()
            time.sleep(
                0.1
            )  # Small pause between traces to allow application to register (increased from 0.05)
            strokes_drawn_in_chunk += 1  # Increment after successful stroke
    finally:
        enable_mouse()  # Garante que o mouse seja reabilitado no final

    if not cancel_drawing:
        print("Desenho concluído!")
    else:
        print("Desenho interrompido pelo usuário.")
    print(f"-------------------------------------------------\n")





if __name__ == "__main__":
    if not PYAUTOGUI_AVAILABLE:
        exit()

    traces_file = "data/traces.json"
    drawing_area_coords_file = "data/drawing_area_coords.json"

    drawing_area = load_drawing_area_coords(drawing_area_coords_file)
    traces_data = load_traces_data(traces_file)

    if drawing_area and traces_data:
        # Start keyboard listener for ESC key
        listener = None
        if PYNPUT_AVAILABLE:
            listener = keyboard.Listener(on_press=on_press)
            listener.start()
            print("Pressione ESC a qualquer momento para cancelar o desenho.")
        else:
            print(
                "Aviso: 'pynput' não está instalado. Não será possível cancelar com ESC."
            )

        try:
            # You can change the speed_level here: 'slow', 'medium', 'fast', 'very_fast'
            # 'medium' is a good balance for most applications. If drawings are still
            # incomplete or "cancelled", try 'slow'.
            # You can also adjust strokes_per_chunk and chunk_break_time here for stability
            draw_strokes_with_pyautogui(
                traces_data,
                drawing_area,
                speed_level="medium",
                strokes_per_chunk=70,
                chunk_break_time=3,
            )
        finally:
            if listener:
                listener.stop()
                listener.join()  # Ensure the listener thread is properly shut down
            enable_mouse()  # Certifique-se de que o mouse seja reativado
    else:
        print(
            "Não foi possível carregar os dados necessários para o desenho no desktop."
        )
