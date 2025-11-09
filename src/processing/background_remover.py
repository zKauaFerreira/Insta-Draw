import io
from PIL import Image

try:
    import rembg
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False

def remove_background_from_image(image):
    """
    Removes the background from a PIL Image using rembg.
    Returns a PIL Image with background removed, or None if rembg is not available or fails.
    """
    if not REMBG_AVAILABLE:
        return None, "A biblioteca `rembg` não está instalada."
    if image is None:
        return None, "Nenhuma imagem fornecida para remover o fundo."

    try:
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        inp_bytes = buf.getvalue()
        out_bytes = rembg.remove(inp_bytes)
        img_no_bg = Image.open(io.BytesIO(out_bytes)).convert("RGBA")
        return img_no_bg, "Fundo removido com sucesso."
    except Exception as e:
        return None, f"Falha ao remover fundo: {e}"
