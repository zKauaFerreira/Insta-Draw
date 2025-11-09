import tkinter as tk
from tkinter import Canvas, filedialog, messagebox, ttk

from src.ui.components import ScrolledFrame

class MainUIBuilder:
    def __init__(self, app):
        self.app = app

    def build_ui(self):
        # Configure main window grid
        self.app.grid_columnconfigure(0, weight=0)  # Left sidebar fixed width
        self.app.grid_columnconfigure(1, weight=1)  # Main canvas expands
        self.app.grid_rowconfigure(0, weight=0)  # Top bar fixed height
        self.app.grid_rowconfigure(1, weight=1)  # Main content (sidebar/canvas) expands

        # TOP BAR FRAME
        self.app.top_bar_frame = tk.Frame(
            self.app, bg="#2b2b2b", height=50
        )  # Dark grey background
        self.app.top_bar_frame.grid(
            row=0, column=0, columnspan=2, sticky="ew"
        )  # Spans across both columns
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

        # Buttons in top bar (moved from controls_frame)
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

        # LEFT SCROLLABLE CONTROLS PANEL
        self.app.scrollable_controls_wrapper = ScrolledFrame(self.app, bg="#2b2b2b", width=320)
        self.app.scrollable_controls_wrapper.grid(row=1, column=0, sticky="nswe")
        # Get the inner frame where widgets should be placed
        self.app.controls_frame = self.app.scrollable_controls_wrapper._get_canvas_frame()

        # Ensure inner frame expands to prevent scrollbar issues
        self.app.controls_frame.grid_columnconfigure(0, weight=1)

        # Sliders and options (parent is now self.app.controls_frame)
        tk.Label(
            self.app.controls_frame,
            text="Traços (Canny) - intensidade",
            bg="#2b2b2b",
            fg="white",
        ).pack(pady=(12, 2), anchor="w", padx=12)
        self.app.slider_edges = tk.Scale(
            self.app.controls_frame,
            from_=50,
            to=500,
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
            self.app.controls_frame, text="Detalhes (Threshold)", bg="#2b2b2b", fg="white"
        ).pack(pady=(12, 2), anchor="w", padx=12)
        self.app.slider_threshold = tk.Scale(
            self.app.controls_frame,
            from_=0,
            to=255,
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
            self.app.controls_frame,
            text="Mistura brilho (0.5 - 2.0)",
            bg="#2b2b2b",
            fg="white",
        ).pack(pady=(8, 2), anchor="w", padx=12)
        self.app.slider_brightness = tk.Scale(
            self.app.controls_frame,
            from_=0.5,
            to=2.0,
            resolution=0.1,
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
            self.app.controls_frame, text="Suavização (Blur)", bg="#2b2b2b", fg="white"
        ).pack(pady=(8, 2), anchor="w", padx=12)
        self.app.slider_blur = tk.Scale(
            self.app.controls_frame,
            from_=0,
            to=21,
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

        tk.Label(
            self.app.controls_frame, text="Zoom / Resize (live)", bg="#2b2b2b", fg="white"
        ).pack(pady=(8, 2), anchor="w", padx=12)
        self.app.slider_scale = tk.Scale(
            self.app.controls_frame,
            from_=0.2,
            to=2.0,
            resolution=0.1,
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
            self.app.controls_frame,
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

        # tools
        tk.Label(
            self.app.controls_frame,
            text="Ferramentas",
            font=("Arial", 14),
            bg="#2b2b2b",
            fg="white",
        ).pack(pady=(10, 6))
        self.app.btn_remove_bg = tk.Button(
            self.app.controls_frame,
            text="✨ Remover Fundo (rembg)",
            command=self.app.remove_background,
            bg="#3b8ed0",
            fg="white",
            activebackground="#4a9cdb",
            activeforeground="white",
        )
        self.app.btn_remove_bg.pack(pady=6, padx=12, fill="x")
        tk.Button(
            self.app.controls_frame,
            text="🖌️ Borracha / Restaurar",
            command=self.app.toggle_eraser,
            bg="#3b8ed0",
            fg="white",
            activebackground="#4a9cdb",
            activeforeground="white",
        ).pack(pady=6, padx=12, fill="x")
        tk.Button(
            self.app.controls_frame,
            text="✂️ Cropar (arraste)",
            command=self.app.enable_crop,
            bg="#3b8ed0",
            fg="white",
            activebackground="#4a9cdb",
            activeforeground="white",
        ).pack(pady=6, padx=12, fill="x")
        tk.Button(
            self.app.controls_frame,
            text="🎨 Converter em Traços (preview)",
            command=self.app.update_preview,
            bg="#3b8ed0",
            fg="white",
            activebackground="#4a9cdb",
            activeforeground="white",
        ).pack(pady=6, padx=12, fill="x")
        # eraser size
        tk.Label(
            self.app.controls_frame, text="Tamanho Borracha (px)", bg="#2b2b2b", fg="white"
        ).pack(pady=(8, 2), anchor="w", padx=12)
        self.app.slider_eraser = tk.Scale(
            self.app.controls_frame,
            from_=4,
            to=120,
            orient="horizontal",
            variable=self.app.eraser_var,
            bg="#2b2b2b",
            fg="white",
            highlightbackground="black",
            troughcolor="#3b8ed0",
            sliderrelief="flat",
        )
        self.app.slider_eraser.pack(pady=2, padx=12, fill="x")

        # status label (remains in the app.controls_frame, but at the bottom)
        self.app.status_label = tk.Label(
            self.app.controls_frame,
            text="Nenhuma imagem carregada",
            wraplength=260,
            anchor="w",
            justify="left",
            bg="#2b2b2b",
            fg="white",
        )
        self.app.status_label.pack(pady=(12, 12), padx=12, fill="x")

        # PREVIEW PANEL (right)
        self.app.preview_frame = tk.Frame(self.app, bg="#111214")
        # Now occupies row 1, column 1 below the top bar
        self.app.preview_frame.grid(row=1, column=1, sticky="nswe")
        self.app.preview_frame.grid_rowconfigure(0, weight=1)
        self.app.preview_frame.grid_columnconfigure(0, weight=1)

        self.app.canvas = Canvas(self.app.preview_frame, bg="#111214", highlightthickness=0)
        self.app.canvas.grid(row=0, column=0, sticky="nsew")
        # default binding for painting (eraser/restore)
        self.app.canvas.bind("<ButtonPress-1>", self.app._start_paint)
        self.app.canvas.bind("<B1-Motion>", self.app._paint)
        self.app.canvas.bind("<ButtonRelease-1>", self.app._end_paint)
