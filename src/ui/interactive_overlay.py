import json
import os
import tkinter as tk


class InteractiveOverlay(tk.Tk):
    """
    Cria um overlay interativo na área de trabalho para definir uma área de desenho.
    Permite movimento e redimensionamento via handles nos cantos.
    """

    def __init__(self):
        super().__init__()

        self.title("Android Drawing Area Overlay")
        self._current_x = 100
        self._current_y = 100
        self._current_width = 300
        self._current_height = 300

        # Configurações para transparência e remoção de bordas
        self.configure(bg="white")
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.7)
        self.overrideredirect(True)
        self.resizable(False, False)

        # Cores e espessura das bordas
        self.BORDER_COLOR = "#0000FF"
        self.BORDER_WIDTH = 4
        self.HANDLE_SIZE = 12
        self.MIN_SIZE = 50  # Tamanho mínimo para a área

        # Variáveis para armazenar as coordenadas e estado de arraste
        self._drag_data = {"x": 0, "y": 0, "state": None}

        # Canvas para desenhar o overlay
        self.canvas = tk.Canvas(
            self,
            highlightthickness=0,
            bg="white",
            width=self._current_width,
            height=self._current_height,
        )
        self.canvas.pack(fill="both", expand=True)

        # Liga eventos para mover o quadrado inteiro
        self.canvas.bind("<ButtonPress-1>", self._on_press_move)
        self.canvas.bind("<B1-Motion>", self._on_drag_move)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

        # Armazenar e salvar coordenadas
        self.coords_file = "data/drawing_area_coords.json"
        self._load_saved_coords()

        # Botão de confirmação
        self.confirm_button = tk.Button(
            self,
            text="Confirmar Área",
            command=self._confirm_and_close,
            bg="#32CD32",
            fg="white",
            font=("Arial", 10, "bold"),
        )

        # Cria os "handles" nos cantos para redimensionamento
        self.handles = {}
        self._create_handles()

        # Aplica as coordenadas carregadas e desenha tudo
        self._update_geometry()

    def _draw_overlay(self):
        """Desenha o overlay com bordas visíveis e centro transparente."""
        self.canvas.delete("overlay_rect")
        self.canvas.create_rectangle(
            0,
            0,
            self._current_width,
            self._current_height,
            outline=self.BORDER_COLOR,
            width=self.BORDER_WIDTH,
            fill="",
            tags="overlay_rect",
        )
        self.confirm_button.place(relx=0.5, rely=0.5, anchor="center")
        self.canvas.tag_raise("all")

    def _create_handles(self):
        """Cria e posiciona os handles de redimensionamento nos cantos."""
        handle_configs = {
            "nw": {"cursor": "top_left_corner"},
            "ne": {"cursor": "top_right_corner"},
            "sw": {"cursor": "bottom_left_corner"},
            "se": {"cursor": "bottom_right_corner"},
        }

        for corner, config in handle_configs.items():
            handle = self.canvas.create_rectangle(
                0,
                0,
                0,
                0,
                fill=self.BORDER_COLOR,
                outline="white",
                width=1,
                tags=f"handle_{corner}",
            )
            self.canvas.tag_bind(
                f"handle_{corner}",
                "<ButtonPress-1>",
                lambda event, c=corner: self._on_press_resize(event, c),
            )
            self.canvas.tag_bind(
                f"handle_{corner}",
                "<B1-Motion>",
                lambda event, c=corner: self._on_drag_resize(event, c),
            )
            self.canvas.tag_bind(
                f"handle_{corner}", "<ButtonRelease-1>", self._on_release
            )
            self.handles[corner] = handle

        self._update_handles()

    def _update_handles(self):
        """Atualiza a posição dos handles."""
        handle_positions = {
            "nw": (0, 0),
            "ne": (self._current_width, 0),
            "sw": (0, self._current_height),
            "se": (self._current_width, self._current_height),
        }

        for corner, (x, y) in handle_positions.items():
            self.canvas.coords(
                self.handles[corner],
                x - self.HANDLE_SIZE // 2,
                y - self.HANDLE_SIZE // 2,
                x + self.HANDLE_SIZE // 2,
                y + self.HANDLE_SIZE // 2,
            )
            self.canvas.tag_raise(self.handles[corner])

    def _on_press_move(self, event):
        """Inicia o arraste da janela (só se não for um handle)."""
        clicked_item_id = self.canvas.find_closest(event.x, event.y)
        clicked_tags = self.canvas.gettags(clicked_item_id)

        is_handle = any("handle_" in tag for tag in clicked_tags)

        if not is_handle:
            self._drag_data["x"] = event.x_root
            self._drag_data["y"] = event.y_root
            self._drag_data["state"] = "move"

    def _on_drag_move(self, event):
        """Move a janela inteira."""
        if self._drag_data["state"] == "move":
            delta_x = event.x_root - self._drag_data["x"]
            delta_y = event.y_root - self._drag_data["y"]
            self._drag_data["x"] = event.x_root
            self._drag_data["y"] = event.y_root
            self._current_x += delta_x
            self._current_y += delta_y
            self.geometry(f"+{self._current_x}+{self._current_y}")

    def _on_press_resize(self, event, corner):
        """Define o estado para redimensionamento e salva o ponto de âncora."""
        self._drag_data["x"] = event.x_root
        self._drag_data["y"] = event.y_root
        self._drag_data["state"] = f"resize_{corner}"

        # Posição oposta (âncora) da janela na tela global
        if corner == "nw":
            self._anchor_x, self._anchor_y = (
                self._current_x + self._current_width,
                self._current_y + self._current_height,
            )
        elif corner == "ne":
            self._anchor_x, self._anchor_y = (
                self._current_x,
                self._current_y + self._current_height,
            )
        elif corner == "sw":
            self._anchor_x, self._anchor_y = (
                self._current_x + self._current_width,
                self._current_y,
            )
        elif corner == "se":
            self._anchor_x, self._anchor_y = (
                self._current_x,
                self._current_y,
            )  # Ponto de âncora fixo no canto superior esquerdo

    def _on_drag_resize(self, event, corner):
        """
        Redimensiona a janela com base no canto arrastado, mantendo o canto oposto fixo.
        """
        if self._drag_data["state"] and "resize" in self._drag_data["state"]:
            # Posição atual do mouse na tela global
            current_mouse_x = event.x_root
            current_mouse_y = event.y_root

            new_x = self._current_x
            new_y = self._current_y
            new_width = self._current_width
            new_height = self._current_height

            # === Lógica de Redimensionamento ===

            # Redimensionamento Horizontal
            if "e" in corner:
                # Âncora está no canto esquerdo (X)
                new_width = max(self.MIN_SIZE, current_mouse_x - self._anchor_x)
                new_x = self._anchor_x
            elif "w" in corner:
                # Âncora está no canto direito (X + Width)
                new_width = max(self.MIN_SIZE, self._anchor_x - current_mouse_x)
                if new_width == self.MIN_SIZE:
                    new_x = self._anchor_x - self.MIN_SIZE
                else:
                    new_x = current_mouse_x

            # Redimensionamento Vertical
            if "s" in corner:
                # Âncora está no canto superior (Y)
                new_height = max(self.MIN_SIZE, current_mouse_y - self._anchor_y)
                new_y = self._anchor_y
            elif "n" in corner:
                # Âncora está no canto inferior (Y + Height)
                new_height = max(self.MIN_SIZE, self._anchor_y - current_mouse_y)
                if new_height == self.MIN_SIZE:
                    new_y = self._anchor_y - self.MIN_SIZE
                else:
                    new_y = current_mouse_y

            # Ajusta a largura se a nova posição X for maior que a âncora (movendo para a esquerda)
            if "w" in corner and new_x > self._anchor_x:
                new_x = self._anchor_x
                new_width = self.MIN_SIZE  # Impede inversão

            # Ajusta a altura se a nova posição Y for maior que a âncora (movendo para cima)
            if "n" in corner and new_y > self._anchor_y:
                new_y = self._anchor_y
                new_height = self.MIN_SIZE  # Impede inversão

            # Atualiza o estado da janela
            self._current_x = new_x
            self._current_y = new_y
            self._current_width = new_width
            self._current_height = new_height

            # Aplica a nova geometria
            self.geometry(f"{new_width}x{new_height}+{new_x}+{new_y}")
            self.canvas.config(width=new_width, height=new_height)

            self._draw_overlay()
            self._update_handles()

    def _on_release(self, event):
        """Reseta o estado de arraste e salva as coordenadas."""
        self._drag_data["state"] = None
        self._save_coordinates_to_file()
        print(
            f"Overlay atualizado: x={self._current_x}, y={self._current_y}, width={self._current_width}, height={self._current_height}"
        )

    def _update_geometry(self):
        """Atualiza a geometria da janela e redesenha."""
        self.geometry(
            f"{self._current_width}x{self._current_height}+{self._current_x}+{self._current_y}"
        )
        self.canvas.config(width=self._current_width, height=self._current_height)
        self._draw_overlay()
        self._update_handles()
        self._save_coordinates_to_file()

    def _save_coordinates_to_file(self):
        """Salva as coordenadas atuais do overlay em um arquivo JSON."""
        coords = {
            "x": self._current_x,
            "y": self._current_y,
            "width": self._current_width,
            "height": self._current_height,
        }
        with open(self.coords_file, "w") as f:
            json.dump(coords, f)

    def _load_saved_coords(self):
        """Carrega as coordenadas salvas do arquivo JSON."""
        if os.path.exists(self.coords_file):
            with open(self.coords_file, "r") as f:
                try:
                    coords = json.load(f)
                    self._current_x = coords.get("x", self._current_x)
                    self._current_y = coords.get("y", self._current_y)
                    self._current_width = coords.get("width", self._current_width)
                    self._current_height = coords.get("height", self._current_height)
                except json.JSONDecodeError:
                    print("Erro ao ler JSON. Usando coordenadas padrão.")

    def _confirm_and_close(self):
        """Confirma as coordenadas e fecha o overlay."""
        self._save_coordinates_to_file()
        print(f"Coordenadas confirmadas e salvas em '{self.coords_file}'.")
        self.destroy()


def start_overlay_app():
    """Função para iniciar a aplicação Tkinter do overlay."""
    app = InteractiveOverlay()
    app.mainloop()


if __name__ == "__main__":
    start_overlay_app()
