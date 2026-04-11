import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
import requests
import threading

API = "http://localhost:8001/api/v1"
TOKEN = {"access": None}


def api_get(path, params=None):
    try:
        headers = {"Authorization": f"Bearer {TOKEN['access']}"} if TOKEN["access"] else {}
        r = requests.get(f"{API}{path}", headers=headers, params=params, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return []


def api_post(path, data):
    try:
        headers = {"Authorization": f"Bearer {TOKEN['access']}"} if TOKEN["access"] else {}
        r = requests.post(f"{API}{path}", json=data, headers=headers, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        messagebox.showerror("Error", str(e))
        return None


class LoginDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Inicio de Sesión")
        self.geometry("350x200")
        self.resizable(False, False)
        self.grab_set()
        self.result = False

        ttk.Label(self, text="Sistema de Facturación Paraguay", font=("Arial", 12, "bold")).pack(pady=15)

        frame = ttk.Frame(self)
        frame.pack(padx=30, fill=tk.X)

        ttk.Label(frame, text="Usuario:").grid(row=0, column=0, sticky="w", pady=5)
        self.usuario = ttk.Entry(frame, width=25)
        self.usuario.grid(row=0, column=1, pady=5)
        self.usuario.insert(0, "admin")

        ttk.Label(frame, text="Contraseña:").grid(row=1, column=0, sticky="w", pady=5)
        self.password = ttk.Entry(frame, width=25, show="*")
        self.password.grid(row=1, column=1, pady=5)
        self.password.insert(0, "secret")

        ttk.Button(self, text="Ingresar", command=self.login).pack(pady=15)
        self.bind("<Return>", lambda e: self.login())
        self.usuario.focus()

    def login(self):
        try:
            r = requests.post(f"{API}/auth/login", data={
                "username": self.usuario.get(),
                "password": self.password.get()
            }, timeout=5)
            if r.status_code == 200:
                TOKEN["access"] = r.json().get("access_token")
                self.result = True
                self.destroy()
            else:
                messagebox.showerror("Error", "Usuario o contraseña incorrectos", parent=self)
        except Exception:
            TOKEN["access"] = "demo"
            self.result = True
            self.destroy()


class TabClientes(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._build()
        self.cargar()

    def _build(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=10, pady=8)
        ttk.Button(toolbar, text="+ Nuevo", command=self.nuevo).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="Actualizar", command=self.cargar).pack(side=tk.LEFT, padx=3)
        ttk.Label(toolbar, text="Buscar RUC:").pack(side=tk.RIGHT, padx=3)
        self.busqueda = ttk.Entry(toolbar, width=18)
        self.busqueda.pack(side=tk.RIGHT, padx=3)
        self.busqueda.bind("<Return>", lambda e: self.cargar())

        cols = ("ID", "RUC", "Nombre", "Teléfono", "Email", "Activo")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=130)
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10)

    def cargar(self):
        data = api_get("/clientes")
        self.tree.delete(*self.tree.get_children())
        for c in data:
            self.tree.insert("", "end", values=(
                c.get("id"), c.get("ruc"), c.get("nombre"),
                c.get("telefono", ""), c.get("email", ""), "✓" if c.get("activo") else "✗"
            ))

    def nuevo(self):
        messagebox.showinfo("Próximamente", "Formulario de nuevo cliente")


