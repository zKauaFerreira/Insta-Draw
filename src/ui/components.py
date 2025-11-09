import tkinter as tk

class ScrolledFrame(tk.Frame):
    def __init__(self, parent, *args, **kw):
        tk.Frame.__init__(self, parent, *args, **kw)

        self.canvas = tk.Canvas(self, borderwidth=0, background=self.cget("bg"))
        self.viewPort = tk.Frame(
            self.canvas, background=self.cget("bg")
        )  # The frame to be scrolled
        self.vsb = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)

        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas_window = self.canvas.create_window(
            (4, 4), window=self.viewPort, anchor="nw", tags="self.viewPort"
        )

        self.viewPort.bind("<Configure>", self.onFrameConfigure)
        self.canvas.bind("<Configure>", self.onCanvasConfigure)
        self.bind("<Configure>", self.onFrameConfigure)

        self.onFrameConfigure(None)  # Initial call to set scrollregion

    def onFrameConfigure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def onCanvasConfigure(self, event):
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)

    def _get_canvas_frame(self):
        return self.viewPort
