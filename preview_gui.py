#!/usr/bin/env python3
"""
Vista previa de la GUI de escritorio para FacturaPY
Ejecutar: python preview_gui.py
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

class FacturacionGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("FacturaPY v1.0")
        self.root.geometry("1400x800")
        self.root.configure(bg="#f0f0f0")

        # Crear menú
        self.create_menu()

        # Crear frame principal con tabs
        self.create_tabs()

        # Status bar
        self.create_statusbar()

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Menú Archivo
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_command(label="Nueva Factura", command=self.new_factura)
        file_menu.add_command(label="Nuevo Cliente", command=self.new_cliente)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.root.quit)

        # Menú Herramientas
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Herramientas", menu=tools_menu)
        tools_menu.add_command(label="Configuración Empresa", command=self.config_empresa)
        tools_menu.add_command(label="Reportes", command=self.reportes)

        # Menú Ayuda
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ayuda", menu=help_menu)
        help_menu.add_command(label="Acerca de", command=self.about)

    def create_tabs(self):
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Dashboard
        self.tab_dashboard(notebook)

        # Tab 2: Facturas
        self.tab_facturas(notebook)

        # Tab 3: Clientes
        self.tab_clientes(notebook)

        # Tab 4: Productos
        self.tab_productos(notebook)

        # Tab 5: Reportes
        self.tab_reportes(notebook)

    def tab_dashboard(self, notebook):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Dashboard")

        # Título
        title = ttk.Label(frame, text="Dashboard - Vista General", font=("Arial", 16, "bold"))
        title.pack(pady=10)

        # Cards de estadísticas
        cards_frame = ttk.Frame(frame)
        cards_frame.pack(fill=tk.BOTH, padx=10, pady=10)

        self.create_card(cards_frame, "Facturas Hoy", "12", "#4CAF50", 0, 0)
        self.create_card(cards_frame, "Monto Total", "₲ 15,450,000", "#2196F3", 0, 1)
        self.create_card(cards_frame, "Pendiente de Pago", "₲ 3,200,000", "#FF9800", 0, 2)
        self.create_card(cards_frame, "Clientes Activos", "28", "#9C27B0", 0, 3)

        # Gráfico simple (placeholder)
        graph_frame = ttk.LabelFrame(frame, text="Ventas últimos 7 días")
        graph_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        canvas = tk.Canvas(graph_frame, height=200, bg="white")
        canvas.pack(fill=tk.BOTH, expand=True)

        # Dibujar barras simples
        canvas.create_rectangle(50, 150, 80, 100, fill="#2196F3")
        canvas.create_rectangle(90, 150, 120, 80, fill="#2196F3")
        canvas.create_rectangle(130, 150, 160, 120, fill="#2196F3")
        canvas.create_text(65, 180, text="Lun")
        canvas.create_text(105, 180, text="Mar")
        canvas.create_text(145, 180, text="Mié")

    def create_card(self, parent, title, value, color, row, col):
        card = tk.Frame(parent, bg=color, height=100)
        card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew", ipadx=20, ipady=20)

        ttk.Label(card, text=title, font=("Arial", 10), background=color, foreground="white").pack()
        ttk.Label(card, text=value, font=("Arial", 18, "bold"), background=color, foreground="white").pack()

        parent.columnconfigure(col, weight=1)

    def tab_facturas(self, notebook):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Facturas")

        # Barra de herramientas
        toolbar = ttk.Frame(frame)
        toolbar.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(toolbar, text="+ Nueva Factura", command=self.new_factura).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Emitir", command=self.emitir_factura).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="PDF", command=self.generar_pdf).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Anular", command=self.anular_factura).pack(side=tk.LEFT, padx=5)

        # Búsqueda
        search_frame = ttk.Frame(toolbar)
        search_frame.pack(side=tk.RIGHT, padx=5)
        ttk.Label(search_frame, text="Buscar:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(search_frame, width=20).pack(side=tk.LEFT)

        # Tabla de facturas
        table_frame = ttk.Frame(frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("Número", "Cliente", "Fecha", "Monto", "Estado", "Acciones")
        tree = ttk.Treeview(table_frame, columns=columns, height=20)
        tree.pack(fill=tk.BOTH, expand=True)

        tree.column("#0", width=0, stretch=tk.NO)
        tree.column("Número", width=120)
        tree.column("Cliente", width=200)
        tree.column("Fecha", width=120)
        tree.column("Monto", width=150)
        tree.column("Estado", width=100)
        tree.column("Acciones", width=150)

        tree.heading("#0", text="")
        tree.heading("Número", text="Número")
        tree.heading("Cliente", text="Cliente")
        tree.heading("Fecha", text="Fecha")
        tree.heading("Monto", text="Monto")
        tree.heading("Estado", text="Estado")
        tree.heading("Acciones", text="Acciones")

        # Datos de ejemplo
        datos = [
            ("001-001-0000001", "Empresa XYZ S.A.", "2024-04-10", "₲ 850,000", "Emitida", "Ver | PDF"),
            ("001-001-0000002", "Cliente ABC", "2024-04-10", "₲ 520,000", "Borrador", "Editar | Emitir"),
            ("001-001-0000003", "RH Logística", "2024-04-09", "₲ 1,250,000", "Pagada", "Ver | PDF"),
        ]

        for i, row in enumerate(datos):
            tree.insert(parent="", index="end", iid=i, text="", values=row)

    def tab_clientes(self, notebook):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Clientes")

        # Barra de herramientas
        toolbar = ttk.Frame(frame)
        toolbar.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(toolbar, text="+ Nuevo Cliente", command=self.new_cliente).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Editar", command=self.edit_cliente).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Eliminar", command=self.delete_cliente).pack(side=tk.LEFT, padx=5)

        ttk.Label(toolbar, text="Buscar por RUC:").pack(side=tk.RIGHT, padx=5)
        ttk.Entry(toolbar, width=20).pack(side=tk.RIGHT, padx=5)

        # Tabla
        table_frame = ttk.Frame(frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("RUC", "Razón Social", "Email", "Teléfono", "Estado")
        tree = ttk.Treeview(table_frame, columns=columns, height=20)
        tree.pack(fill=tk.BOTH, expand=True)

        for col in columns:
            tree.column(col, width=150)
            tree.heading(col, text=col)

        datos = [
            ("5000005-8", "Empresa XYZ S.A.", "contacto@xyz.com", "+595 971 123456", "Activo"),
            ("80069563-1", "Cliente ABC", "abc@mail.com", "+595 983 456789", "Activo"),
            ("3456789-2", "RH Logística", "rh@log.com", "+595 991 234567", "Inactivo"),
        ]

        for i, row in enumerate(datos):
            tree.insert(parent="", index="end", iid=i, text="", values=row)

    def tab_productos(self, notebook):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Productos")

        toolbar = ttk.Frame(frame)
        toolbar.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(toolbar, text="+ Nuevo Producto", command=self.new_producto).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Editar", command=self.edit_producto).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Eliminar", command=self.delete_producto).pack(side=tk.LEFT, padx=5)

        table_frame = ttk.Frame(frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("Código", "Descripción", "Precio", "IVA", "Stock")
        tree = ttk.Treeview(table_frame, columns=columns, height=20)
        tree.pack(fill=tk.BOTH, expand=True)

        for col in columns:
            tree.column(col, width=150)
            tree.heading(col, text=col)

        datos = [
            ("P001", "Servicio de Consultoría", "₲ 500,000", "10%", "∞"),
            ("P002", "Licencia Software", "₲ 150,000", "10%", "∞"),
            ("P003", "Hardware", "₲ 3,500,000", "10%", "15"),
        ]

        for i, row in enumerate(datos):
            tree.insert(parent="", index="end", iid=i, text="", values=row)

    def tab_reportes(self, notebook):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Reportes")

        title = ttk.Label(frame, text="Reportes y Análisis", font=("Arial", 14, "bold"))
        title.pack(pady=10)

        # Opciones de reporte
        options_frame = ttk.Frame(frame)
        options_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(options_frame, text="Tipo de Reporte:").pack(side=tk.LEFT, padx=5)
        reporte_var = tk.StringVar()
        ttk.Combobox(options_frame, textvariable=reporte_var, values=[
            "Ventas por Período",
            "Clientes Morosos",
            "Productos Más Vendidos",
            "IVA Mensual"
        ], state="readonly", width=25).pack(side=tk.LEFT, padx=5)

        ttk.Button(options_frame, text="Generar", command=self.generar_reporte).pack(side=tk.LEFT, padx=5)
        ttk.Button(options_frame, text="Exportar PDF", command=self.exportar_reporte).pack(side=tk.LEFT, padx=5)

        # Área de contenido
        content_frame = ttk.Frame(frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(content_frame, text="Selecciona un reporte para visualizar").pack(pady=50)

    def create_statusbar(self):
        statusbar = ttk.Frame(self.root, relief=tk.SUNKEN)
        statusbar.pack(side=tk.BOTTOM, fill=tk.X)

        ttk.Label(statusbar, text="Usuario: admin | Empresa: Mi Empresa S.A. | Conectado: ✓", relief=tk.SUNKEN).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Label(statusbar, text=f"Última actualización: {datetime.now().strftime('%H:%M:%S')}", relief=tk.SUNKEN).pack(side=tk.RIGHT, padx=5, pady=5)

    # Callbacks (por ahora vacíos)
    def new_factura(self):
        messagebox.showinfo("Desarrollo", "Próximamente: Crear nueva factura")

    def new_cliente(self):
        messagebox.showinfo("Desarrollo", "Próximamente: Crear nuevo cliente")

    def new_producto(self):
        messagebox.showinfo("Desarrollo", "Próximamente: Crear nuevo producto")

    def emitir_factura(self):
        messagebox.showinfo("Desarrollo", "Próximamente: Emitir factura")

    def generar_pdf(self):
        messagebox.showinfo("Desarrollo", "Próximamente: Generar PDF")

    def anular_factura(self):
        messagebox.showinfo("Desarrollo", "Próximamente: Anular factura")

    def edit_cliente(self):
        messagebox.showinfo("Desarrollo", "Próximamente: Editar cliente")

    def delete_cliente(self):
        messagebox.showinfo("Desarrollo", "Próximamente: Eliminar cliente")

    def edit_producto(self):
        messagebox.showinfo("Desarrollo", "Próximamente: Editar producto")

    def delete_producto(self):
        messagebox.showinfo("Desarrollo", "Próximamente: Eliminar producto")

    def config_empresa(self):
        messagebox.showinfo("Desarrollo", "Próximamente: Configurar empresa")

    def reportes(self):
        messagebox.showinfo("Desarrollo", "Próximamente: Ver reportes")

    def generar_reporte(self):
        messagebox.showinfo("Desarrollo", "Próximamente: Generar reporte")

    def exportar_reporte(self):
        messagebox.showinfo("Desarrollo", "Próximamente: Exportar reporte")

    def about(self):
        messagebox.showinfo("Acerca de", "FacturaPY v1.0\n\nSistema de Gestión Comercial para Paraguay")

if __name__ == "__main__":
    root = tk.Tk()
    app = FacturacionGUI(root)
    root.mainloop()