class TabFacturas(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._build()
        self.cargar()

    def _build(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=10, pady=8)
        ttk.Button(toolbar, text="+ Nueva Factura", command=self.nueva).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="Ver PDF", command=self.ver_pdf).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="Actualizar", command=self.cargar).pack(side=tk.LEFT, padx=3)

        cols = ("N°", "Cliente", "Fecha", "Total (₲)", "Estado", "Condición")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=140)
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10)

        # Colorear filas por estado
        self.tree.tag_configure("EMITIDA", background="#e8f5e9")
        self.tree.tag_configure("BORRADOR", background="#fff8e1")
        self.tree.tag_configure("ANULADA", background="#ffebee")

    def cargar(self):
        data = api_get("/facturas")
        self.tree.delete(*self.tree.get_children())
        for f in data:
            estado = f.get("estado", "")
            self.tree.insert("", "end", tags=(estado,), values=(
                f.get("numero_factura", f.get("id")),
                f.get("cliente_id", ""),
                str(f.get("fecha_emision", ""))[:10],
                f"₲ {float(f.get('monto_total', 0)):,.0f}",
                estado,
                f.get("condicion_venta", "")
            ))

    def nueva(self):
        messagebox.showinfo("Próximamente", "Formulario de nueva factura")

    def ver_pdf(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Selecciona una factura")
            return
        messagebox.showinfo("Próximamente", "Generar PDF de la factura seleccionada")


class TabProductos(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._build()
        self.cargar()

    def _build(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=10, pady=8)
        ttk.Button(toolbar, text="+ Nuevo", command=self.nuevo).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="Actualizar", command=self.cargar).pack(side=tk.LEFT, padx=3)

        cols = ("ID", "Código", "Descripción", "Precio (₲)", "IVA", "Activo")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=150)
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10)

    def cargar(self):
        data = api_get("/productos")
        self.tree.delete(*self.tree.get_children())
        for p in data:
            self.tree.insert("", "end", values=(
                p.get("id"), p.get("codigo"), p.get("descripcion"),
                f"₲ {float(p.get('precio_unitario', 0)):,.0f}",
                f"{p.get('tasa_iva', '')}%",
                "✓" if p.get("activo") else "✗"
            ))

    def nuevo(self):
        messagebox.showinfo("Próximamente", "Formulario de nuevo producto")


class TabProveedores(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._build()
        self.cargar()

    def _build(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=10, pady=8)
        ttk.Button(toolbar, text="+ Nuevo", command=self.nuevo).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="Actualizar", command=self.cargar).pack(side=tk.LEFT, padx=3)

        cols = ("ID", "RUC", "Nombre", "Teléfono", "Email", "Saldo (₲)")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=140)
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10)

    def cargar(self):
        data = api_get("/proveedores")
        self.tree.delete(*self.tree.get_children())
        for p in data:
            self.tree.insert("", "end", values=(
                p.get("prov_cod"), p.get("prov_ruc"), p.get("prov_nom"),
                p.get("prov_tel", ""), p.get("prov_email", ""),
                f"₲ {float(p.get('prov_sal', 0)):,.0f}"
            ))

    def nuevo(self):
        messagebox.showinfo("Próximamente", "Formulario de nuevo proveedor")


class TabCompras(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._build()
        self.cargar()

    def _build(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=10, pady=8)
        ttk.Button(toolbar, text="+ Nueva Compra", command=self.nueva).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="Actualizar", command=self.cargar).pack(side=tk.LEFT, padx=3)

        cols = ("N°", "Proveedor", "Fecha", "Total (₲)", "Tipo", "Estado")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=150)
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10)

        self.tree.tag_configure("recibida", background="#e8f5e9")
        self.tree.tag_configure("anulada", background="#ffebee")

    def cargar(self):
        data = api_get("/compras")
        self.tree.delete(*self.tree.get_children())
        tipos = {1: "Contado", 2: "Crédito", 3: "Cheque"}
        for c in data:
            estado = c.get("com_estado", "")
            self.tree.insert("", "end", tags=(estado,), values=(
                c.get("com_nro"),
                c.get("com_proveedor", ""),
                str(c.get("com_fecha", ""))[:10],
                f"₲ {float(c.get('com_total', 0)):,.0f}",
                tipos.get(c.get("com_tipo", 1), "Contado"),
                estado.upper()
            ))

    def nueva(self):
        messagebox.showinfo("Próximamente", "Formulario de nueva compra")


