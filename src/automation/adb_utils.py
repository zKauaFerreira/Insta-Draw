import subprocess
import time
import xml.etree.ElementTree as ET
import os

def run_adb_command(command):
    """Executa um comando ADB e retorna sua saída."""
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"🚨 Erro ao executar comando ADB: {e}")
        print(f"Stderr: {e.stderr}")
        return None

def get_screen_dump():
    """Faz o dump do layout da UI da tela atual para XML e retorna o conteúdo."""
    print("📲 Fazendo dump do layout da UI da tela...")
    dump_command = "adb shell uiautomator dump /sdcard/window_dump.xml"
    run_adb_command(dump_command)
    time.sleep(1)
    pull_command = "adb pull /sdcard/window_dump.xml data/window_dump.xml"
    run_adb_command(pull_command)
    try:
        with open("data/window_dump.xml", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print("🚨 Erro: data/window_dump.xml não encontrado localmente após o pull.")
        return None

def find_button_coordinates(xml_data, resource_id=None, content_desc=None, text=None):
    """Analisa dados XML da UI para encontrar as coordenadas de um elemento."""
    if not xml_data:
        return None
    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError as e:
        print(f"🚨 Erro ao analisar XML: {e}")
        return None
    for node in root.iter("node"):
        match = True
        if resource_id is not None and node.get("resource-id") != resource_id:
            match = False
        if content_desc is not None and node.get("content-desc") != content_desc:
            match = False
        if text is not None and node.get("text") != text:
            match = False
        if match:
            bounds_str = node.get("bounds")
            if bounds_str:
                bounds_parts = bounds_str.strip("[]").split("][")
                start_x, start_y = map(int, bounds_parts[0].split(","))
                end_x, end_y = map(int, bounds_parts[1].split(","))
                center_x = (start_x + end_x) // 2
                center_y = (start_y + end_y) // 2
                print(
                    f"✅ Elemento '{content_desc or resource_id or text}' encontrado em ({center_x}, {center_y})"
                )
                return center_x, center_y
    print(f"❌ Elemento '{content_desc or resource_id or text}' não encontrado.")
    return None

def find_color_button_by_properties(xml_data, content_desc, index):
    """
    Encontra as coordenadas de um botão de cor dentro da paleta,
    usando content-desc e o atributo 'index' do nó.
    """
    if not xml_data:
        return None
    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError as e:
        print(f"🚨 Erro ao analisar XML: {e}")
        return None

    # First, find the parent palette node (doodles_colour_palette_tools)
    palette_parent_resource_id = "com.instagram.android:id/doodles_colour_palette_tools"
    palette_node = None
    for node in root.iter("node"):
        if node.get("resource-id") == palette_parent_resource_id:
            palette_node = node
            break

    if not palette_node:
        print(f"❌ Contêiner da paleta de cores '{palette_parent_resource_id}' não encontrado.")
        return None

    # Now, find the colour_palette_pager within the palette_node
    colour_palette_pager_node = None
    for node in palette_node.iter("node"):
        if node.get("resource-id") == "com.instagram.android:id/colour_palette_pager":
            colour_palette_pager_node = node
            break

    if not colour_palette_pager_node:
        print("❌ Nó 'colour_palette_pager' não encontrado dentro do contêiner da paleta.")
        return None

    # Find the specific android.view.View that contains the color buttons
    color_buttons_container = None
    for node in colour_palette_pager_node.findall("node"): # findall for direct children
        if node.get("class") == "android.view.View" and not node.get("resource-id") and not node.get("content-desc"):
            color_buttons_container = node
            break
    
    if not color_buttons_container:
        print("❌ Contêiner de botões de cor (android.view.View) não encontrado.")
        return None

    # Now, iterate through the children of the color_buttons_container to find the specific color button
    for child_node in color_buttons_container.findall("node"): # findall for direct children
        if child_node.get("content-desc") == content_desc and child_node.get("index") == str(index):
            bounds_str = child_node.get("bounds")
            if bounds_str:
                bounds_parts = bounds_str.strip("[]").split("][")
                start_x, start_y = map(int, bounds_parts[0].split(","))
                end_x, end_y = map(int, bounds_parts[1].split(","))
                center_x = (start_x + end_x) // 2
                center_y = (start_y + end_y) // 2
                print(
                    f"✅ Cor '{content_desc}' com índice '{index}' encontrada em ({center_x}, {center_y})"
                )
                return center_x, center_y

def tap_coordinates(x, y):
    """Simula um toque nas coordenadas fornecidas."""
    print(f"👆 Tocando em: ({x}, {y})")
    tap_command = f"adb shell input tap {x} {y}"
    run_adb_command(tap_command)

def swipe_coordinates(x1, y1, x2, y2, duration_ms):
    """Simula um deslize para ajustar o slider."""
    print(f"↔️ Deslizando o slider de ({x1}, {y1}) para ({x2}, {y2}) em {duration_ms}ms")
    swipe_command = f"adb shell input swipe {x1} {y1} {x2} {y2} {duration_ms}"
    run_adb_command(swipe_command)
