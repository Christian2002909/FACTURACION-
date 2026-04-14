"""
GUI moderna — Sistema de Facturación Paraguay
CustomTkinter · dark mode · diseño profesional
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading
import json
from datetime import date, datetime
from decimal import Decimal

# ── Configuración global ──────────────────────────────────────────────────────
API = "http://localhost:8000/api/v1"
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

C = {
    "bg":       "#1a1a2e",
    "panel":    "#16213e",
    "card":     "#0f3460",
    "accent":   "#e94560",
    "accent2":  "#533483",
    "text":     "#eaeaea",
    "muted":    "#8892a4",
    "success":  "#2ecc71",
    "warning":  "#f39c12",
    "danger":   "#e74c3c",
    "border":   "#2a2a4a",
    "row_even": "#1e1e3a",
    "row_odd":  "#16213e",
    "sel":      "#533483",
}


# ── Cliente HTTP ──────────────────────────────────────────────────────────────
class APIClient:
    def __init__(self):
        self.token = None
        self.s = requests.Session()

    def login(self, username, password):
        r = self.s.post(f"{API}/auth/login",
                        json={"username": username, "password": password}, timeout=5)
        if r.status_code == 200:
            self.token = r.json()["access_token"]
            self.s.headers.update({"Authorization": f"Bearer {self.token}"})
            return True
        return False

    def get(self, path, **kw):
        return self.s.get(f"{API}{path}", timeout=10, **kw)

    def post(self, path, **kw):
        return self.s.post(f"{API}{path}", timeout=10, **kw)

    def put(self, path, **kw):
        return self.s.put(f"{API}{path}", timeout=10, **kw)

    def delete(self, path, **kw):
        return self.s.delete(f"{API}{path}", timeout=10, **kw)


client = APIClient()


# ── Helpers ───────────────────────────────────────────────────────────────────
def make_table(parent, columns, col_widths=None):
    frame = ctk.CTkFrame(parent, fg_color=C["panel"], corner_radius=10)
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Dark.Treeview",
                    background=C["row_odd"], foreground=C["text"],
                    fieldbackground=C["row_odd"], rowheight=32,
                    borderwidth=0, font=("Segoe UI", 11))
    style.configure("Dark.Treeview.Heading",
                    background=C["card"], foreground=C["text"],
                    font=("Segoe UI", 11, "bold"), borderwidth=0, relief="flat")
    style.map("Dark.Treeview",
              background=[("selected", C["sel"])],
              foreground=[("selected", "#ffffff")])
    style.map("Dark.Treeview.Heading",
              background=[("active", C["accent2"])])

    tree = ttk.Treeview(frame, columns=columns, show="headings",
                        style="Dark.Treeview", selectmode="browse")
    for i, col in enumerate(columns):
        w = col_widths[i] if col_widths else 150
        tree.heading(col, text=col)
        tree.column(col, width=w, anchor="w")

    sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
    sb.pack(side="right", fill="y", pady=8)
    tree.tag_configure("even", background=C["row_even"])
    tree.tag_configure("odd",  background=C["row_odd"])
    return frame, tree


def apply_zebra(tree):
    for i, item in enumerate(tree.get_children()):
        tree.item(item, tags=("even" if i % 2 == 0 else "odd",))


def field(parent, label, row, col=0, wide=False, choices=None, default=None):
    ctk.CTkLabel(parent, text=label, text_color=C["muted"],
                 font=("Segoe UI", 11)).grid(row=row, column=col * 2,
                                              sticky="w", padx=(12, 8), pady=5)
    if choices:
        var = ctk.StringVar(value=default or choices[0])
        w = ctk.CTkOptionMenu(parent, values=choices, variable=var,
                               width=260 if wide else 200,
                               fg_color=C["card"], button_color=C["accent2"],
                               font=("Segoe UI", 11))
        w.grid(row=row, column=col * 2 + 1, sticky="ew", pady=5,
               columnspan=3 if wide else 1, padx=(0, 12))
        return var
    else:
        var = ctk.StringVar(value=default or "")
        e = ctk.CTkEntry(parent, textvariable=var,
                         width=420 if wide else 200,
                         fg_color=C["card"], border_color=C["border"],
                         text_color=C["text"], font=("Segoe UI", 11))
        e.grid(row=row, column=col * 2 + 1, sticky="ew", pady=5,
               columnspan=3 if wide else 1, padx=(0, 12))
        return var


def toast(parent, msg, ok=True):
    color = C["success"] if ok else C["danger"]
    t = ctk.CTkLabel(parent, text=f"  {'✓' if ok else '✗'}  {msg}  ",
                     fg_color=color, text_color="#fff",
                     corner_radius=8, font=("Segoe UI", 12, "bold"))
    t.place(relx=0.5, rely=0.97, anchor="s")
    parent.after(3000, t.destroy)


def btn(parent, text, cmd, color=None, icon=""):
    color = color or C["accent"]
    return ctk.CTkButton(parent, text=f"{icon}  {text}" if icon else text,
                         command=cmd, fg_color=color, hover_color=C["accent2"],
                         font=("Segoe UI", 12, "bold"),
                         corner_radius=8, height=36)


def gs(val):
    return f"Gs {int(float(val or 0)):,}".replace(",", ".")


# ── Login ─────────────────────────────────────────────────────────────────────
class LoginScreen(ctk.CTkFrame):
    def __init__(self, master, on_success):
        super().__init__(master, fg_color=C["bg"])
        self.on_success = on_success
        self._build()

    def _build(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        card = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=20,
                            width=400, height=480)
        card.grid(row=0, column=0)
        card.grid_propagate(False)

        ctk.CTkLabel(card, text="📊", font=("Segoe UI", 52)).pack(pady=(44, 4))
        ctk.CTkLabel(card, text="Facturación Paraguay",
                     font=("Segoe UI", 22, "bold"),
                     text_color=C["text"]).pack()
        ctk.CTkLabel(card, text="Sistema de Gestión Comercial",
                     font=("Segoe UI", 12), text_color=C["muted"]).pack(pady=(2, 28))

        self.user = ctk.CTkEntry(card, placeholder_text="Usuario",
                                  width=300, height=44,
                                  fg_color=C["card"], border_color=C["border"],
                                  font=("Segoe UI", 13))
        self.user.pack(pady=6)
        self.user.insert(0, "admin")

        self.pw = ctk.CTkEntry(card, placeholder_text="Contraseña",
                                show="•", width=300, height=44,
                                fg_color=C["card"], border_color=C["border"],
                                font=("Segoe UI", 13))
        self.pw.pack(pady=6)
        self.pw.insert(0, "admin123")

        self.err = ctk.CTkLabel(card, text="", text_color=C["danger"],
                                 font=("Segoe UI", 11))
        self.err.pack(pady=4)

        self.login_btn = ctk.CTkButton(card, text="Iniciar Sesión",
                                        command=self._login,
                                        width=300, height=44,
                                        fg_color=C["accent"], hover_color="#c0392b",
                                        font=("Segoe UI", 13, "bold"), corner_radius=10)
        self.login_btn.pack(pady=8)
        ctk.CTkLabel(card, text="v2.0 · Paraguay 2026",
                     text_color=C["muted"], font=("Segoe UI", 10)).pack(pady=(16, 0))
        self.pw.bind("<Return>", lambda e: self._login())

    def _login(self):
        self.login_btn.configure(state="disabled", text="Verificando...")
        self.err.configure(text="")
        threading.Thread(target=lambda: self._do_login(), daemon=True).start()

    def _do_login(self):
        ok = client.login(self.user.get(), self.pw.get())
        self.after(0, lambda: self._result(ok))

    def _result(self, ok):
        self.login_btn.configure(state="normal", text="Iniciar Sesión")
        if ok:
            self.on_success()
        else:
            self.err.configure(text="Usuario o contraseña incorrectos")


# ── Sidebar ───────────────────────────────────────────────────────────────────
MENU = [
    ("🏠", "Dashboard"),
    ("📄", "Facturas"),
    ("👥", "Clientes"),
    ("📦", "Productos"),
    ("🏭", "Proveedores"),
    ("🛒", "Compras"),
    ("💰", "Caja"),
    ("📈", "Reportes"),
]


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, on_select):
        super().__init__(master, fg_color=C["panel"], width=210, corner_radius=0)
        self.on_select = on_select
        self._btns = {}
        self._active = None
        self._build()

    def _build(self):
        self.pack_propagate(False)
        logo = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=0, height=64)
        logo.pack(fill="x")
        logo.pack_propagate(False)
        ctk.CTkLabel(logo, text="📊 Facturación",
                     font=("Segoe UI", 15, "bold"), text_color=C["text"]).pack(expand=True)

        ctk.CTkFrame(self, fg_color=C["border"], height=1).pack(fill="x")
        ctk.CTkLabel(self, text="  MENÚ PRINCIPAL", text_color=C["muted"],
                     font=("Segoe UI", 9, "bold")).pack(pady=(16, 4), anchor="w")

        for icon, name in MENU:
            b = ctk.CTkButton(self, text=f"  {icon}  {name}", anchor="w",
                               height=44, fg_color="transparent",
                               hover_color=C["card"], text_color=C["muted"],
                               font=("Segoe UI", 12), corner_radius=6,
                               command=lambda n=name: self.select(n))
            b.pack(fill="x", padx=8, pady=2)
            self._btns[name] = b

        ctk.CTkFrame(self, fg_color="transparent").pack(fill="both", expand=True)
        ctk.CTkLabel(self, text="v2.0 · 2026",
                     text_color=C["muted"], font=("Segoe UI", 9)).pack(pady=12)

    def select(self, name):
        if self._active:
            self._btns[self._active].configure(fg_color="transparent",
                                                text_color=C["muted"])
        self._active = name
        self._btns[name].configure(fg_color=C["accent"], text_color="#ffffff")
        self.on_select(name)


# ── Dashboard ─────────────────────────────────────────────────────────────────
class DashboardPanel(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=C["bg"])
        self._build()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 8))
        ctk.CTkLabel(hdr, text="Dashboard",
                     font=("Segoe UI", 22, "bold"), text_color=C["text"]).pack(side="left")
        ctk.CTkLabel(hdr, text=f"Hoy: {date.today().strftime('%d/%m/%Y')}",
                     font=("Segoe UI", 12), text_color=C["muted"]).pack(side="right")

        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.pack(fill="x", padx=24, pady=8)
        self.m = {}
        defs = [("💰", "Ventas Hoy", "—", C["success"]),
                ("📄", "Facturas", "—", C["accent"]),
                ("👥", "Clientes", "—", C["accent2"]),
                ("📦", "Productos", "—", C["warning"])]
        for i, (icon, lbl, val, color) in enumerate(defs):
            card = ctk.CTkFrame(cards_frame, fg_color=C["panel"], corner_radius=12)
            card.grid(row=0, column=i, padx=8, sticky="ew")
            cards_frame.grid_columnconfigure(i, weight=1)
            ctk.CTkLabel(card, text=icon, font=("Segoe UI", 30)).pack(pady=(16, 0))
            v = ctk.CTkLabel(card, text=val, font=("Segoe UI", 18, "bold"),
                             text_color=color)
            v.pack()
            ctk.CTkLabel(card, text=lbl, font=("Segoe UI", 10),
                         text_color=C["muted"]).pack(pady=(0, 14))
            self.m[lbl] = v

        info = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=12)
        info.pack(fill="both", expand=True, padx=24, pady=16)
        ctk.CTkLabel(info, text="Sistema de Facturación Paraguay",
                     font=("Segoe UI", 18, "bold"), text_color=C["text"]).pack(pady=(28, 4))
        ctk.CTkLabel(info,
                     text="Gestión completa de facturas electrónicas, clientes, productos, caja y reportes.",
                     font=("Segoe UI", 12), text_color=C["muted"]).pack()
        ctk.CTkLabel(info,
                     text="✓ Factura electrónica SIFEN  ·  ✓ PDF automático  ·  ✓ IVA 5% y 10%  ·  ✓ Dark Mode",
                     font=("Segoe UI", 11), text_color=C["success"]).pack(pady=12)

        threading.Thread(target=self._load, daemon=True).start()

    def _load(self):
        try:
            cl = client.get("/clientes").json()
            pr = client.get("/productos").json()
            fa = client.get("/facturas").json()
            self.after(0, lambda: self.m["Clientes"].configure(text=str(len(cl) if isinstance(cl, list) else 0)))
            self.after(0, lambda: self.m["Productos"].configure(text=str(len(pr) if isinstance(pr, list) else 0)))
            self.after(0, lambda: self.m["Facturas"].configure(text=str(len(fa) if isinstance(fa, list) else 0)))
        except Exception:
            pass


# ── Base CRUD ─────────────────────────────────────────────────────────────────
class CrudPanel(ctk.CTkFrame):
    TITLE = ""
    COLUMNS = []
    COL_WIDTHS = []

    def __init__(self, master):
        super().__init__(master, fg_color=C["bg"])
        self._items = []
        self._sel_id = None
        self._build_layout()

    def _build_layout(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 4))
        ctk.CTkLabel(hdr, text=self.TITLE,
                     font=("Segoe UI", 22, "bold"), text_color=C["text"]).pack(side="left")

        tb = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=10, height=52)
        tb.pack(fill="x", padx=24, pady=4)
        tb.pack_propagate(False)
        self._build_toolbar(tb)

        tf, self.tree = make_table(self, self.COLUMNS, self.COL_WIDTHS)
        tf.pack(fill="both", expand=True, padx=24, pady=(4, 8))
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", lambda e: self._on_edit())
        self.load()

    def _build_toolbar(self, tb):
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *a: self._filter())
        ctk.CTkEntry(tb, textvariable=self.search_var, placeholder_text="🔍  Buscar...",
                     width=240, height=34, fg_color=C["card"], border_color=C["border"],
                     font=("Segoe UI", 12)).pack(side="left", padx=12, pady=8)
        btn(tb, "Nuevo", self._on_new, C["accent"], "➕").pack(side="left", padx=4)
        btn(tb, "Editar", self._on_edit, C["accent2"], "✏️").pack(side="left", padx=4)
        btn(tb, "Eliminar", self._on_delete, C["danger"], "🗑️").pack(side="left", padx=4)
        btn(tb, "↺ Actualizar", self.load, C["card"]).pack(side="right", padx=12)

    def _on_select(self, e):
        sel = self.tree.selection()
        if sel:
            self._sel_id = self.tree.item(sel[0])["values"][0]

    def _filter(self):
        q = self.search_var.get().lower()
        for i in self.tree.get_children():
            self.tree.delete(i)
        for it in self._items:
            if any(q in str(v).lower() for v in it.values()):
                self._insert_row(it)
        apply_zebra(self.tree)

    def _insert_row(self, item): raise NotImplementedError
    def load(self): raise NotImplementedError
    def _on_new(self): self._open_form(None)

    def _on_edit(self):
        if not self._sel_id:
            return messagebox.showinfo("Aviso", "Seleccione un registro")
        item = next((i for i in self._items if i.get("id") == self._sel_id), None)
        self._open_form(item)

    def _on_delete(self):
        if not self._sel_id:
            return messagebox.showinfo("Aviso", "Seleccione un registro")
        if messagebox.askyesno("Confirmar", "¿Eliminar el registro seleccionado?"):
            self._delete(self._sel_id)

    def _open_form(self, item): pass
    def _delete(self, id_): pass


# ── Clientes ──────────────────────────────────────────────────────────────────
class ClientesPanel(CrudPanel):
    TITLE = "👥  Clientes"
    COLUMNS = ["ID", "Tipo", "RUC/CI", "Razón Social", "Teléfono", "Email", "Ciudad", "Estado"]
    COL_WIDTHS = [50, 80, 120, 220, 120, 180, 110, 80]

    def _insert_row(self, c):
        self.tree.insert("", "end", values=(
            c["id"], c.get("tipo_contribuyente", ""),
            c.get("ruc_ci", ""), c["razon_social"],
            c.get("telefono", ""), c.get("email", ""),
            c.get("ciudad", ""), "✓ Activo" if c.get("activo") else "✗"))

    def load(self):
        def do():
            try:
                data = client.get("/clientes").json()
                self._items = data if isinstance(data, list) else []
                self.after(0, self._refresh)
            except Exception as e:
                self.after(0, lambda: toast(self, str(e), False))
        threading.Thread(target=do, daemon=True).start()

    def _refresh(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for c in self._items: self._insert_row(c)
        apply_zebra(self.tree)

    def _open_form(self, item): ClienteForm(self, item, on_save=self.load)

    def _delete(self, id_):
        def do():
            try:
                client.delete(f"/clientes/{id_}")
                self.after(0, self.load)
                self.after(0, lambda: toast(self, "Cliente eliminado"))
            except Exception as e:
                self.after(0, lambda: toast(self, str(e), False))
        threading.Thread(target=do, daemon=True).start()


class ClienteForm(ctk.CTkToplevel):
    def __init__(self, parent, item, on_save):
        super().__init__(parent)
        self.item = item; self.on_save = on_save
        self.title("Cliente")
        self.geometry("500x420")
        self.resizable(False, False)
        self.configure(fg_color=C["bg"])
        self.grab_set()
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="✏️  Editar Cliente" if self.item else "➕  Nuevo Cliente",
                     font=("Segoe UI", 16, "bold"), text_color=C["text"]).pack(pady=(20, 8))
        form = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=12)
        form.pack(fill="both", expand=True, padx=20, pady=4)
        form.grid_columnconfigure(1, weight=1)
        v = self.item or {}
        self.tipo  = field(form, "Tipo *", 0, choices=["RUC","CI","PASAPORTE","EXTRANJERO"],
                           default=v.get("tipo_contribuyente","RUC"))
        self.ruc   = field(form, "RUC / CI", 1, default=v.get("ruc_ci",""))
        self.razon = field(form, "Razón Social *", 2, wide=True, default=v.get("razon_social",""))
        self.tel   = field(form, "Teléfono", 3, default=v.get("telefono",""))
        self.email = field(form, "Email", 4, default=v.get("email",""))
        self.dir   = field(form, "Dirección", 5, wide=True, default=v.get("direccion",""))
        self.ciudad= field(form, "Ciudad", 6, default=v.get("ciudad","Asunción"))
        bbar = ctk.CTkFrame(self, fg_color="transparent")
        bbar.pack(fill="x", padx=20, pady=10)
        btn(bbar, "Guardar", self._save, C["accent"], "💾").pack(side="right", padx=4)
        btn(bbar, "Cancelar", self.destroy, C["card"]).pack(side="right", padx=4)

    def _save(self):
        if not self.razon.get():
            return messagebox.showerror("Error", "Razón Social es obligatorio")
        payload = {
            "tipo_contribuyente": self.tipo.get(),
            "ruc_ci": self.ruc.get() or None,
            "razon_social": self.razon.get(),
            "telefono": self.tel.get() or None,
            "email": self.email.get() or None,
            "direccion": self.dir.get() or "Sin dirección",
            "ciudad": self.ciudad.get() or None,
        }
        def do():
            try:
                if self.item:
                    r = client.put(f"/clientes/{self.item['id']}", json=payload)
                else:
                    r = client.post("/clientes", json=payload)
                if r.status_code in (200, 201):
                    self.after(0, lambda: (self.on_save(), self.destroy()))
                else:
                    msg = r.json().get("detail", r.text)
                    self.after(0, lambda: messagebox.showerror("Error", str(msg)))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=do, daemon=True).start()


# ── Productos ─────────────────────────────────────────────────────────────────
class ProductosPanel(CrudPanel):
    TITLE = "📦  Productos"
    COLUMNS = ["ID", "Código", "Descripción", "Precio", "IVA", "Unidad", "Estado"]
    COL_WIDTHS = [50, 110, 240, 130, 60, 90, 70]

    def _insert_row(self, p):
        self.tree.insert("", "end", values=(
            p["id"], p["codigo"], p["descripcion"],
            gs(p["precio_unitario"]),
            f"{p['tasa_iva']}%",
            p.get("unidad_medida",""),
            "✓" if p.get("activo") else "✗"))

    def load(self):
        def do():
            try:
                data = client.get("/productos").json()
                self._items = data if isinstance(data, list) else []
                self.after(0, self._refresh)
            except Exception as e:
                self.after(0, lambda: toast(self, str(e), False))
        threading.Thread(target=do, daemon=True).start()

    def _refresh(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for p in self._items: self._insert_row(p)
        apply_zebra(self.tree)

    def _open_form(self, item): ProductoForm(self, item, on_save=self.load)

    def _delete(self, id_):
        def do():
            try:
                client.delete(f"/productos/{id_}")
                self.after(0, self.load)
                self.after(0, lambda: toast(self, "Producto eliminado"))
            except Exception as e:
                self.after(0, lambda: toast(self, str(e), False))
        threading.Thread(target=do, daemon=True).start()


class ProductoForm(ctk.CTkToplevel):
    def __init__(self, parent, item, on_save):
        super().__init__(parent)
        self.item = item; self.on_save = on_save
        self.title("Producto")
        self.geometry("460x380")
        self.resizable(False, False)
        self.configure(fg_color=C["bg"])
        self.grab_set()
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="✏️  Editar Producto" if self.item else "➕  Nuevo Producto",
                     font=("Segoe UI", 16, "bold"), text_color=C["text"]).pack(pady=(20, 8))
        form = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=12)
        form.pack(fill="both", expand=True, padx=20, pady=4)
        form.grid_columnconfigure(1, weight=1)
        v = self.item or {}
        self.codigo = field(form, "Código *", 0, default=v.get("codigo",""))
        self.desc   = field(form, "Descripción *", 1, wide=True, default=v.get("descripcion",""))
        self.precio = field(form, "Precio *", 2, default=str(int(float(v.get("precio_unitario",0)))) if v else "")
        self.iva    = field(form, "IVA %", 3, choices=["10","5","0"],
                            default=str(v.get("tasa_iva","10")))
        self.unidad = field(form, "Unidad", 4, choices=["UNIDAD","KG","LITRO","CAJA","METRO"],
                            default=v.get("unidad_medida","UNIDAD"))
        bbar = ctk.CTkFrame(self, fg_color="transparent")
        bbar.pack(fill="x", padx=20, pady=10)
        btn(bbar, "Guardar", self._save, C["accent"], "💾").pack(side="right", padx=4)
        btn(bbar, "Cancelar", self.destroy, C["card"]).pack(side="right", padx=4)

    def _save(self):
        if not self.codigo.get() or not self.desc.get():
            return messagebox.showerror("Error", "Código y Descripción son obligatorios")
        try:
            precio = float(self.precio.get().replace(".","").replace(",","."))
        except ValueError:
            return messagebox.showerror("Error", "Precio inválido")
        payload = {
            "codigo": self.codigo.get(),
            "descripcion": self.desc.get(),
            "precio_unitario": precio,
            "tasa_iva": self.iva.get(),
            "unidad_medida": self.unidad.get(),
        }
        def do():
            try:
                if self.item:
                    r = client.put(f"/productos/{self.item['id']}", json=payload)
                else:
                    r = client.post("/productos", json=payload)
                if r.status_code in (200, 201):
                    self.after(0, lambda: (self.on_save(), self.destroy()))
                else:
                    msg = r.json().get("detail", r.text)
                    self.after(0, lambda: messagebox.showerror("Error", str(msg)))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=do, daemon=True).start()


# ── Facturas ──────────────────────────────────────────────────────────────────
class FacturasPanel(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=C["bg"])
        self._items = []
        self._sel_id = None
        self._build()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 4))
        ctk.CTkLabel(hdr, text="📄  Facturas",
                     font=("Segoe UI", 22, "bold"), text_color=C["text"]).pack(side="left")

        tb = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=10, height=52)
        tb.pack(fill="x", padx=24, pady=4)
        tb.pack_propagate(False)
        btn(tb, "Nueva", self._nueva, C["accent"], "➕").pack(side="left", padx=12, pady=8)
        btn(tb, "Emitir", self._emitir, C["success"], "✅").pack(side="left", padx=4)
        btn(tb, "PDF", self._pdf, C["accent2"], "📄").pack(side="left", padx=4)
        btn(tb, "Anular", self._anular, C["danger"], "❌").pack(side="left", padx=4)
        btn(tb, "↺", self.load, C["card"]).pack(side="right", padx=12)

        cols = ["ID","Número","Fecha","Cliente ID","Total","IVA","Condición","Estado"]
        widths = [50,150,100,90,140,110,100,120]
        tf, self.tree = make_table(self, cols, widths)
        tf.pack(fill="both", expand=True, padx=24, pady=(4,8))
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.load()

    def _on_select(self, e):
        sel = self.tree.selection()
        if sel:
            self._sel_id = self.tree.item(sel[0])["values"][0]

    def load(self):
        def do():
            try:
                data = client.get("/facturas").json()
                self._items = data if isinstance(data, list) else []
                self.after(0, self._refresh)
            except Exception as e:
                self.after(0, lambda: toast(self, str(e), False))
        threading.Thread(target=do, daemon=True).start()

    def _refresh(self):
        icons = {"BORRADOR":"📝","EMITIDA":"✅","ANULADA":"❌","PAGADA":"💰"}
        for i in self.tree.get_children(): self.tree.delete(i)
        for f in self._items:
            estado = f.get("estado","")
            self.tree.insert("", "end", values=(
                f["id"], f.get("numero_completo") or "—",
                f["fecha_emision"], f["cliente_id"],
                gs(f["total"]), gs(f["total_iva"]),
                f.get("condicion_venta",""),
                f"{icons.get(estado,'')} {estado}"))
        apply_zebra(self.tree)

    def _nueva(self): FacturaForm(self, on_save=self.load)

    def _emitir(self):
        if not self._sel_id: return messagebox.showinfo("Aviso","Seleccione una factura")
        item = next((i for i in self._items if i["id"] == self._sel_id), None)
        if item and item.get("estado") != "BORRADOR":
            return messagebox.showinfo("Aviso","Solo se pueden emitir facturas en BORRADOR")
        def do():
            try:
                r = client.post(f"/facturas/{self._sel_id}/emitir")
                if r.status_code == 200:
                    num = r.json().get("numero_completo","")
                    self.after(0, lambda: (self.load(), toast(self, f"Emitida: {num}")))
                else:
                    msg = r.json().get("detail", r.text)
                    self.after(0, lambda: messagebox.showerror("Error", str(msg)))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=do, daemon=True).start()

    def _anular(self):
        if not self._sel_id: return messagebox.showinfo("Aviso","Seleccione una factura")
        if not messagebox.askyesno("Confirmar","¿Anular factura?"): return
        def do():
            try:
                r = client.post(f"/facturas/{self._sel_id}/anular")
                if r.status_code == 200:
                    self.after(0, lambda: (self.load(), toast(self, "Factura anulada")))
                else:
                    msg = r.json().get("detail", r.text)
                    self.after(0, lambda: messagebox.showerror("Error", str(msg)))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=do, daemon=True).start()

    def _pdf(self):
        if not self._sel_id: return messagebox.showinfo("Aviso","Seleccione una factura")
        import os
        def do():
            try:
                r = client.get(f"/facturas/{self._sel_id}/pdf")
                if r.status_code == 200:
                    path = f"data/facturas/factura_{self._sel_id}.pdf"
                    with open(path,"wb") as f: f.write(r.content)
                    os.startfile(path)
                else:
                    self.after(0, lambda: messagebox.showerror("Error", r.text))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=do, daemon=True).start()


class FacturaForm(ctk.CTkToplevel):
    def __init__(self, parent, on_save):
        super().__init__(parent)
        self.on_save = on_save
        self.title("Nueva Factura")
        self.geometry("720x620")
        self.configure(fg_color=C["bg"])
        self.grab_set()
        self._clientes = []
        self._productos = []
        self._detalles = []
        self._build()
        threading.Thread(target=self._load_data, daemon=True).start()

    def _build(self):
        ctk.CTkLabel(self, text="➕  Nueva Factura",
                     font=("Segoe UI", 16, "bold"), text_color=C["text"]).pack(pady=(16,4))

        top = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=12)
        top.pack(fill="x", padx=16, pady=4)
        top.grid_columnconfigure(1, weight=1)
        top.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(top, text="Cliente *", text_color=C["muted"],
                     font=("Segoe UI",11)).grid(row=0, column=0, padx=12, pady=8, sticky="w")
        self.cli_var = ctk.StringVar()
        self.cli_menu = ctk.CTkOptionMenu(top, variable=self.cli_var,
                                           values=["Cargando..."], width=280,
                                           fg_color=C["card"], button_color=C["accent2"],
                                           font=("Segoe UI",11))
        self.cli_menu.grid(row=0, column=1, padx=4, pady=8, sticky="ew")

        self.cond  = field(top, "Condición", 0, col=1, choices=["CONTADO","CREDITO"])
        self.fecha = field(top, "Fecha", 1, col=0, default=str(date.today()))
        self.obs   = field(top, "Observación", 1, col=1, default="")

        ctk.CTkLabel(self, text="  Ítems",
                     font=("Segoe UI",13,"bold"), text_color=C["text"]).pack(anchor="w", padx=16)

        add = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=10)
        add.pack(fill="x", padx=16, pady=4)

        ctk.CTkLabel(add, text="Producto", text_color=C["muted"],
                     font=("Segoe UI",11)).grid(row=0, column=0, padx=8, pady=8)
        self.prod_var = ctk.StringVar()
        self.prod_menu = ctk.CTkOptionMenu(add, variable=self.prod_var,
                                            values=["Cargando..."], width=220,
                                            fg_color=C["card"], button_color=C["accent2"],
                                            font=("Segoe UI",11))
        self.prod_menu.grid(row=0, column=1, padx=4)

        ctk.CTkLabel(add, text="Cant.", text_color=C["muted"],
                     font=("Segoe UI",11)).grid(row=0, column=2, padx=4)
        self.cant = ctk.CTkEntry(add, width=60, fg_color=C["card"], font=("Segoe UI",11))
        self.cant.insert(0,"1")
        self.cant.grid(row=0, column=3, padx=4)

        ctk.CTkLabel(add, text="Precio", text_color=C["muted"],
                     font=("Segoe UI",11)).grid(row=0, column=4, padx=4)
        self.precio_ent = ctk.CTkEntry(add, width=110, fg_color=C["card"], font=("Segoe UI",11))
        self.precio_ent.grid(row=0, column=5, padx=4)

        btn(add, "Agregar", self._agregar, C["success"], "➕").grid(row=0, column=6, padx=8)

        cols = ["#","Descripción","Cant.","Precio","IVA%","Total"]
        widths = [30,240,60,120,60,130]
        tf, self.items_tree = make_table(self, cols, widths)
        tf.pack(fill="both", expand=True, padx=16, pady=4)
        self.items_tree.bind("<Delete>", lambda e: self._quitar())

        bot = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=10)
        bot.pack(fill="x", padx=16, pady=4)
        self.total_lbl = ctk.CTkLabel(bot, text="Total: Gs 0",
                                       font=("Segoe UI",14,"bold"), text_color=C["success"])
        self.total_lbl.pack(side="right", padx=16, pady=8)
        ctk.CTkLabel(bot, text="Presione Delete para quitar un ítem",
                     text_color=C["muted"], font=("Segoe UI",10)).pack(side="left", padx=16)

        bbar = ctk.CTkFrame(self, fg_color="transparent")
        bbar.pack(fill="x", padx=16, pady=8)
        btn(bbar, "Guardar Borrador", self._save, C["accent"], "💾").pack(side="right", padx=4)
        btn(bbar, "Cancelar", self.destroy, C["card"]).pack(side="right", padx=4)

    def _load_data(self):
        try:
            self._clientes = client.get("/clientes").json()
            self._productos = client.get("/productos").json()
            cli_opts  = [f"{c['id']} - {c['razon_social']}" for c in self._clientes]
            prod_opts = [f"{p['id']} - {p['descripcion']}" for p in self._productos]
            self.after(0, lambda: self.cli_menu.configure(values=cli_opts or ["Sin clientes"]))
            self.after(0, lambda: self.prod_menu.configure(values=prod_opts or ["Sin productos"]))
            if cli_opts:  self.after(0, lambda: self.cli_var.set(cli_opts[0]))
            if prod_opts:
                self.after(0, lambda: self.prod_var.set(prod_opts[0]))
                p0 = self._productos[0]
                self.after(0, lambda: (self.precio_ent.delete(0,"end"),
                                       self.precio_ent.insert(0, str(int(float(p0["precio_unitario"]))))))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))

    def _agregar(self):
        ps = self.prod_var.get()
        if not ps or ps in ("Cargando...","Sin productos"): return
        pid = int(ps.split(" - ")[0])
        prod = next((p for p in self._productos if p["id"] == pid), None)
        if not prod: return
        try:
            cant  = float(self.cant.get())
            precio = float(self.precio_ent.get().replace(".","").replace(",","."))
        except ValueError:
            return messagebox.showerror("Error","Cantidad/precio inválido")

        total = cant * precio
        self._detalles.append({
            "orden": len(self._detalles)+1,
            "producto_id": pid,
            "descripcion": prod["descripcion"],
            "cantidad": cant,
            "precio_unitario": precio,
            "tasa_iva": prod["tasa_iva"],
        })
        self.items_tree.insert("", "end", values=(
            len(self._detalles), prod["descripcion"],
            int(cant), gs(precio), f"{prod['tasa_iva']}%", gs(total)))
        apply_zebra(self.items_tree)
        self._recalc()

    def _quitar(self):
        sel = self.items_tree.selection()
        if not sel: return
        idx = self.items_tree.index(sel[0])
        self.items_tree.delete(sel[0])
        self._detalles.pop(idx)
        self._recalc()

    def _recalc(self):
        total = sum(d["cantidad"] * d["precio_unitario"] for d in self._detalles)
        self.total_lbl.configure(text=f"Total: {gs(total)}")

    def _save(self):
        if not self._detalles: return messagebox.showerror("Error","Agregue al menos un ítem")
        cs = self.cli_var.get()
        if not cs or cs in ("Cargando...","Sin clientes"): return messagebox.showerror("Error","Seleccione cliente")
        payload = {
            "fecha_emision": self.fecha.get(),
            "cliente_id": int(cs.split(" - ")[0]),
            "condicion_venta": self.cond.get(),
            "observacion": self.obs.get() or None,
            "detalles": self._detalles,
        }
        def do():
            try:
                r = client.post("/facturas", json=payload)
                if r.status_code == 201:
                    self.after(0, lambda: (self.on_save(), self.destroy()))
                else:
                    msg = r.json().get("detail", r.text)
                    self.after(0, lambda: messagebox.showerror("Error", str(msg)))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=do, daemon=True).start()


# ── Proveedores ───────────────────────────────────────────────────────────────
class ProveedoresPanel(CrudPanel):
    TITLE = "🏭  Proveedores"
    COLUMNS = ["Código","RUC","Razón Social","Teléfono","Email","Ciudad"]
    COL_WIDTHS = [80,130,240,120,180,120]

    def _insert_row(self, p):
        self.tree.insert("", "end", values=(
            p.get("prov_cod",""), p.get("prov_ruc",""),
            p.get("prov_nombre",""), p.get("prov_telefono",""),
            p.get("prov_email",""), p.get("prov_ciudad","")))

    def load(self):
        def do():
            try:
                data = client.get("/proveedores").json()
                self._items = data if isinstance(data, list) else []
                self.after(0, self._refresh)
            except Exception as e:
                self.after(0, lambda: toast(self, str(e), False))
        threading.Thread(target=do, daemon=True).start()

    def _refresh(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for p in self._items: self._insert_row(p)
        apply_zebra(self.tree)

    def _open_form(self, item): ProveedorForm(self, item, on_save=self.load)


class ProveedorForm(ctk.CTkToplevel):
    def __init__(self, parent, item, on_save):
        super().__init__(parent)
        self.item = item; self.on_save = on_save
        self.title("Proveedor")
        self.geometry("480x380")
        self.resizable(False, False)
        self.configure(fg_color=C["bg"])
        self.grab_set()
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="✏️  Proveedor" if self.item else "➕  Nuevo Proveedor",
                     font=("Segoe UI",16,"bold"), text_color=C["text"]).pack(pady=(20,8))
        form = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=12)
        form.pack(fill="both", expand=True, padx=20, pady=4)
        form.grid_columnconfigure(1, weight=1)
        v = self.item or {}
        self.cod    = field(form,"Código *",   0, default=v.get("prov_cod",""))
        self.ruc    = field(form,"RUC",        1, default=v.get("prov_ruc",""))
        self.nombre = field(form,"Nombre *",   2, wide=True, default=v.get("prov_nombre",""))
        self.tel    = field(form,"Teléfono",   3, default=v.get("prov_telefono",""))
        self.email  = field(form,"Email",      4, default=v.get("prov_email",""))
        self.ciudad = field(form,"Ciudad",     5, default=v.get("prov_ciudad",""))
        bbar = ctk.CTkFrame(self, fg_color="transparent")
        bbar.pack(fill="x", padx=20, pady=10)
        btn(bbar,"Guardar",self._save,C["accent"],"💾").pack(side="right",padx=4)
        btn(bbar,"Cancelar",self.destroy,C["card"]).pack(side="right",padx=4)

    def _save(self):
        if not self.cod.get() or not self.nombre.get():
            return messagebox.showerror("Error","Código y Nombre son obligatorios")
        payload = {
            "prov_cod": self.cod.get(), "prov_ruc": self.ruc.get() or None,
            "prov_nombre": self.nombre.get(), "prov_telefono": self.tel.get() or None,
            "prov_email": self.email.get() or None, "prov_ciudad": self.ciudad.get() or None,
        }
        def do():
            try:
                if self.item:
                    r = client.put(f"/proveedores/{self.item['prov_cod']}", json=payload)
                else:
                    r = client.post("/proveedores", json=payload)
                if r.status_code in (200,201):
                    self.after(0, lambda: (self.on_save(), self.destroy()))
                else:
                    msg = r.json().get("detail", r.text)
                    self.after(0, lambda: messagebox.showerror("Error", str(msg)))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=do, daemon=True).start()


# ── Compras ───────────────────────────────────────────────────────────────────
class ComprasPanel(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=C["bg"])
        self._build()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20,4))
        ctk.CTkLabel(hdr, text="🛒  Compras",
                     font=("Segoe UI",22,"bold"), text_color=C["text"]).pack(side="left")

        tb = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=10, height=52)
        tb.pack(fill="x", padx=24, pady=4)
        tb.pack_propagate(False)
        btn(tb,"↺",self.load,C["card"]).pack(side="right",padx=12)

        cols = ["Nro","Fecha","Proveedor","Total","Estado"]
        widths = [80,110,250,140,110]
        tf, self.tree = make_table(self, cols, widths)
        tf.pack(fill="both", expand=True, padx=24, pady=(4,8))
        self.load()

    def load(self):
        def do():
            try:
                data = client.get("/compras").json()
                items = data if isinstance(data,list) else []
                self.after(0, lambda: self._refresh(items))
            except Exception as e:
                self.after(0, lambda: toast(self, str(e), False))
        threading.Thread(target=do, daemon=True).start()

    def _refresh(self, items):
        for i in self.tree.get_children(): self.tree.delete(i)
        for c in items:
            self.tree.insert("","end", values=(
                c.get("com_nro",""), c.get("com_fecha",""),
                c.get("com_proveedor",""),
                gs(c.get("com_total",0)), c.get("com_estado","")))
        apply_zebra(self.tree)


# ── Caja ──────────────────────────────────────────────────────────────────────
class CajaPanel(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=C["bg"])
        self._caja = None
        self._build()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20,4))
        ctk.CTkLabel(hdr, text="💰  Caja",
                     font=("Segoe UI",22,"bold"), text_color=C["text"]).pack(side="left")

        card = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=12)
        card.pack(fill="x", padx=24, pady=8)

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=12)
        self.estado_lbl = ctk.CTkLabel(top, text="⏳ Cargando...",
                                        font=("Segoe UI",16,"bold"), text_color=C["text"])
        self.estado_lbl.pack(side="left")
        bbar = ctk.CTkFrame(top, fg_color="transparent")
        bbar.pack(side="right")
        btn(bbar,"Abrir Caja",  self._abrir,  C["success"],"🔓").pack(side="left",padx=4)
        btn(bbar,"Cerrar Caja", self._cerrar, C["danger"], "🔒").pack(side="left",padx=4)
        btn(bbar,"↺",           self.load,    C["card"]).pack(side="left",padx=4)

        metrics = ctk.CTkFrame(card, fg_color="transparent")
        metrics.pack(fill="x", padx=16, pady=(0,12))
        self.m = {}
        defs = [("Saldo Inicial",C["muted"]),("Ingresos",C["success"]),
                ("Egresos",C["danger"]),("Saldo Final",C["accent"])]
        for i,(lbl,color) in enumerate(defs):
            f = ctk.CTkFrame(metrics, fg_color=C["card"], corner_radius=8)
            f.grid(row=0, column=i, padx=6, sticky="ew")
            metrics.grid_columnconfigure(i, weight=1)
            ctk.CTkLabel(f, text=lbl, text_color=C["muted"], font=("Segoe UI",10)).pack(pady=(8,0))
            v = ctk.CTkLabel(f, text="Gs 0", text_color=color, font=("Segoe UI",14,"bold"))
            v.pack(pady=(0,8))
            self.m[lbl] = v

        mv = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=12)
        mv.pack(fill="x", padx=24, pady=4)
        ctk.CTkLabel(mv, text="Registrar Movimiento",
                     font=("Segoe UI",13,"bold"), text_color=C["text"]).pack(anchor="w",padx=16,pady=(12,4))

        row = ctk.CTkFrame(mv, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(0,12))

        ctk.CTkLabel(row,text="Tipo",text_color=C["muted"],font=("Segoe UI",11)).pack(side="left",padx=(0,4))
        self.mv_tipo = ctk.StringVar(value="INGRESO")
        ctk.CTkOptionMenu(row,variable=self.mv_tipo,values=["INGRESO","EGRESO"],
                          width=120,fg_color=C["card"],button_color=C["accent2"],
                          font=("Segoe UI",11)).pack(side="left",padx=4)

        ctk.CTkLabel(row,text="Monto Gs",text_color=C["muted"],font=("Segoe UI",11)).pack(side="left",padx=(8,4))
        self.mv_monto = ctk.CTkEntry(row,width=120,fg_color=C["card"],font=("Segoe UI",11))
        self.mv_monto.pack(side="left",padx=4)

        ctk.CTkLabel(row,text="Concepto",text_color=C["muted"],font=("Segoe UI",11)).pack(side="left",padx=(8,4))
        self.mv_concepto = ctk.CTkEntry(row,width=220,fg_color=C["card"],font=("Segoe UI",11))
        self.mv_concepto.pack(side="left",padx=4)

        btn(row,"Registrar",self._movimiento,C["accent"],"✓").pack(side="left",padx=8)
        self.load()

    def load(self):
        def do():
            try:
                r = client.get("/caja/hoy")
                if r.status_code == 200:
                    self._caja = r.json()
                    self.after(0, self._refresh)
                else:
                    self._caja = None
                    self.after(0, lambda: self.estado_lbl.configure(
                        text="🔴 Caja cerrada — no hay caja abierta hoy", text_color=C["danger"]))
            except Exception as e:
                self.after(0, lambda: toast(self, str(e), False))
        threading.Thread(target=do, daemon=True).start()

    def _refresh(self):
        if not self._caja: return
        cerrada = self._caja.get("caj_cerrada", False)
        estado  = "🔴 Cerrada" if cerrada else "🟢 Abierta"
        color   = C["danger"] if cerrada else C["success"]
        fecha   = self._caja.get("caj_fecha","")
        self.estado_lbl.configure(text=f"{estado} — {fecha}", text_color=color)
        self.m["Saldo Inicial"].configure(text=gs(self._caja.get("caj_saldoinicial",0)))
        self.m["Ingresos"].configure(text=gs(self._caja.get("caj_totalingre",0)))
        self.m["Egresos"].configure(text=gs(self._caja.get("caj_totalegre",0)))
        self.m["Saldo Final"].configure(text=gs(self._caja.get("caj_saldofinal",0)))

    def _abrir(self): AbrirCajaDialog(self, on_done=self.load)

    def _cerrar(self):
        if not messagebox.askyesno("Confirmar","¿Cerrar la caja de hoy?"): return
        def do():
            try:
                r = client.post("/caja/cerrar")
                if r.status_code == 200:
                    self.after(0, lambda: (self.load(), toast(self,"Caja cerrada")))
                else:
                    msg = r.json().get("detail", r.text)
                    self.after(0, lambda: messagebox.showerror("Error", str(msg)))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=do, daemon=True).start()

    def _movimiento(self):
        try:
            monto = float(self.mv_monto.get().replace(".","").replace(",","."))
        except ValueError:
            return messagebox.showerror("Error","Monto inválido")
        payload = {"tipo": self.mv_tipo.get(), "monto": monto,
                   "concepto": self.mv_concepto.get() or "Sin concepto"}
        def do():
            try:
                r = client.post("/caja/movimiento", json=payload)
                if r.status_code == 200:
                    self.after(0, lambda: (self.load(), toast(self,"Movimiento registrado")))
                else:
                    msg = r.json().get("detail", r.text)
                    self.after(0, lambda: messagebox.showerror("Error", str(msg)))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=do, daemon=True).start()


class AbrirCajaDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_done):
        super().__init__(parent)
        self.on_done = on_done
        self.title("Abrir Caja")
        self.geometry("360x240")
        self.resizable(False, False)
        self.configure(fg_color=C["bg"])
        self.grab_set()
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="🔓  Abrir Caja del Día",
                     font=("Segoe UI",16,"bold"), text_color=C["text"]).pack(pady=(24,12))
        form = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=12)
        form.pack(fill="x", padx=20, pady=4)
        form.grid_columnconfigure(1, weight=1)
        self.usuario = field(form,"Usuario",0,default="admin")
        self.saldo   = field(form,"Saldo Inicial Gs",1,default="0")
        bbar = ctk.CTkFrame(self, fg_color="transparent")
        bbar.pack(fill="x", padx=20, pady=12)
        btn(bbar,"Abrir",self._abrir,C["success"],"🔓").pack(side="right",padx=4)
        btn(bbar,"Cancelar",self.destroy,C["card"]).pack(side="right",padx=4)

    def _abrir(self):
        try:
            saldo = float(self.saldo.get().replace(".","").replace(",","."))
        except ValueError:
            saldo = 0
        payload = {"caj_usuario": self.usuario.get() or "admin", "saldo_inicial": saldo}
        def do():
            try:
                r = client.post("/caja/abrir", json=payload)
                if r.status_code == 200:
                    self.after(0, lambda: (self.on_done(), self.destroy()))
                else:
                    msg = r.json().get("detail", r.text)
                    self.after(0, lambda: messagebox.showerror("Error", str(msg)))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=do, daemon=True).start()


# ── Reportes ──────────────────────────────────────────────────────────────────
class ReportesPanel(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=C["bg"])
        self._build()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20,4))
        ctk.CTkLabel(hdr, text="📈  Reportes",
                     font=("Segoe UI",22,"bold"), text_color=C["text"]).pack(side="left")

        filtros = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=12)
        filtros.pack(fill="x", padx=24, pady=8)
        row = ctk.CTkFrame(filtros, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(row,text="Desde:",text_color=C["muted"],font=("Segoe UI",11)).pack(side="left",padx=(0,4))
        self.desde = ctk.CTkEntry(row,width=110,fg_color=C["card"],font=("Segoe UI",11))
        self.desde.insert(0,f"{date.today().year}-01-01")
        self.desde.pack(side="left",padx=4)

        ctk.CTkLabel(row,text="Hasta:",text_color=C["muted"],font=("Segoe UI",11)).pack(side="left",padx=(8,4))
        self.hasta = ctk.CTkEntry(row,width=110,fg_color=C["card"],font=("Segoe UI",11))
        self.hasta.insert(0,str(date.today()))
        self.hasta.pack(side="left",padx=4)

        btn(row,"Ventas período",  self._ventas,      C["accent"],  "📊").pack(side="left",padx=8)
        btn(row,"IVA Mensual",     self._iva,          C["accent2"], "📋").pack(side="left",padx=4)
        btn(row,"Más Vendidos",    self._mas_vendidos, C["success"], "🏆").pack(side="left",padx=4)
        btn(row,"Deudores",        self._deudores,     C["warning"], "⚠️").pack(side="left",padx=4)

        self.result_lbl = ctk.CTkLabel(self, text="",
                                        font=("Segoe UI",13,"bold"), text_color=C["text"])
        self.result_lbl.pack(anchor="w", padx=24, pady=(8,0))

        cols = ["Concepto","Valor 1","Valor 2","Valor 3"]
        widths = [320,160,160,160]
        tf, self.tree = make_table(self, cols, widths)
        tf.pack(fill="both", expand=True, padx=24, pady=(4,16))

    def _clear(self):
        for i in self.tree.get_children(): self.tree.delete(i)

    def _show(self, data, title):
        self._clear()
        self.result_lbl.configure(text=title)
        if isinstance(data, list):
            for item in data:
                vals = list(item.values()) if isinstance(item,dict) else [item,"","",""]
                while len(vals) < 4: vals.append("")
                self.tree.insert("","end", values=tuple(str(v) for v in vals[:4]))
        elif isinstance(data, dict):
            for k,v in data.items():
                self.tree.insert("","end", values=(k,v,"",""))
        apply_zebra(self.tree)

    def _ventas(self):
        def do():
            try:
                r = client.get("/reportes/ventas-periodo",
                               params={"desde":self.desde.get(),"hasta":self.hasta.get()})
                self.after(0, lambda: self._show(r.json(),"📊 Ventas por Período"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error",str(e)))
        threading.Thread(target=do,daemon=True).start()

    def _iva(self):
        def do():
            try:
                mes = self.desde.get()[:7]
                r = client.get("/reportes/iva-mensual", params={"mes":mes})
                self.after(0, lambda: self._show(r.json(),"📋 IVA Mensual"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error",str(e)))
        threading.Thread(target=do,daemon=True).start()

    def _mas_vendidos(self):
        def do():
            try:
                r = client.get("/reportes/productos-mas-vendidos",
                               params={"desde":self.desde.get(),"hasta":self.hasta.get()})
                self.after(0, lambda: self._show(r.json(),"🏆 Más Vendidos"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error",str(e)))
        threading.Thread(target=do,daemon=True).start()

    def _deudores(self):
        def do():
            try:
                r = client.get("/reportes/clientes-deudores")
                self.after(0, lambda: self._show(r.json(),"⚠️ Clientes Deudores"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error",str(e)))
        threading.Thread(target=do,daemon=True).start()


# ── App Principal ─────────────────────────────────────────────────────────────
PANELS = {
    "Dashboard":   DashboardPanel,
    "Facturas":    FacturasPanel,
    "Clientes":    ClientesPanel,
    "Productos":   ProductosPanel,
    "Proveedores": ProveedoresPanel,
    "Compras":     ComprasPanel,
    "Caja":        CajaPanel,
    "Reportes":    ReportesPanel,
}


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Facturación Paraguay")
        self.geometry("1280x760")
        self.minsize(1024,640)
        self.configure(fg_color=C["bg"])
        self._cache = {}
        self._current = None
        self._show_login()

    def _show_login(self):
        self._login_frame = LoginScreen(self, on_success=self._show_main)
        self._login_frame.pack(fill="both", expand=True)

    def _show_main(self):
        self._login_frame.destroy()

        self._sidebar = Sidebar(self, on_select=self._navigate)
        self._sidebar.pack(side="left", fill="y")
        ctk.CTkFrame(self, fg_color=C["border"], width=1).pack(side="left", fill="y")

        content = ctk.CTkFrame(self, fg_color=C["bg"])
        content.pack(side="left", fill="both", expand=True)

        topbar = ctk.CTkFrame(content, fg_color=C["panel"], corner_radius=0, height=46)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)
        ctk.CTkLabel(topbar, text="Sistema de Facturación Paraguay",
                     font=("Segoe UI",12), text_color=C["muted"]).pack(side="left",padx=16)
        ctk.CTkLabel(topbar, text="● Conectado",
                     font=("Segoe UI",11), text_color=C["success"]).pack(side="right",padx=16)

        self._area = ctk.CTkFrame(content, fg_color=C["bg"])
        self._area.pack(fill="both", expand=True)

        self._sidebar.select("Dashboard")

    def _navigate(self, name):
        if self._current:
            self._current.pack_forget()
        if name not in self._cache:
            self._cache[name] = PANELS[name](self._area)
        self._current = self._cache[name]
        self._current.pack(fill="both", expand=True)
