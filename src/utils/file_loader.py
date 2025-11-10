import json
import os

def load_drawing_area_coords(file_path="data/drawing_area_coords.json"):
    """Carrega as coordenadas da área de desenho do arquivo JSON."""
    if not os.path.exists(file_path):
        print(
            f"🚨 Erro: Arquivo de coordenadas da área de desenho não encontrado: {file_path}"
        )
        return None
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"🚨 Erro ao decodificar JSON em {file_path}: {e}")
        return None
    except Exception as e:
        print(f"🚨 Erro ao ler {file_path}: {e}")
        return None


def load_traces_data(file_path="data/traces.json"):
    """
    Carrega os dados dos traços do arquivo JSON.
    Espera um dicionário com 'raw_bbox_width', 'raw_bbox_height' e 'grouped_traces'.
    """
    if not os.path.exists(file_path):
        print(f"🚨 Erro: Arquivo de traços não encontrado: {file_path}")
        print("Por favor, execute 'main.py' e salve os traços primeiro.")
        return None
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            if (
                not isinstance(data, dict)
                or "raw_bbox_width" not in data
                or "grouped_traces" not in data
            ):
                print(f"🚨 Erro: Formato de arquivo de traços inválido em {file_path}.")
                print(
                    "Esperado um dicionário com 'raw_bbox_width', 'raw_bbox_height' e 'grouped_traces'."
                )
                return None
            return data
    except json.JSONDecodeError as e:
        print(f"🚨 Erro ao decodificar JSON em {file_path}: {e}")
        return None
    except Exception as e:
        print(f"🚨 Erro ao ler {file_path}: {e}")
        return None
