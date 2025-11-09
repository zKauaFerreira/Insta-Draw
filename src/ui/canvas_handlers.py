import tkinter as tk
from tkinter import messagebox
import cv2
import numpy as np
from PIL import Image

class CanvasInteractionHandler:
    def __init__(self, app):
        self.app = app

    def toggle_eraser(self):
        self.app.erase_mode = not self.app.erase_mode
        self.app.status_label.config(
            text=f"Modo: {'Borracha' if self.app.erase_mode else 'Restaurar'}"
        )

    def _start_paint(self, event):
        if not self.app.display_image:  # Do not allow painting if no image is loaded
            return
        self.app.last_x = event.x
        self.app.last_y = event.y

    def _paint(self, event):
        if self.app.display_image is None or self.app.last_x is None or self.app.last_y is None:
            return

        # map canvas coords to image coords, accounting for offset and scale
        ix = int((event.x - self.app.x_offset) / self.app.scale)
        iy = int((event.y - self.app.y_offset) / self.app.scale)
        radius = self.app.eraser_var.get()

        # ensure we operate on RGBA numpy array
        img = np.array(self.app.display_image.convert("RGBA"))
        h, w = img.shape[:2]

        # Clamp drawing coordinates to image bounds
        ix = max(0, min(w - 1, ix))
        iy = max(0, min(h - 1, iy))

        # Create a mask for the circular region
        mask = np.zeros((h, w), dtype=np.uint8)
        cv2.circle(mask, (ix, iy), radius, 255, -1)

        if self.app.erase_mode:
            # set alpha in circular region to 0
            img[..., 3] = np.where(mask == 255, 0, img[..., 3])
        else:
            # restore: paint white opaque on RGB and alpha=255 in region
            for c in range(3):
                img[..., c] = np.where(mask == 255, 255, img[..., c])
            img[..., 3] = np.where(mask == 255, 255, img[..., 3])

        # update display_image and redraw
        self.app.display_image = Image.fromarray(img)
        self.app.show_image()
        self.app.last_x, self.app.last_y = event.x, event.y

    def _end_paint(self, _=None):
        self.app.last_x = None
        self.app.last_y = None
        self.app._save_state_for_undo()

    def enable_crop(self):
        if self.app.display_image is None:
            self.app.status_label.config(text="Carrega uma imagem primeiro.")
            return
        self.app.status_label.config(
            text="Modo crop ativado: arraste para selecionar. Clique novamente para cancelar."
        )
        # bind crop handlers (temporarily overriding current paint bindings)
        self.app.canvas.unbind("<ButtonPress-1>")
        self.app.canvas.unbind("<B1-Motion>")
        self.app.canvas.unbind("<ButtonRelease-1>")
        self.app.canvas.bind("<ButtonPress-1>", self._crop_start)
        self.app.canvas.bind("<B1-Motion>", self._crop_draw)
        self.app.canvas.bind("<ButtonRelease-1>", self._crop_end)

    def _crop_start(self, event):
        self.app.crop_start = (event.x, event.y)
        if self.app.crop_rect_id:
            self.app.canvas.delete(self.app.crop_rect_id)
        self.app.crop_rect_id = self.app.canvas.create_rectangle(
            event.x, event.y, event.x, event.y, outline="red", width=2
        )

    def _crop_draw(self, event):
        if not self.app.crop_start or not self.app.crop_rect_id:
            return
        x0, y0 = self.app.crop_start
        self.app.canvas.coords(self.app.crop_rect_id, x0, y0, event.x, event.y)

    def _crop_end(self, event):
        if not self.app.crop_start or not self.app.crop_rect_id:
            self._restore_paint_bindings()  # Restore bindings even if crop failed
            return

        x0, y0 = self.app.crop_start
        x1, y1 = event.x, event.y
        x0, x1 = sorted((x0, x1))
        y0, y1 = sorted((y0, y1))

        # convert canvas coords to image coords using scale and offset
        ix0 = int((x0 - self.app.x_offset) / self.app.scale)
        iy0 = int((y0 - self.app.y_offset) / self.app.scale)
        ix1 = int((x1 - self.app.x_offset) / self.app.scale)
        iy1 = int((y1 - self.app.y_offset) / self.app.scale)

        # clamp to image bounds
        if self.app.display_image is None:
            self._restore_paint_bindings()
            return
        iw, ih = self.app.display_image.size
        ix0 = max(0, min(iw, ix0))
        iy0 = max(0, min(ih, iy0))
        ix1 = max(0, min(iw, ix1))
        iy1 = max(0, min(ih, iy1))

        # Check for valid crop area
        if ix1 - ix0 <= 1 or iy1 - iy0 <= 1:
            self.app.status_label.config(text="Seleção inválida (muito pequena).")
            # cleanup
            self.app.canvas.delete(self.app.crop_rect_id)
            self.app.crop_rect_id = None
            self.app.crop_start = None
            self._restore_paint_bindings()
            return

        # crop the PIL image (display_image is PIL)
        try:
            cropped = self.app.display_image.crop((ix0, iy0, ix1, iy1))
            self.app.display_image = cropped.copy()
            self.app.processed_image = cropped.copy()
            self.app.original_image = (
                cropped.copy()
            )  # make crop become new original for further ops
            self.app.scale_var.set(1.0)  # Reset zoom slider
            self.app.show_image()
            self.app._save_state_for_undo()
            self.app.status_label.config(text="Imagem cortada.")
        except Exception as e:
            messagebox.showerror("Erro crop", f"Falha no crop: {e}")
            self.app.status_label.config(text="Crop falhou.")

        # cleanup
        self.app.canvas.delete(self.app.crop_rect_id)
        self.app.crop_rect_id = None
        self.app.crop_start = None
        self._restore_paint_bindings()

    def _restore_paint_bindings(self):
        # re-bind paint handlers
        self.app.canvas.bind("<ButtonPress-1>", self._start_paint)
        self.app.canvas.bind("<B1-Motion>", self._paint)
        self.app.canvas.bind("<ButtonRelease-1>", self._end_paint)
        # Clear any active selection rectangles
        if self.app.crop_rect_id:
            self.app.canvas.delete(self.app.crop_rect_id)
            self.app.crop_rect_id = None
        self.app.status_label.config(text="Modo: Pintura/Borracha")
