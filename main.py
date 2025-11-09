#!/usr/bin/env python3
# main.py — Insta-Draw (using tkinter)

import io
import json
import tkinter as tk
from tkinter import Canvas, filedialog, messagebox, ttk
import subprocess # Re-added for launching overlay
import os # Re-added for checking overlay script existence

import cv2
import numpy as np
from PIL import Image, ImageTk

from src.ui.components import ScrolledFrame
from src.processing.canny_processor import process_image_for_preview
from src.processing.trace_extractor import extract_and_normalize_traces
from src.processing.background_remover import remove_background_from_image
from src.utils.history_manager import HistoryManager

try:
    import rembg
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False


class StrokeExtractorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🎨 Insta-Draw - Edição Avançada")
        self.geometry("1280x720")
        self.minsize(900, 600)
        self.resizable(True, True)

        # images in PIL.Image (or None)
        self.original_image: Image.Image | None = None
        self.processed_image: Image.Image | None = None
        self.display_image: Image.Image | None = None

        # editing state
        self.erase_mode = False
        self.scale = 1.0  # Current effective scale (auto-adjusted + slider)
        self.last_x = None
        self.last_y = None
        self.crop_rect_id = None
        self.crop_start = None
        self.x_offset = 0  # Image offset on canvas for centering
        self.y_offset = 0

        # history for undo/redo
        self.history_manager = HistoryManager()

        # tkinter variables for sliders and checkbox
        self.edges_var = tk.DoubleVar(value=150.0)
        self.brightness_var = tk.DoubleVar(value=1.0)
        self.blur_var = tk.IntVar(value=0)
        self.scale_var = tk.DoubleVar(value=1.0)  # User's zoom factor
        self.eraser_var = tk.IntVar(value=24)
        self.threshold_var = tk.IntVar(value=100)
        self.traces_only_var = tk.BooleanVar(value=False)

        # build UI
        self._build_ui()

        # bind undo/redo
        self.bind("<Control-z>", self.undo)
        self.bind("<Control-y>", self.redo)
        # Bind configure event for canvas to resize/recenter image - Moved here
        self.canvas.bind("<Configure>", self.show_image)

from src.ui.components import ScrolledFrame
from src.processing.canny_processor import process_image_for_preview
from src.processing.trace_extractor import extract_and_normalize_traces
from src.processing.background_remover import remove_background_from_image
from src.utils.history_manager import HistoryManager
from src.ui.main_ui_builder import MainUIBuilder
from src.ui.canvas_handlers import CanvasInteractionHandler


class StrokeExtractorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🎨 Insta-Draw - Edição Avançada")
        self.geometry("1280x720")
        self.minsize(900, 600)
        self.resizable(True, True)

        # images in PIL.Image (or None)
        self.original_image: Image.Image | None = None
        self.processed_image: Image.Image | None = None
        self.display_image: Image.Image | None = None

        # editing state
        self.erase_mode = False
        self.scale = 1.0  # Current effective scale (auto-adjusted + slider)
        self.last_x = None
        self.last_y = None
        self.crop_rect_id = None
        self.crop_start = None
        self.x_offset = 0  # Image offset on canvas for centering
        self.y_offset = 0

        # history for undo/redo
        self.history_manager = HistoryManager()

        # tkinter variables for sliders and checkbox
        self.edges_var = tk.DoubleVar(value=150.0)
        self.brightness_var = tk.DoubleVar(value=1.0)
        self.blur_var = tk.IntVar(value=0)
        self.scale_var = tk.DoubleVar(value=1.0)  # User's zoom factor
        self.eraser_var = tk.IntVar(value=24)
        self.threshold_var = tk.IntVar(value=100)
        self.traces_only_var = tk.BooleanVar(value=False)

        # build UI
        self.ui_builder = MainUIBuilder(self)
        self.ui_builder.build_ui()

        # Initialize canvas interaction handler
        self.canvas_handler = CanvasInteractionHandler(self)

        # bind undo/redo
        self.bind("<Control-z>", self.undo)
        self.bind("<Control-y>", self.redo)
        # Bind configure event for canvas to resize/recenter image - Moved here
        self.canvas.bind("<Configure>", self.show_image)

    # ---------- I/O ----------
    def load_image(self):
        path = filedialog.askopenfilename(
            filetypes=[("Imagens", "*.png *.jpg *.jpeg *.bmp *.webp")]
        )
        if not path:
            return
        try:
            img = Image.open(path).convert("RGBA")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir a imagem:\n{e}")
            return

        self.original_image = img.copy()
        self.processed_image = img.copy()
        self.display_image = img.copy()
        self.scale_var.set(1.0)  # Reset zoom slider to default

        self.history_manager.clear()
        self._save_state_for_undo()

        self.show_image()  # Display the image after loading
        self.status_label.config(text=f"Imagem carregada: {path.split('/')[-1]}")

    def save_image(self):
        if self.display_image is None:
            messagebox.showwarning(
                "Nada para salvar", "Carrega e processa uma imagem primeiro."
            )
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("WEBP", "*.webp"), ("JPEG", "*.jpg")],
        )
        if not path:
            return
        try:
            self.display_image.save(path)
            self.status_label.config(text=f"Salvo em {path}")
        except Exception as e:
            messagebox.showerror("Erro ao salvar", str(e))

    def save_traces(self):
        if self.original_image is None:
            messagebox.showwarning("Nada para salvar", "Processe uma imagem primeiro.")
            return

        # --- Step 1: Launch interactive_overlay.py to define the drawing area ---
        overlay_script_name = "src/ui/interactive_overlay.py"
        overlay_coords_file = "data/drawing_area_coords.json"

        if not os.path.exists(overlay_script_name):
            messagebox.showerror(
                "Erro",
                f"O arquivo '{overlay_script_name}' não foi encontrado. "
                "Certifique-se de que ele está no diretório correto."
            )
            return

        self.status_label.config(text="Iniciando overlay para definir área de desenho...")
        self.update_idletasks()

        try:
            subprocess.run(["python3", overlay_script_name], check=True)
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Erro", f"Erro ao executar o overlay: {e}")
            return
        except FileNotFoundError:
            try:
                subprocess.run(["python", overlay_script_name], check=True)
            except:
                messagebox.showerror(
                    "Erro",
                    "O comando 'python3' ou 'python' não foi reconhecido. Verifique o PATH."
                )
                return
        
        # --- Step 2: Read the defined drawing area coordinates ---
        if not os.path.exists(overlay_coords_file):
            messagebox.showerror(
                "Erro",
                f"O arquivo '{overlay_coords_file}' não foi criado pelo overlay. "
                "A definição da área de desenho falhou."
            )
            return
        
        # We don't need to read the coords here, just ensure the file exists.
        # draw_automation.py will read it directly.

        # --- Step 3: Process image and extract traces ---
        arr = np.array(self.original_image)
        try:
            gray = cv2.cvtColor(arr, cv2.COLOR_RGBA2GRAY)
        except Exception:
            gray = cv2.cvtColor(arr[..., :3], cv2.COLOR_RGB2GRAY)

        blur_val = self.blur_var.get()
        if blur_val > 0:
            if blur_val % 2 == 0:
                blur_val += 1
            gray = cv2.GaussianBlur(gray, (blur_val, blur_val), 0)

        upper = int(self.edges_var.get())
        lower = int(self.threshold_var.get())
        edges = cv2.Canny(gray, lower, upper)

        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            messagebox.showinfo(
                "Nenhum traço",
                "Nenhum traço foi encontrado com as configurações atuais.",
            )
            return

        # Fixed path for saving traces
        path = "data/traces.json"

        all_raw_points = []
        raw_processed_traces = []

        for contour in contours:


            # Do not simplify contour; use raw contour points
            # Ensure contour coordinates are integers
            coords = contour.squeeze().tolist()
            if not isinstance(coords[0], list):  # Handle single point contours
                coords = [coords]
            
            # Collect all raw points to calculate overall bounding box
            for p in coords:
                all_raw_points.append(p)
            
            raw_processed_traces.append({"path": coords})
        
        if not all_raw_points:
            messagebox.showinfo(
                "Nenhum traço",
                "Nenhum traço foi encontrado com as configurações atuais.",
            )
            return

        # Calculate overall bounding box of all raw traces
        min_x = min(p[0] for p in all_raw_points)
        min_y = min(p[1] for p in all_raw_points)
        max_x = max(p[0] for p in all_raw_points)
        max_y = max(p[1] for p in all_raw_points)

        raw_bbox_width = max_x - min_x
        raw_bbox_height = max_y - min_y

        if raw_bbox_width == 0 or raw_bbox_height == 0:
            messagebox.showwarning(
                "Erro de Escala",
                "A caixa delimitadora dos traços é zero. Não é possível escalar."
            )
            return

        # Normalize traces to start from (0,0) relative to their bounding box
        normalized_traces = []
        for trace in raw_processed_traces:
            normalized_path = []
            for p in trace["path"]:
                normalized_path.append([p[0] - min_x, p[1] - min_y])
            normalized_traces.append({"path": normalized_path})

        # Save raw, normalized traces and their bounding box dimensions
        traces_data_to_save = {
            "raw_bbox_width": raw_bbox_width,
            "raw_bbox_height": raw_bbox_height,
            "traces": normalized_traces
        }

        try:
            with open(path, "w") as f:
                json.dump(traces_data_to_save, f, indent=4)
            self.status_label.config(text=f"Traços brutos normalizados salvos em {path}. Overlay definido.")
            self.start_automation_button.config(state="normal") # Enable the button
        except Exception as e:
            messagebox.showerror("Erro ao salvar traços", str(e))

    def start_drawing_automation(self):
        adb_script_name = "src/automation/adb_automation.py"
        if not os.path.exists(adb_script_name):
            messagebox.showerror(
                "Erro",
                f"O arquivo '{adb_script_name}' não foi encontrado. "
                "Certifique-se de que ele está no diretório correto."
            )
            return
        
        self.status_label.config(text="Iniciando automação ADB e de desenho...")
        self.update_idletasks()
        self.start_automation_button.config(state="disabled") # Disable button during automation

        try:
            # Execute adb_automation.py, which will then execute draw_automation.py
            subprocess.run(["python3", "-m", "src.automation.adb_automation"], check=True)
            self.status_label.config(text="Automação de desenho concluída (ou cancelada).")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Erro", f"Erro ao executar automação: {e}")
            self.status_label.config(text="Automação de desenho falhou.")
        except FileNotFoundError:
            try:
                subprocess.run(["python", adb_script_name], check=True)
                self.status_label.config(text="Automação de desenho concluída (ou cancelada).")
            except:
                messagebox.showerror(
                    "Erro",
                    "O comando 'python3' ou 'python' não foi reconhecido. Verifique o PATH."
                )
                self.status_label.config(text="Automação de desenho falhou.")
        finally:
            self.start_automation_button.config(state="normal") # Re-enable button after completion/failure

    # ---------- processamento / preview ----------
    def update_preview(self, _=None):
        """Gera preview convertendo imagem para traços e blendando com a imagem colorida."""
        if self.original_image is None:
            self.status_label.config(text="Carrega uma imagem primeiro.")
            return

        # always work in numpy (RGBA)
        arr = np.array(self.original_image)  # shape HxWx4
        # convert to gray (cv2 understands RGBA->GRAY with cv2.COLOR_RGBA2GRAY)
        try:
            gray = cv2.cvtColor(arr, cv2.COLOR_RGBA2GRAY)
        except Exception:
            # fallback: convert RGB first
            gray = cv2.cvtColor(arr[..., :3], cv2.COLOR_RGB2GRAY)

        blur_val = self.blur_var.get()
        if blur_val > 0:
            if blur_val % 2 == 0:  # Gaussian blur kernel size must be odd
                blur_val += 1
            gray = cv2.GaussianBlur(gray, (blur_val, blur_val), 0)

        # thresholds: lower fixed, upper adjustable
        upper = int(self.edges_var.get())
        lower = int(self.threshold_var.get())

        edges = cv2.Canny(gray, lower, upper)

        if self.traces_only_var.get():
            # black traces on a white background (for Instagram-like drawing style)
            traces = cv2.bitwise_not(edges)
            combined = cv2.cvtColor(traces, cv2.COLOR_GRAY2RGBA)
            combined[:, :, 3] = 255  # Make sure alpha is fully opaque
        else:
            # invert edges so they are white lines on a black background initially
            edges_inv = cv2.bitwise_not(edges)
            # make RGBA edge image
            edges_rgba = cv2.cvtColor(edges_inv, cv2.COLOR_GRAY2RGBA)

            brightness = float(self.brightness_var.get())
            # clamp brightness to reasonable range
            brightness = max(0.1, min(3.0, brightness))

            # blend original and edges (weights chosen for preview)
            base = arr.copy().astype(np.uint8)
            edges_rgba = edges_rgba.astype(np.uint8)

            # Weighted blend: boost base by brightness, then overlay edges
            boosted = cv2.convertScaleAbs(base[..., :3], alpha=brightness, beta=0)
            # convert boosted back to RGBA with original alpha if present
            alpha = (
                base[..., 3:4]
                if base.shape[2] == 4
                else np.full((base.shape[0], base.shape[1], 1), 255, dtype=np.uint8)
            )
            combined_rgb = cv2.addWeighted(boosted, 0.85, edges_rgba[..., :3], 0.45, 0)
            combined = np.dstack([combined_rgb, alpha])

        # set processed/display images as PIL Image
        self.processed_image = Image.fromarray(combined)
        self.display_image = self.processed_image.copy()
        self._save_state_for_undo()
        self.show_image()
        self.status_label.config(text="Preview atualizado (traços).")

    # ---------- background removal ----------
    def remove_background(self):
        if self.original_image is None:
            self.status_label.config(text="Carrega uma imagem primeiro.")
            return
        if not REMBG_AVAILABLE:
            messagebox.showerror(
                "rembg não disponível",
                "A biblioteca `rembg` não está instalada.\n"
                "Instale com: pip install rembg",
            )
            return
        try:
            self.status_label.config(text="Removendo fundo (aguarde)...")
            self.update_idletasks()  # Force UI update before a potentially long operation
            # rembg accepts bytes
            buf = io.BytesIO()
            self.original_image.save(buf, format="PNG")
            inp_bytes = buf.getvalue()
            out_bytes = rembg.remove(inp_bytes)
            img = Image.open(io.BytesIO(out_bytes)).convert("RGBA")
            self.processed_image = img.copy()
            self.display_image = img.copy()
            self.original_image = (
                img.copy()
            )  # make background-removed version the new original for further ops
            self._save_state_for_undo()
            self.show_image()
            self.status_label.config(text="Fundo removido.")
        except Exception as e:
            messagebox.showerror("Erro rembg", f"Falha ao remover fundo:\n{e}")
            self.status_label.config(text="Falha ao remover fundo.")

    # ---------- canvas display / interactions ----------
    def show_image(self, _=None):
        """Desenha a imagem atual (display_image) no canvas com a escala atual."""
        if self.display_image is None:
            return

        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        if canvas_w <= 1 or canvas_h <= 1:
            # If canvas not yet configured or too small, retry after a short delay
            self.after(20, self.show_image)
            return

        img_w, img_h = self.display_image.size
        if img_w <= 0 or img_h <= 0:
            return

        # Calculate base scale to fit image inside canvas
        scale_w = canvas_w / img_w
        scale_h = canvas_h / img_h
        base_scale = min(scale_w, scale_h)

        # Apply user zoom from slider (self.scale_var.get() is the user's multiplier)
        self.scale = base_scale * self.scale_var.get()

        new_w = max(1, int(img_w * self.scale))
        new_h = max(1, int(img_h * self.scale))

        # Calculate offsets to center the image on the canvas
        self.x_offset = (canvas_w - new_w) // 2
        self.y_offset = (canvas_h - new_h) // 2

        resized = self.display_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        self._tkimg = ImageTk.PhotoImage(resized)

        # clear canvas and draw
        self.canvas.delete("all")
        # Ensure canvas dimensions match current widget size
        self.canvas.config(width=canvas_w, height=canvas_h)
        self.canvas.create_image(
            self.x_offset, self.y_offset, anchor="nw", image=self._tkimg
        )
        # keep reference to prevent GC
        self.canvas.image = self._tkimg

    # ---------- painting (eraser/restore) ----------
    def toggle_eraser(self):
        self.erase_mode = not self.erase_mode
        self.status_label.config(
            text=f"Modo: {'Borracha' if self.erase_mode else 'Restaurar'}"
        )

    def _start_paint(self, event):
        if not self.display_image:  # Do not allow painting if no image is loaded
            return
        self.last_x = event.x
        self.last_y = event.y

    def _paint(self, event):
        if self.display_image is None or self.last_x is None or self.last_y is None:
            return

        # map canvas coords to image coords, accounting for offset and scale
        ix = int((event.x - self.x_offset) / self.scale)
        iy = int((event.y - self.y_offset) / self.scale)
        radius = self.eraser_var.get()

        # ensure we operate on RGBA numpy array
        img = np.array(self.display_image.convert("RGBA"))
        h, w = img.shape[:2]

        # Clamp drawing coordinates to image bounds
        ix = max(0, min(w - 1, ix))
        iy = max(0, min(h - 1, iy))

        # Create a mask for the circular region
        mask = np.zeros((h, w), dtype=np.uint8)
        cv2.circle(mask, (ix, iy), radius, 255, -1)

        if self.erase_mode:
            # set alpha in circular region to 0
            img[..., 3] = np.where(mask == 255, 0, img[..., 3])
        else:
            # restore: paint white opaque on RGB and alpha=255 in region
            for c in range(3):
                img[..., c] = np.where(mask == 255, 255, img[..., c])
            img[..., 3] = np.where(mask == 255, 255, img[..., 3])

        # update display_image and redraw
        self.display_image = Image.fromarray(img)
        self.show_image()
        self.last_x, self.last_y = event.x, event.y

    def _end_paint(self, _=None):
        self.last_x = None
        self.last_y = None
        self._save_state_for_undo()

    # ---------- cropping ----------
    def enable_crop(self):
        if self.display_image is None:
            self.status_label.config(text="Carrega uma imagem primeiro.")
            return
        self.status_label.config(
            text="Modo crop ativado: arraste para selecionar. Clique novamente para cancelar."
        )
        # bind crop handlers (temporarily overriding current paint bindings)
        self.canvas.unbind("<ButtonPress-1>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease-1>")
        self.canvas.bind("<ButtonPress-1>", self._crop_start)
        self.canvas.bind("<B1-Motion>", self._crop_draw)
        self.canvas.bind("<ButtonRelease-1>", self._crop_end)

    def _crop_start(self, event):
        self.crop_start = (event.x, event.y)
        if self.crop_rect_id:
            self.canvas.delete(self.crop_rect_id)
        self.crop_rect_id = self.canvas.create_rectangle(
            event.x, event.y, event.x, event.y, outline="red", width=2
        )

    def _crop_draw(self, event):
        if not self.crop_start or not self.crop_rect_id:
            return
        x0, y0 = self.crop_start
        self.canvas.coords(self.crop_rect_id, x0, y0, event.x, event.y)

    def _crop_end(self, event):
        if not self.crop_start or not self.crop_rect_id:
            self._restore_paint_bindings()  # Restore bindings even if crop failed
            return

        x0, y0 = self.crop_start
        x1, y1 = event.x, event.y
        x0, x1 = sorted((x0, x1))
        y0, y1 = sorted((y0, y1))

        # convert canvas coords to image coords using scale and offset
        ix0 = int((x0 - self.x_offset) / self.scale)
        iy0 = int((y0 - self.y_offset) / self.scale)
        ix1 = int((x1 - self.x_offset) / self.scale)
        iy1 = int((y1 - self.y_offset) / self.scale)

        # clamp to image bounds
        if self.display_image is None:
            self._restore_paint_bindings()
            return
        iw, ih = self.display_image.size
        ix0 = max(0, min(iw, ix0))
        iy0 = max(0, min(ih, iy0))
        ix1 = max(0, min(iw, ix1))
        iy1 = max(0, min(ih, iy1))

        # Check for valid crop area
        if ix1 - ix0 <= 1 or iy1 - iy0 <= 1:
            self.status_label.config(text="Seleção inválida (muito pequena).")
            # cleanup
            self.canvas.delete(self.crop_rect_id)
            self.crop_rect_id = None
            self.crop_start = None
            self._restore_paint_bindings()
            return

        # crop the PIL image (display_image is PIL)
        try:
            cropped = self.display_image.crop((ix0, iy0, ix1, iy1))
            self.display_image = cropped.copy()
            self.processed_image = cropped.copy()
            self.original_image = (
                cropped.copy()
            )  # make crop become new original for further ops
            self.scale_var.set(1.0)  # Reset zoom slider
            self.show_image()
            self._save_state_for_undo()
            self.status_label.config(text="Imagem cortada.")
        except Exception as e:
            messagebox.showerror("Erro crop", f"Falha no crop: {e}")
            self.status_label.config(text="Crop falhou.")

        # cleanup
        self.canvas.delete(self.crop_rect_id)
        self.crop_rect_id = None
        self.crop_start = None
        self._restore_paint_bindings()

    def _restore_paint_bindings(self):
        # re-bind paint handlers
        self.canvas.bind("<ButtonPress-1>", self.canvas_handler._start_paint)
        self.canvas.bind("<B1-Motion>", self.canvas_handler._paint)
        self.canvas.bind("<ButtonRelease-1>", self.canvas_handler._end_paint)
        # Clear any active selection rectangles
        if self.crop_rect_id:
            self.canvas.delete(self.crop_rect_id)
            self.crop_rect_id = None
        self.status_label.config(text="Modo: Pintura/Borracha")

    # ---------- undo/redo ----------
    def _save_state_for_undo(self):
        """Salva o estado atual da `display_image` no histórico."""
        self.history_manager.save_state(self.display_image)

    def undo(self, _=None):
        """Volta para o estado anterior no histórico."""
        restored_image = self.history_manager.undo()
        if restored_image:
            self.display_image = restored_image
            self.show_image()
            self.status_label.config(text="Ação desfeita.")
        else:
            self.status_label.config(text="Nada para desfazer.")

    def redo(self, _=None):
        """Refaz uma ação previamente desfeita."""
        restored_image = self.history_manager.redo()
        if restored_image:
            self.display_image = restored_image
            self.show_image()
            self.status_label.config(text="Ação refeita.")
        else:
            self.status_label.config(text="Nada para refazer.")

    # ---------- finish ----------
    def run(self):
        self.mainloop()


if __name__ == "__main__":
    app = StrokeExtractorApp()
    app.run()