class TabCaja(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._build()
        self.cargar()

    def _build(self):
        # Info de caja actual
        info_frame = ttk.LabelFrame(self, text="Caja de Hoy")
        info_frame.pack(fill=tk.X, padx=10, pady=8)

        self.lbl_fecha = ttk.Label(info_frame, text="Fecha: —")
        self.lbl_fecha.grid(row=0, column=0, padx=15, pady=5)
        self.lbl_ingreso = ttk.Label(info_frame, text="Ingresos: ₲ 0", foreground="green")
        self.lbl_ingreso.grid(row=0, column=1, padx=15)
        self.lbl_egreso = ttk.Label(info_frame, text="Egresos: ₲ 0", foreground="red")
        self.lbl_egreso.grid(row=0, column=2, padx=15)
        self.lbl_saldo = ttk.Label(info_frame, text="Saldo: ₲ 0", font=("Arial", 11, "bold"))
        self.lbl_saldo.grid(row=0, column=3, padx=15)
        self.lbl_estado = ttk.Label(info_frame, text="Estado: —")
        self.lbl_estado.grid(row=0, column=4, padx=15)

        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=10, pady=4)
        ttk.Button(toolbar, text="Abrir Caja", command=self.abrir_caja).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="Cerrar Caja", command=self.cerrar_caja).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="Actualizar", command=self.cargar).pack(side=tk.LEFT, padx=3)

        # Historial
        ttk.Label(self, text="Historial de Cajas", font=("Arial", 10, "bold")).pack(padx=10, anchor="w")
        cols = ("Fecha", "Saldo Inicial", "Ingresos", "Egresos", "Saldo Final", "Estado")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=150)
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def cargar(self):
        caja = api_get("/caja/hoy")
        if isinstance(caja, dict) and "caj_fecha" in caja:
            self.lbl_fecha.config(text=f"Fecha: {caja['caj_fecha']}")
            self.lbl_ingreso.config(text=f"Ingresos: ₲ {float(caja['caj_totalingre']):,.0f}")
            self.lbl_egreso.config(text=f"Egresos: ₲ {float(caja['caj_totalegre']):,.0f}")
            self.lbl_saldo.config(text=f"Saldo: ₲ {float(caja['caj_saldofinal']):,.0f}")
            self.lbl_estado.config(text="Cerrada ✗" if caja.get("caj_cerrada") else "Abierta ✓",
                                   foreground="red" if caja.get("caj_cerrada") else "green")

        historial = api_get("/caja/historial")
        self.tree.delete(*self.tree.get_children())
        for c in historial:
            self.tree.insert("", "end", values=(
                c.get("caj_fecha"),
                f"₲ {float(c.get('caj_saldoinicial', 0)):,.0f}",
                f"₲ {float(c.get('caj_totalingre', 0)):,.0f}",
                f"₲ {float(c.get('caj_totalegre', 0)):,.0f}",
                f"₲ {float(c.get('caj_saldofinal', 0)):,.0f}",
                "Cerrada" if c.get("caj_cerrada") else "Abierta"
            ))

    def abrir_caja(self):
        res = api_post("/caja/abrir", {"caj_usuario": "admin", "caj_saldoinicial": 0})
        if res:
            messagebox.showinfo("OK", "Caja abierta correctamente")
            self.cargar()

    def cerrar_caja(self):
        if messagebox.askyesno("Confirmar", "¿Cerrar la caja de hoy?"):
            res = api_post("/caja/cerrar", {})
            if res:
                messagebox.showinfo("OK", f"Caja cerrada. Saldo final: ₲ {res.get('saldo_final', 0):,.0f}")
                self.cargar()


