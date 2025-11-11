import tkinter as tk
from tkinter import Canvas, filedialog, messagebox, ttk
from src.ui.components import ScrolledFrame
from src.utils.color_utils import INSTAGRAM_PALETTE # Import the palette

class MainUIBuilder:
    def __init__(self, app):
        self.app = app
        self.color_buttons = {} # To keep track of color buttons for selection indication

    def build_ui(self):
        # TOP BAR FRAME
        self.app.top_bar_frame = tk.Frame(
            self.app, bg="#2b2b2b", height=50
        )  # Dark grey background
        self.app.top_bar_frame.grid(
            row=0, column=0, columnspan=3, sticky="ew"
        )  # Spans across all three columns
        self.app.top_bar_frame.grid_columnconfigure(
            0, weight=1
        )  # Allows title to center/spread

        # Title in top bar
        tk.Label(
            self.app.top_bar_frame,
            text="🎨 Insta-Draw Studio",
            font=("Arial", 18, "bold"),
            bg="#2b2b2b",
            fg="white",
        ).pack(side="left", padx=(18, 0), pady=6)

        # Buttons in top bar
        tk.Button(
            self.app.top_bar_frame,
            text="📁 Abrir Imagem",
            command=self.app.load_image,
            bg="#3b8ed0",
            fg="white",
            activebackground="#4a9cdb",
            activeforeground="white",
        ).pack(side="left", padx=5, pady=6)
        tk.Button(
            self.app.top_bar_frame,
            text="💾 Salvar Resultado",
            command=self.app.save_image,
            bg="#3b8ed0",
            fg="white",
            activebackground="#4a9cdb",
            activeforeground="white",
        ).pack(side="left", padx=5, pady=6)
        tk.Button(
            self.app.top_bar_frame,
            text="📈 Salvar Traços",
            command=self.app.save_traces,
            bg="#3b8ed0",
            fg="white",
            activebackground="#4a9cdb",
            activeforeground="white",
        ).pack(side="left", padx=5, pady=6)
        
        self.app.start_automation_button = tk.Button(
            self.app.top_bar_frame,
            text="▶️ Iniciar Automação de Desenho",
            command=self.app.start_drawing_automation,
            bg="#28a745", # Green color
            fg="white",
            activebackground="#218838",
            activeforeground="white",
            state="disabled" # Initially disabled
        )
        self.app.start_automation_button.pack(side="left", padx=5, pady=6)

        # Label for estimated time
        self.app.estimated_time_label = tk.Label(
            self.app.top_bar_frame,
            text="Estimado: 00:00",
            font=("Arial", 10),
            bg="#2b2b2b",
            fg="white",
        )
        self.app.estimated_time_label.pack(side="left", padx=5, pady=6)

        # Label for elapsed time
        self.app.elapsed_time_label = tk.Label(
            self.app.top_bar_frame,
            text="Decorrido: 00:00",
            font=("Arial", 10),
            bg="#2b2b2b",
            fg="white",
        )
        self.app.elapsed_time_label.pack(side="left", padx=5, pady=6)

        # LEFT SCROLLABLE CONTROLS PANEL
        self.app.left_controls_wrapper = ScrolledFrame(self.app, bg="#2b2b2b", width=320)
        self.app.left_controls_wrapper.grid(row=1, column=0, sticky="nswe")
        self.app.left_controls_frame = self.app.left_controls_wrapper._get_canvas_frame()
        self.app.left_controls_frame.grid_columnconfigure(0, weight=1)

        # Right SCROLLABLE CONTROLS PANEL
        self.app.right_controls_wrapper = ScrolledFrame(self.app, bg="#2b2b2b", width=250) # Slightly narrower
        self.app.right_controls_wrapper.grid(row=1, column=2, sticky="nswe")
        self.app.right_controls_frame = self.app.right_controls_wrapper._get_canvas_frame()
        self.app.right_controls_frame.grid_columnconfigure(0, weight=1)

        # Sliders and options (Left Sidebar)
        tk.Label(
            self.app.left_controls_frame,
            text="Traços (Canny) - intensidade",
            bg="#2b2b2b",
            fg="white",
        ).pack(pady=(12, 2), anchor="w", padx=12)
        self.app.slider_edges = tk.Scale(
            self.app.left_controls_frame,
            from_=0, # Increased range
            to=1000, # Increased range
            orient="horizontal",
            command=self.app.update_preview,
            variable=self.app.edges_var,
            bg="#2b2b2b",
            fg="white",
            highlightbackground="black",
            troughcolor="#3b8ed0",
            sliderrelief="flat",
        )
        self.app.slider_edges.pack(pady=2, padx=12, fill="x")

        tk.Label(
            self.app.left_controls_frame, text="Detalhes (Threshold)", bg="#2b2b2b", fg="white"
        ).pack(pady=(12, 2), anchor="w", padx=12)
        self.app.slider_threshold = tk.Scale(
            self.app.left_controls_frame,
            from_=0,
            to=500, # Increased range
            orient="horizontal",
            command=self.app.update_preview,
            variable=self.app.threshold_var,
            bg="#2b2b2b",
            fg="white",
            highlightbackground="black",
            troughcolor="#3b8ed0",
            sliderrelief="flat",
        )
        self.app.slider_threshold.pack(pady=2, padx=12, fill="x")

        tk.Label(
            self.app.left_controls_frame,
            text="Mistura brilho (0.1 - 5.0)", # Updated text for new range
            bg="#2b2b2b",
            fg="white",
        ).pack(pady=(8, 2), anchor="w", padx=12)
        self.app.slider_brightness = tk.Scale(
            self.app.left_controls_frame,
            from_=0.1, # Increased range
            to=5.0, # Increased range
            resolution=0.05, # Finer resolution
            orient="horizontal",
            command=self.app.update_preview,
            variable=self.app.brightness_var,
            bg="#2b2b2b",
            fg="white",
            highlightbackground="black",
            troughcolor="#3b8ed0",
            sliderrelief="flat",
        )
        self.app.slider_brightness.pack(pady=2, padx=12, fill="x")

        tk.Label(
            self.app.left_controls_frame, text="Suavização (Blur)", bg="#2b2b2b", fg="white"
        ).pack(pady=(8, 2), anchor="w", padx=12)
        self.app.slider_blur = tk.Scale(
            self.app.left_controls_frame,
            from_=0,
            to=51, # Increased range
            resolution=2, # Ensure odd kernel size for blur
            orient="horizontal",
            command=self.app.update_preview,
            variable=self.app.blur_var,
            bg="#2b2b2b",
            fg="white",
            highlightbackground="black",
            troughcolor="#3b8ed0",
            sliderrelief="flat",
        )
        self.app.slider_blur.pack(pady=2, padx=12, fill="x")

        # New sliders for contour control
        tk.Label(
            self.app.left_controls_frame, text="Simplificação Contorno (Epsilon)", bg="#2b2b2b", fg="white"
        ).pack(pady=(8, 2), anchor="w", padx=12)
        self.app.slider_epsilon = tk.Scale(
            self.app.left_controls_frame,
            from_=0.0,
            to=10.0,
            resolution=0.1,
            orient="horizontal",
            command=self.app.update_preview,
            variable=self.app.contour_simplify_epsilon_var,
            bg="#2b2b2b",
            fg="white",
            highlightbackground="black",
            troughcolor="#3b8ed0",
            sliderrelief="flat",
        )
        self.app.slider_epsilon.pack(pady=2, padx=12, fill="x")

        tk.Label(
            self.app.left_controls_frame, text="Área Mínima Contorno", bg="#2b2b2b", fg="white"
        ).pack(pady=(8, 2), anchor="w", padx=12)
        self.app.slider_min_area = tk.Scale(
            self.app.left_controls_frame,
            from_=0,
            to=500,
            orient="horizontal",
            command=self.app.update_preview,
            variable=self.app.min_contour_area_var,
            bg="#2b2b2b",
            fg="white",
            highlightbackground="black",
            troughcolor="#3b8ed0",
            sliderrelief="flat",
        )
        self.app.slider_min_area.pack(pady=2, padx=12, fill="x")

        tk.Label(
            self.app.left_controls_frame, text="Espessura Linha Preview", bg="#2b2b2b", fg="white"
        ).pack(pady=(8, 2), anchor="w", padx=12)
        self.app.slider_line_thickness = tk.Scale(
            self.app.left_controls_frame,
            from_=1,
            to=5,
            orient="horizontal",
            command=self.app.update_preview,
            variable=self.app.preview_line_thickness_var,
            bg="#2b2b2b",
            fg="white",
            highlightbackground="black",
            troughcolor="#3b8ed0",
            sliderrelief="flat",
        )
        self.app.slider_line_thickness.pack(pady=2, padx=12, fill="x")

        tk.Label(
            self.app.left_controls_frame, text="Zoom / Resize (live)", bg="#2b2b2b", fg="white"
        ).pack(pady=(8, 2), anchor="w", padx=12)
        self.app.slider_scale = tk.Scale(
            self.app.left_controls_frame,
            from_=0.1, # Increased range
            to=4.0, # Increased range
            resolution=0.05, # Finer resolution
            orient="horizontal",
            command=self.app.show_image,
            variable=self.app.scale_var,
            bg="#2b2b2b",
            fg="white",
            highlightbackground="black",
            troughcolor="#3b8ed0",
            sliderrelief="flat",
        )
        self.app.slider_scale.pack(pady=2, padx=12, fill="x")

        self.app.check_traces_only = tk.Checkbutton(
            self.app.left_controls_frame,
            text="Apenas Traços (preview)",
            command=self.app.update_preview,
            variable=self.app.traces_only_var,
            bg="#2b2b2b",
            fg="white",
            selectcolor="#3b8ed0",
            activebackground="#2b2b2b",
            activeforeground="white",
            relief="flat",
            highlightthickness=0,
        )
        self.app.check_traces_only.pack(pady=6, padx=12, fill="x")

        self.app.check_paint_as_traces = tk.Checkbutton(
            self.app.left_controls_frame,
            text="Pintar como Traços",
            command=self.app.update_preview, # Re-render preview when this changes
            variable=self.app.paint_as_traces_var,
            bg="#2b2b2b",
            fg="white",
            selectcolor="#3b8ed0",
            activebackground="#2b2b2b",
            activeforeground="white",
            relief="flat",
            highlightthickness=0,
        )
        self.app.check_paint_as_traces.pack(pady=6, padx=12, fill="x")

        # Monochromatic Mode Checkbox
        self.app.check_monochromatic = tk.Checkbutton(
            self.app.left_controls_frame,
            text="Modo Monocromático",
            command=self._toggle_monochromatic_mode,
            variable=self.app.monochromatic_var,
            bg="#2b2b2b",
            fg="white",
            selectcolor="#3b8ed0",
            activebackground="#2b2b2b",
            activeforeground="white",
            relief="flat",
            highlightthickness=0,
        )
        self.app.check_monochromatic.pack(pady=6, padx=12, fill="x")

        # Monochromatic Color Selector Frame
        self.monochromatic_color_frame = tk.Frame(self.app.left_controls_frame, bg="#2b2b2b")
        self.monochromatic_color_frame.pack(pady=5, padx=12, fill="x")
        
        tk.Label(self.monochromatic_color_frame, text="Selecionar Cor Monocromática:", bg="#2b2b2b", fg="white").pack(anchor="w")

        # Create color buttons for each palette color
        for page_index, colors in INSTAGRAM_PALETTE.items():
            page_frame = tk.Frame(self.monochromatic_color_frame, bg="#2b2b2b")
            page_frame.pack(fill="x", pady=2)
            tk.Label(page_frame, text=f"Página {page_index}:", bg="#2b2b2b", fg="white").pack(side="left")
            
            for color_index, color_info in enumerate(colors):
                hex_color = color_info["hex"]
                btn = tk.Button(
                    page_frame,
                    bg=hex_color,
                    activebackground=hex_color,
                    width=2,
                    height=1,
                    relief="raised",
                    command=lambda pi=page_index, ci=color_index, h=hex_color, r=color_info["rgb"]: self._select_mono_color(pi, ci, h, r)
                )
                btn.pack(side="left", padx=2, pady=2)
                self.color_buttons[(page_index, color_index)] = btn
        
        # Initially hide the color selector frame
        self.monochromatic_color_frame.pack_forget()

        # Tools (Right Sidebar)
        tk.Label(
            self.app.right_controls_frame,
            text="Ferramentas",
            font=("Arial", 14),
            bg="#2b2b2b",
            fg="white",
        ).pack(pady=(10, 6))
        self.app.btn_remove_bg = tk.Button(
            self.app.right_controls_frame,
            text="✨ Remover Fundo (rembg)",
            command=self.app.remove_background,
            bg="#3b8ed0",
            fg="white",
            activebackground="#4a9cdb",
            activeforeground="white",
        )
        self.app.btn_remove_bg.pack(pady=6, padx=12, fill="x")
        tk.Button(
            self.app.right_controls_frame,
            text="🖌️ Borracha / Restaurar",
            command=self.app.toggle_eraser,
            bg="#3b8ed0",
            fg="white",
            activebackground="#4a9cdb",
            activeforeground="white",
        ).pack(pady=6, padx=12, fill="x")
        tk.Button(
            self.app.right_controls_frame,
            text="✂️ Cropar (arraste)",
            command=self.app.enable_crop,
            bg="#3b8ed0",
            fg="white",
            activebackground="#4a9cdb",
            activeforeground="white",
        ).pack(pady=6, padx=12, fill="x")
        tk.Button(
            self.app.right_controls_frame,
            text="🎨 Converter em Traços (preview)",
            command=self.app.update_preview,
            bg="#3b8ed0",
            fg="white",
            activebackground="#4a9cdb",
            activeforeground="white",
        ).pack(pady=6, padx=12, fill="x")
        # eraser size
        tk.Label(
            self.app.right_controls_frame, text="Tamanho Borracha (px)", bg="#2b2b2b", fg="white"
        ).pack(pady=(8, 2), anchor="w", padx=12)
        self.app.slider_eraser = tk.Scale(
            self.app.right_controls_frame,
            from_=1, # Increased range
            to=200, # Increased range
            orient="horizontal",
            variable=self.app.eraser_var,
            bg="#2b2b2b",
            fg="white",
            highlightbackground="black",
            troughcolor="#3b8ed0",
            sliderrelief="flat",
        )
        self.app.slider_eraser.pack(pady=2, padx=12, fill="x")

        # status label (remains in the app.left_controls_frame, but at the bottom)
        self.app.status_label = tk.Label(
            self.app.left_controls_frame, # Moved to left sidebar
            text="Nenhuma imagem carregada",
            wraplength=260,
            anchor="w",
            justify="left",
            bg="#2b2b2b",
            fg="white",
        )
        self.app.status_label.pack(pady=(12, 12), padx=12, fill="x")

        # PREVIEW PANEL (center)
        self.app.preview_frame = tk.Frame(self.app, bg="#111214")
        self.app.preview_frame.grid(row=1, column=1, sticky="nswe") # Placed in center column
        self.app.preview_frame.grid_rowconfigure(0, weight=1)
        self.app.preview_frame.grid_columnconfigure(0, weight=1)

        self.app.canvas = Canvas(self.app.preview_frame, bg="#111214", highlightthickness=0)
        self.app.canvas.grid(row=0, column=0, sticky="nsew")
        # default binding for painting (eraser/restore)
        self.app.canvas.bind("<ButtonPress-1>", self.app.canvas_handler._start_paint)
        self.app.canvas.bind("<B1-Motion>", self.app.canvas_handler._paint)
        self.app.canvas.bind("<ButtonRelease-1>", self.app.canvas_handler._end_paint)
    
    def _toggle_monochromatic_mode(self):
        if self.app.monochromatic_var.get():
            self.monochromatic_color_frame.pack(pady=5, padx=12, fill="x")
            # Select the first color by default if none is selected
            if self.app.selected_mono_color_info is None:
                first_page = min(INSTAGRAM_PALETTE.keys())
                first_color_info = INSTAGRAM_PALETTE[first_page][0]
                self._select_mono_color(first_page, 0, first_color_info["hex"], first_color_info["rgb"])
        else:
            self.monochromatic_color_frame.pack_forget()
            self.app.selected_mono_color_info = None # Clear selection when mode is off
            self._clear_color_selection_highlight()
        self.app.update_preview()

    def _select_mono_color(self, page_index, color_index, hex_value, rgb_value):
        # Clear previous highlight
        self._clear_color_selection_highlight()

        # Highlight new selection
        selected_btn = self.color_buttons.get((page_index, color_index))
        if selected_btn:
            selected_btn.config(relief="sunken", borderwidth=3)
        
        self.app.selected_mono_color_info = {
            "page_index": page_index,
            "color_index": color_index,
            "hex_value": hex_value,
            "rgb_value": rgb_value
        }
        self.app.update_preview()
        self.app.status_label.config(text=f"Cor monocromática selecionada: {hex_value}")

    def _clear_color_selection_highlight(self):
        for (page_idx, color_idx), btn in self.color_buttons.items():
            btn.config(relief="raised", borderwidth=1)
