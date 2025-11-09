
import subprocess
import re

# Variável global para armazenar os IDs dos dispositivos desabilitados
disabled_devices = []

def run_command(command):
    """
    Executa um comando no shell e retorna a saída.
    """
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"🚨 Erro ao executar o comando: {e}")
        print(f"   Comando: {e.cmd}")
        print(f"   Saída: {e.stdout}")
        print(f"   Erro: {e.stderr}")
        return None

def get_mouse_devices():
    """
    Lista todos os dispositivos de entrada e filtra para encontrar mouses.
    Retorna uma lista de IDs de dispositivos de mouse.
    """
    output = run_command("xinput list")
    if output is None:
        return []
    
    devices = []
    # Regex para encontrar linhas que são "slave pointer"
    # Ex: '↳ Logitech USB Optical Mouse    id=9    [slave  pointer  (2)]'
    pointer_regex = re.compile(r".*id=(\d+)\s+\[slave\s+pointer.*")
    
    for line in output.splitlines():
        match = pointer_regex.match(line)
        if match:
            devices.append(match.group(1))
            
    return devices

def disable_mouse():
    """
    Desabilita todos os dispositivos de mouse encontrados pelo xinput.
    """
    global disabled_devices
    disabled_devices = get_mouse_devices()
    
    if not disabled_devices:
        print("⚠️ Nenhum dispositivo de mouse encontrado para desabilitar.")
        return

    print("🖱️ Desabilitando os seguintes dispositivos de mouse:")
    for device_id in disabled_devices:
        print(f"  - Desabilitando dispositivo ID: {device_id}")
        run_command(f"sudo xinput disable {device_id}")
    
    print("✅ Mouse(s) desabilitado(s). Pressione ESC para cancelar o desenho e reabilitar.")

def enable_mouse():
    """
    Reabilita os dispositivos de mouse que foram previamente desabilitados.
    """
    global disabled_devices
    if not disabled_devices:
        return

    print("🖱️ Reabilitando os seguintes dispositivos de mouse:")
    for device_id in disabled_devices:
        print(f"  - Reabilitando dispositivo ID: {device_id}")
        run_command(f"sudo xinput enable {device_id}")
    
    print("✅ Mouse(s) reabilitado(s).")
    # Limpa a lista após reabilitar
    disabled_devices = []