class TabReportes(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._build()

    def _build(self):
        # Filtros
        filtros = ttk.LabelFrame(self, text="Ventas por Período")
        filtros.pack(fill=tk.X, padx=10, pady=8)

        ttk.Label(filtros, text="Desde:").grid(row=0, column=0, padx=8, pady=8)
        self.desde = ttk.Entry(filtros, width=12)
        self.desde.insert(0, str(date.today()).replace("-01", "-01"))
        self.desde.grid(row=0, column=1, padx=5)

        ttk.Label(filtros, text="Hasta:").grid(row=0, column=2, padx=8)
        self.hasta = ttk.Entry(filtros, width=12)
        self.hasta.insert(0, str(date.today()))
        self.hasta.grid(row=0, column=3, padx=5)

        ttk.Button(filtros, text="Generar", command=self.generar_ventas).grid(row=0, column=4, padx=10)

        self.resultado = ttk.Label(self, text="", font=("Arial", 11))
        self.resultado.pack(pady=10)

        # Otros reportes
        otros = ttk.LabelFrame(self, text="Otros Reportes")
        otros.pack(fill=tk.X, padx=10, pady=8)

        ttk.Button(otros, text="Clientes Deudores", command=self.clientes_deudores).pack(side=tk.LEFT, padx=10, pady=8)
        ttk.Button(otros, text="Productos Más Vendidos", command=self.mas_vendidos).pack(side=tk.LEFT, padx=10)
        ttk.Button(otros, text="IVA Mensual", command=self.iva_mensual).pack(side=tk.LEFT, padx=10)

        cols = ("Campo", "Valor")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=300)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def generar_ventas(self):
        data = api_get("/reportes/ventas-periodo", {"desde": self.desde.get(), "hasta": self.hasta.get()})
        if isinstance(data, dict):
            self.tree.delete(*self.tree.get_children())
            for k, v in data.items():
                self.tree.insert("", "end", values=(k, v))

    def clientes_deudores(self):
        data = api_get("/reportes/clientes-deudores")
        self.tree.delete(*self.tree.get_children())
        for c in data:
            self.tree.insert("", "end", values=(c.get("nombre"), f"₲ {float(c.get('total_deuda', 0)):,.0f}"))

    def mas_vendidos(self):
        data = api_get("/reportes/productos-mas-vendidos")
        self.tree.delete(*self.tree.get_children())
        for p in data:
            self.tree.insert("", "end", values=(p.get("descripcion"), f"Vendido: {p.get('total_vendido')}"))

    def iva_mensual(self):
        hoy = date.today()
        data = api_get("/reportes/iva-mensual", {"anio": hoy.year, "mes": hoy.month})
        if isinstance(data, dict):
            self.tree.delete(*self.tree.get_children())
            for k, v in data.items():
                self.tree.insert("", "end", values=(k, v))


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Facturación Paraguay")
        self.geometry("1300x750")
        self.configure(bg="#f5f5f5")

        self._login()
        self._build_menu()
        self._build_tabs()
        self._build_statusbar()

    def _login(self):
        dlg = LoginDialog(self)
        self.wait_window(dlg)
        if not dlg.result:
            self.destroy()

    def _build_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        m = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=m)
        m.add_command(label="Salir", command=self.quit)

        m2 = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ayuda", menu=m2)
        m2.add_command(label="Acerca de", command=lambda: messagebox.showinfo(
            "Acerca de", "Sistema de Facturación Paraguay v1.0\nBased on Zion v50 design"
        ))

    def _build_tabs(self):
        nb = ttk.Notebook(self)
        nb.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        nb.add(TabFacturas(nb), text="  Facturas  ")
        nb.add(TabClientes(nb), text="  Clientes  ")
        nb.add(TabProductos(nb), text="  Productos  ")
        nb.add(TabProveedores(nb), text="  Proveedores  ")
        nb.add(TabCompras(nb), text="  Compras  ")
        nb.add(TabCaja(nb), text="  Caja  ")
        nb.add(TabReportes(nb), text="  Reportes  ")

    def _build_statusbar(self):
        bar = tk.Frame(self, relief=tk.SUNKEN, bd=1)
        bar.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Label(bar, text=f"Sistema de Facturación Paraguay | {date.today()}").pack(side=tk.LEFT, padx=10, pady=3)
        ttk.Label(bar, text="API: localhost:8000").pack(side=tk.RIGHT, padx=10)


if __name__ == "__main__":
    App().mainloop()
