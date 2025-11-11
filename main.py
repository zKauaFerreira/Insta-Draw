#!/usr/bin/env python3
# main.py — Insta-Draw (using tkinter)

import io
import json
import tkinter as tk
from tkinter import Canvas, filedialog, messagebox, ttk
import subprocess # Re-added for launching overlay
import os # Re-added for checking overlay script existence
import threading # Added for multithreading
import time

import cv2
import numpy as np
from PIL import Image, ImageTk

from src.ui.components import ScrolledFrame
from src.processing.canny_processor import process_image_for_preview
from src.processing.trace_extractor import extract_and_normalize_traces
from src.processing.background_remover import remove_background_from_image
from src.utils.history_manager import HistoryManager
from src.ui.main_ui_builder import MainUIBuilder
from src.ui.canvas_handlers import CanvasInteractionHandler
from src.utils.color_utils import get_nearest_palette_color


try:
    import rembg
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False

PREVIEW_MAX_SIZE = (800, 800)



class StrokeExtractorApp(tk.Tk):
    def __init__(self):
        print("StrokeExtractorApp: __init__ started")
        super().__init__()
        self.title("🎨 Insta-Draw - Edição Avançada")
        self.geometry("1280x720")
        self.minsize(900, 600)
        self.resizable(True, True)

        # Configure main window grid for 3 columns: left sidebar, canvas, right sidebar
        self.grid_columnconfigure(0, weight=0) # Left sidebar fixed width
        self.grid_columnconfigure(1, weight=1) # Main canvas expands
        self.grid_columnconfigure(2, weight=0) # Right sidebar fixed width
        self.grid_rowconfigure(0, weight=0) # Top bar fixed height
        self.grid_rowconfigure(1, weight=1) # Main content (sidebars/canvas) expands

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
        self.traces_only_var = tk.BooleanVar(value=True)
        self.paint_as_traces_var = tk.BooleanVar(value=False)
        self.monochromatic_var = tk.BooleanVar(value=False)
        self.selected_mono_color_info = None # To store the selected monochromatic color (page, index, hex, rgb)
        self.after_id = None # For debouncing update_preview
        self.processing_thread = None # Initialize processing thread

        self.start_time = 0
        self.elapsed_time_timer_id = None

        # New variables for more control
        self.contour_simplify_epsilon_var = tk.DoubleVar(value=0.0) # For cv2.approxPolyDP
        self.min_contour_area_var = tk.IntVar(value=10) # To filter small contours
        self.preview_line_thickness_var = tk.IntVar(value=1) # For drawing thickness in preview

        # Initialize canvas interaction handler
        self.canvas_handler = CanvasInteractionHandler(self)

        # build UI
        self.ui_builder = MainUIBuilder(self)
        self.ui_builder.build_ui()

        # bind undo/redo
        self.bind("<Control-z>", self.undo)
        self.bind("<Control-y>", self.redo)
        # Bind configure event for canvas to resize/recenter image - Moved here
        self.canvas.bind("<Configure>", self.show_image)
        print("StrokeExtractorApp: __init__ finished")

    def _update_elapsed_time(self):
        if self.start_time > 0:
            elapsed_seconds = int(time.time() - self.start_time)
            minutes, seconds = divmod(elapsed_seconds, 60)
            self.elapsed_time_label.config(text=f"Decorrido: {minutes:02d}:{seconds:02d}")
            self.elapsed_time_timer_id = self.after(1000, self._update_elapsed_time)

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

        self.update_preview() # Call directly to refresh preview
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
        print("save_traces method called!")
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
        # Determine which image to use for trace extraction and color sampling
        if self.paint_as_traces_var.get():
            # If "Paint as Traces" is active, use the display_image (which includes user edits)
            image_for_traces = self.display_image.convert("RGB")
            self.status_label.config(text="Extraindo traços da pintura...")
        else:
            # Otherwise, use the original_image
            image_for_traces = self.original_image.convert("RGB")
            self.status_label.config(text="Extraindo traços da imagem original...")

        original_img_np = np.array(image_for_traces)

        arr = np.array(image_for_traces)
        try:
            gray = cv2.cvtColor(arr, cv2.COLOR_RGBA2GRAY)
        except Exception:
            # fallback: convert RGB first
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

        # Apply contour simplification and filtering
        filtered_contours = []
        epsilon_val = self.contour_simplify_epsilon_var.get()
        min_area_val = self.min_contour_area_var.get()

        for contour in contours:
            # Filter by minimum area
            if cv2.contourArea(contour) < min_area_val:
                continue
            
            # Simplify contour if epsilon is greater than 0
            if epsilon_val > 0:
                # Calculate epsilon based on contour perimeter
                perimeter = cv2.arcLength(contour, True)
                epsilon = epsilon_val * perimeter / 100 # Epsilon as percentage of perimeter
                approx_contour = cv2.approxPolyDP(contour, epsilon, True)
                if len(approx_contour) > 1: # Ensure simplified contour has at least 2 points
                    filtered_contours.append(approx_contour)
            else:
                filtered_contours.append(contour)

        if not filtered_contours:
            messagebox.showinfo(
                "Nenhum traço",
                "Nenhum traço foi encontrado com as configurações atuais.",
            )
            return

        # Fixed path for saving traces
        path = "data/traces.json"

        all_raw_points = []
        # Use a dictionary to group traces by color
        grouped_traces_by_color = {} # Key: (page_index, color_index), Value: list of {"path": coords, "original_rgb": original_rgb}
        
        total_points = 0

        for contour in filtered_contours: # Iterate through filtered contours
            total_points += len(contour)
            # Calculate bounding box for the contour
            x, y, w, h = cv2.boundingRect(contour)
            
            # Sample color at the center of the bounding box
            center_x = x + w // 2
            center_y = y + h // 2

            # Ensure coordinates are within image bounds
            center_x = max(0, min(original_img_np.shape[1] - 1, center_x))
            center_y = max(0, min(original_img_np.shape[0] - 1, center_y))

            # Get pixel color at the center of the bounding box
            # original_img_np is already RGB (or RGBA, but we only need RGB)
            pixel_color = original_img_np[center_y, center_x][:3]
            original_rgb = (int(pixel_color[0]), int(pixel_color[1]), int(pixel_color[2])) # Ensure it's an RGB tuple


            # Find the nearest Instagram palette color
            # Apply color overrides if any
            color_overrides = {
                (75, 140, 225): {"page_index": 1, "color_index": 3, "hex_value": "#FFDC4C", "rgb_value": (255, 220, 76), "name": "Yellow"}
            }

            if original_rgb in color_overrides:
                nearest_color_info = color_overrides[original_rgb]
                print(f"DEBUG (save_traces): Color override applied for {original_rgb} -> {nearest_color_info['name']}")
            elif self.monochromatic_var.get():
                if self.selected_mono_color_info is None:
                    messagebox.showwarning("Cor Monocromática", "Selecione uma cor para o modo monocromático.")
                    return # Exit if no color is selected in monochromatic mode
                nearest_color_info = self.selected_mono_color_info
            else:
                nearest_color_info = get_nearest_palette_color(*original_rgb)
            
            print(f"DEBUG (save_traces): Contour original_rgb: {original_rgb} mapped to {nearest_color_info['name']} (Palette RGB: {nearest_color_info['rgb_value']})")

            # Do not simplify contour; use raw contour points
            # Ensure contour coordinates are integers
            coords = contour.squeeze().tolist()
            if not isinstance(coords[0], list):  # Handle single point contours
                coords = [coords]
            
            # Collect all raw points to calculate overall bounding box
            for p in coords:
                all_raw_points.append(p)
            
            # Group traces by their palette color
            color_key = (nearest_color_info["page_index"], nearest_color_info["color_index"])
            if color_key not in grouped_traces_by_color:
                grouped_traces_by_color[color_key] = {
                    "palette_color": nearest_color_info,
                    "paths": []
                }
            grouped_traces_by_color[color_key]["paths"].append(coords)
        
        if not all_raw_points:
            messagebox.showinfo(
                "Nenhum traço",
                "Nenhum traço foi encontrado com as configurações atuais.",
            )
            return

        # --- Estimated Time Calculation ---
        num_color_changes = len(grouped_traces_by_color)
        # Heuristic values: time per point and time per color change
        time_per_point = 0.005  # seconds per point
        time_per_color_change = 1.5  # seconds to change a color
        estimated_total_seconds = (total_points * time_per_point) + (num_color_changes * time_per_color_change)
        
        minutes, seconds = divmod(int(estimated_total_seconds), 60)
        self.estimated_time_label.config(text=f"Estimado: {minutes:02d}:{seconds:02d}")
        
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
        # The structure of traces_data_to_save will change to reflect grouped traces
        normalized_grouped_traces = []
        for color_key, color_group in grouped_traces_by_color.items():
            normalized_paths_for_color = []
            for trace_path in color_group["paths"]:
                normalized_path = []
                for p in trace_path:
                    normalized_path.append([p[0] - min_x, p[1] - min_y])
                normalized_paths_for_color.append(normalized_path)
            
            normalized_grouped_traces.append({
                "palette_color": color_group["palette_color"],
                "paths": normalized_paths_for_color
            })

        # Save raw, normalized traces and their bounding box dimensions
        traces_data_to_save = {
            "raw_bbox_width": raw_bbox_width,
            "raw_bbox_height": raw_bbox_height,
            "grouped_traces": normalized_grouped_traces # Changed from "traces" to "grouped_traces"
        }

        try:
            with open(path, "w") as f:
                json.dump(traces_data_to_save, f, indent=4)
            self.status_label.config(text=f"Traços brutos normalizados salvos em {path}. Overlay definido.")
            self.start_automation_button.config(state="normal") # Enable the button
        except Exception as e:
            messagebox.showerror("Erro ao salvar traços", str(e))

    def start_drawing_automation(self):
        def _run_automation():
            """Runs the automation in a thread, managing UI updates."""
            self.start_time = time.time()
            # Schedule the timer to start in the main thread
            self.after(0, self._update_elapsed_time)
            
            self.status_label.config(text="Iniciando automação ADB e de desenho...")
            self.start_automation_button.config(state="disabled")

            try:
                # Using python -m to ensure it runs as a module
                subprocess.run(["python3", "-m", "src.automation.adb_automation"], check=True, capture_output=True, text=True)
                self.status_label.config(text="Automação de desenho concluída.")
            except subprocess.CalledProcessError as e:
                error_message = "Erro na automação:\n"
                error_message += e.stderr or "Nenhuma saída de erro capturada."
                messagebox.showerror("Erro de Automação", error_message)
                self.status_label.config(text="Automação de desenho falhou.")
            except FileNotFoundError:
                messagebox.showerror("Erro", "O comando 'python3' não foi encontrado. Verifique o PATH.")
                self.status_label.config(text="Automação de desenho falhou.")
            except Exception as e:
                messagebox.showerror("Erro Inesperado", f"Ocorreu um erro inesperado: {e}")
                self.status_label.config(text="Automação de desenho falhou.")
            finally:
                # Stop the timer
                if self.elapsed_time_timer_id:
                    self.after_cancel(self.elapsed_time_timer_id)
                self.start_time = 0
                # Re-enable the button in the main thread
                self.after(0, lambda: self.start_automation_button.config(state="normal"))

        # Run the automation in a separate thread to keep the UI responsive
        threading.Thread(target=_run_automation, daemon=True).start()

    # ---------- processamento / preview ----------
    def update_preview(self, _=None):
        """
        Debounces the actual preview update to prevent excessive calls when sliders are adjusted rapidly.
        Starts image processing in a separate thread.
        """
        if self.original_image is None:
            self.status_label.config(text="Carrega uma imagem primeiro.")
            return

        if self.after_id:
            self.after_cancel(self.after_id)
        
        # Use a shorter debounce for checkboxes/sliders that trigger heavy processing
        # This ensures that rapid changes don't queue up too many threads
        debounce_time = 250 # ms

        self.after_id = self.after(debounce_time, self._start_preview_processing_thread)

    def _start_preview_processing_thread(self):
        """Starts the image processing in a separate thread."""
        if self.processing_thread and self.processing_thread.is_alive():
            # If a thread is already running, let it finish.
            # For more advanced cancellation, a threading.Event could be used.
            self.status_label.config(text="Processamento em andamento... aguarde.")
            return

        self.status_label.config(text="Processando imagem em segundo plano...")
        self.processing_thread = threading.Thread(target=self._process_image_for_preview_threaded)
        self.processing_thread.daemon = True # Allow the main program to exit even if thread is running
        self.processing_thread.start()

    def _process_image_for_preview_threaded(self):
        """
        Wrapper for _process_image_for_preview to be run in a separate thread.
        Updates the UI on the main thread after processing.
        """
        processed_image = self._process_image_for_preview()
        if processed_image:
            self.after(0, self._update_ui_with_processed_image, processed_image)
        else:
            self.after(0, lambda: self.status_label.config(text="Falha no processamento do preview."))

    def _process_image_for_preview(self):
        """
        Performs the heavy image processing for the preview.
        Returns the processed PIL Image.
        """
        if self.original_image is None:
            return None

        # --- Performance Optimization ---
        # Create a downscaled version of the image for preview processing
        preview_img = self.original_image.copy()
        preview_img.thumbnail(PREVIEW_MAX_SIZE, Image.Resampling.LANCZOS)
        
        # always work in numpy (RGBA)
        arr = np.array(preview_img)

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
            # Determine which image to use for trace extraction and color sampling for preview
            if self.paint_as_traces_var.get():
                # For "Paint as Traces", we need to use the display_image, but also downscaled
                image_for_preview_traces = self.display_image.copy()
                image_for_preview_traces.thumbnail(PREVIEW_MAX_SIZE, Image.Resampling.LANCZOS)
            else:
                image_for_preview_traces = preview_img.convert("RGB")

            contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            # Apply contour simplification and filtering for preview
            filtered_contours = []
            epsilon_val = self.contour_simplify_epsilon_var.get()
            min_area_val = self.min_contour_area_var.get()
            line_thickness = self.preview_line_thickness_var.get()

            for contour in contours:
                # Filter by minimum area
                if cv2.contourArea(contour) < min_area_val:
                    continue
                
                # Simplify contour if epsilon is greater than 0
                if epsilon_val > 0:
                    # Calculate epsilon based on contour perimeter
                    perimeter = cv2.arcLength(contour, True)
                    epsilon = epsilon_val * perimeter / 100 # Epsilon as percentage of perimeter
                    approx_contour = cv2.approxPolyDP(contour, epsilon, True)
                    if len(approx_contour) > 1: # Ensure simplified contour has at least 2 points
                        filtered_contours.append(approx_contour)
                else:
                    filtered_contours.append(contour)

            # Create a blank white image for drawing colored traces
            combined = np.full(image_for_preview_traces.size[::-1] + (4,), 255, dtype=np.uint8) # White RGBA background
            
            original_img_np = np.array(image_for_preview_traces.convert("RGB"))

            for contour in filtered_contours: # Iterate through filtered contours
                # Determine the color to draw the contour with
                if self.monochromatic_var.get() and self.selected_mono_color_info:
                    palette_rgb = self.selected_mono_color_info["rgb_value"]
                else:
                    # Calculate average color for the current contour from the chosen image
                    mask = np.zeros(original_img_np.shape[:2], dtype=np.uint8)
                    cv2.drawContours(mask, [contour], -1, 255, -1) # Draw contour on mask
                    
                    # Use the mask to get the mean color of the image within the contour
                    mean_color_bgr = cv2.mean(original_img_np, mask=mask)[:3]
                    original_rgb = (int(mean_color_bgr[2]), int(mean_color_bgr[1]), int(mean_color_bgr[0])) # Convert BGR to RGB

                    # Find the nearest Instagram palette color
                    nearest_color_info = get_nearest_palette_color(*original_rgb)
                    
                    if nearest_color_info:
                        palette_rgb = nearest_color_info["rgb_value"]
                    else:
                        palette_rgb = (0, 0, 0) # Default to black if no color info

                # OpenCV uses BGR, so convert RGB to BGR
                palette_bgr = (palette_rgb[2], palette_rgb[1], palette_rgb[0])
                cv2.drawContours(combined, [contour], -1, palette_bgr + (255,), line_thickness) # Draw with color and full opacity
            
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

        return Image.fromarray(combined)

    def _update_ui_with_processed_image(self, processed_image):
        """Updates the UI with the processed image on the main thread."""
        self.processed_image = processed_image
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
    def show_image(self, event=None):
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
        print("StrokeExtractorApp: run method called, entering mainloop...")
        self.mainloop()


if __name__ == "__main__":
    app = StrokeExtractorApp()
    app.run()