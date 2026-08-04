import tkinter as tk
from tkinter import ttk


class Dashboard:

    def __init__(self, grid, compressor, extruder):
        self.grid = grid
        self.compressor = compressor
        self.extruder = extruder

        self.root = tk.Tk()
        self.root.title("Simulador")
        self.root.geometry("600x450")

        self._create_widgets()


    def _create_widgets(self):

        frame = ttk.LabelFrame(
            self.root,
            text="Rede Elétrica"
        )

        frame.pack(fill="x", padx=10, pady=10)


        ttk.Button(
            frame,
            text="Iniciar Afundamento de Tensão",
            command=self.grid.start_fault
        ).pack(padx=5, pady=3)


        ttk.Button(
            frame,
            text="Desligar Falha",
            command=self.grid.stop_fault
        ).pack(padx=5, pady=3)




        frame = ttk.LabelFrame(
            self.root,
            text="Compressor"
        )
        frame.pack(fill="x", padx=10, pady=10)


        ttk.Button(
            frame,
            text="Iniciar Falha",
            command=self.compressor.start_fault
        ).pack(padx=5, pady=3)


        ttk.Button(
            frame,
            text="Desligar Falha",
            command=self.compressor.stop_fault
        ).pack(padx=5, pady=3)




        frame = ttk.LabelFrame(
            self.root,
            text="Extrusora"
        )
        frame.pack(fill="x", padx=10, pady=10)


        ttk.Button(
            frame,
            text="Aumentar THD",
            command=self.extruder.start_fault
        ).pack(padx=5, pady=3)


        ttk.Button(
            frame,
            text="Desligar Falha",
            command=self.extruder.stop_fault
        ).pack(padx=5, pady=3)


    def update(self):
        self.root.update()


    def destroy(self):
        self.root.destroy()