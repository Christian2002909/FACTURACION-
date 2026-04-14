"""
GUI moderna — FacturaPY — Sistema de Gestión Comercial
CustomTkinter · modo claro · colores CV TechStore
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading
import json
import os
import subprocess
import platform
from datetime import date, datetime
from decimal import Decimal

# ── Configuración global ──────────────────────────────────────────────────────
API = "http://localhost:8000/api/v1"
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

C = {
    "bg":        "#F4F6F9",
    "panel":     "#FFFFFF",
    "sidebar":   "#1B2A4A",
    "header":    "#1B2A4A",
    "accent":    "#1565C0",
    "accent2":   "#29ABE2",
    "text":      "#1B2A4A",
    "text_inv":  "#FFFFFF",
    "muted":     "#607D8B",
    "success":   "#2E7D32",
    "warning":   "#F57F17",
    "danger":    "#C62828",
    "border":    "#E0E7EF",
    "row_even":  "#F8FAFC",
    "row_odd":   "#FFFFFF",
    "sel":       "#1565C0",
    "input_bg":  "#F4F6F9",
}


# ── Cliente HTTP ──────────────────────────────────────────────────────────────
class APIClient:
    def __init__(self):
        self.token = None
        self.username = "admin"
        self.s = requests.Session()

    def login(self, username, password):
        r = self.s.post(f"{API}/auth/login",
                        json={"username": username, "password": password}, timeout=5)
        if r.status_code == 200:
            self.token = r.json()["access_token"]
            self.username = username
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


# ── Print config helpers ─────────────────────────────────────────────────────
PRINT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "print_config.json")

def load_print_config():
    try:
        with open(PRINT_CONFIG_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {"print_mode": "ask", "printer_type": "a4"}

def save_print_config(config):
    os.makedirs(os.path.dirname(PRINT_CONFIG_PATH), exist_ok=True)
    with open(PRINT_CONFIG_PATH, "w") as f:
        json.dump(config, f)


def print_factura(factura_id, printer_type="a4"):
    """Descarga el PDF de la factura y lo envía a imprimir."""
    try:
        r = client.get(f"/facturas/{factura_id}/pdf")
        if r.status_code != 200:
            messagebox.showerror("Error", "No se pudo obtener el PDF de la factura")
            return False

        os.makedirs("data/facturas", exist_ok=True)
        pdf_path = os.path.join("data", "facturas", f"factura_{factura_id}.pdf")
        with open(pdf_path, "wb") as f:
            f.write(r.content)

        if platform.system() == "Windows":
            os.startfile(pdf_path, "print")
        else:
            subprocess.run(["lp", pdf_path], check=True)

        return True
    except Exception as e:
        messagebox.showerror("Error de impresión", f"No se pudo imprimir: {str(e)}")
        return False


# ── Logo helper ──────────────────────────────────────────────────────────────
def _load_logo(width, height):
    """Carga el logo desde app/assets/LOGO-CV.jpg con PIL, retorna CTkImage o None."""
    try:
        from PIL import Image
        logo_paths = [
            os.path.join(os.path.dirname(__file__), "..", "assets", "LOGO-CV.jpg"),
            os.path.join("app", "assets", "LOGO-CV.jpg"),
            "LOGO-CV.jpg",
        ]
        for p in logo_paths:
            if os.path.exists(p):
                img = Image.open(p)
                return ctk.CTkImage(light_image=img, dark_image=img, size=(width, height))
    except Exception:
        pass
    return None


# ── Helpers ───────────────────────────────────────────────────────────────────
def make_table(parent, columns, col_widths=None):
    frame = ctk.CTkFrame(parent, fg_color=C["panel"], corner_radius=10,
                         border_width=1, border_color=C["border"])
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Light.Treeview",
                    background=C["row_odd"], foreground=C["text"],
                    fieldbackground=C["row_odd"], rowheight=32,
                    borderwidth=0, font=("Segoe UI", 11))
    style.configure("Light.Treeview.Heading",
                    background=C["header"], foreground=C["text_inv"],
                    font=("Segoe UI", 11, "bold"), borderwidth=0, relief="flat")
    style.map("Light.Treeview",
              background=[("selected", C["sel"])],
              foreground=[("selected", "#ffffff")])
    style.map("Light.Treeview.Heading",
              background=[("active", C["accent"])])

    tree = ttk.Treeview(frame, columns=columns, show="headings",
                        style="Light.Treeview", selectmode="browse")
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
                               fg_color=C["input_bg"], button_color=C["accent"],
                               text_color=C["text"],
                               font=("Segoe UI", 11))
        w.grid(row=row, column=col * 2 + 1, sticky="ew", pady=5,
               columnspan=3 if wide else 1, padx=(0, 12))
        return var
    else:
        var = ctk.StringVar(value=default or "")
        e = ctk.CTkEntry(parent, textvariable=var,
                         width=420 if wide else 200,
                         fg_color=C["input_bg"], border_color=C["border"],
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
    hover = C["header"] if color == C["accent"] else C["accent"]
    return ctk.CTkButton(parent, text=f"{icon}  {text}" if icon else text,
                         command=cmd, fg_color=color, hover_color=hover,
                         text_color=C["text_inv"],
                         font=("Segoe UI", 12, "bold"),
                         corner_radius=8, height=36)


def gs(val):
    try:
        n = int(float(val or 0))
        return f"Gs. {n:,}".replace(",", ".")
    except Exception:
        return "Gs. 0"


def format_gs_input(var, widget=None):
    """Formatea automáticamente un campo de entrada de guaraníes con puntos de miles."""
    def _format(*args):
        val = var.get().replace(".", "").replace(",", "")
        if val.isdigit() and len(val) > 0:
            formatted = f"{int(val):,}".replace(",", ".")
            var.set(formatted)
            if widget:
                widget.icursor("end")
    return _format


def unformat_gs(s):
    """Quita puntos de miles de un string formateado: '1.000.000' -> '1000000'."""
    return s.replace(".", "").replace(",", ".")


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
                            width=420, height=540, border_width=1, border_color=C["border"])
        card.grid(row=0, column=0)
        card.grid_propagate(False)

        # Logo
        logo_img = _load_logo(180, 60)
        if logo_img:
            ctk.CTkLabel(card, image=logo_img, text="").pack(pady=(36, 8))
        else:
            ctk.CTkLabel(card, text="CV TechStore",
                         font=("Segoe UI", 18, "bold"),
                         text_color=C["accent"]).pack(pady=(36, 8))

        ctk.CTkLabel(card, text="FacturaPY",
                     font=("Segoe UI", 26, "bold"),
                     text_color=C["text"]).pack(pady=(4, 0))
        ctk.CTkLabel(card, text="Sistema de Gestión Comercial",
                     font=("Segoe UI", 12), text_color=C["muted"]).pack(pady=(2, 4))
        ctk.CTkLabel(card, text="v1.0 · Paraguay 2026",
                     font=("Segoe UI", 10), text_color=C["muted"]).pack(pady=(0, 20))

        ctk.CTkFrame(card, fg_color=C["border"], height=1).pack(fill="x", padx=40)

        self.user = ctk.CTkEntry(card, placeholder_text="Usuario",
                                  width=300, height=44,
                                  fg_color=C["input_bg"], border_color=C["border"],
                                  text_color=C["text"], font=("Segoe UI", 13))
        self.user.pack(pady=(20, 6))
        self.user.insert(0, "admin")

        self.pw = ctk.CTkEntry(card, placeholder_text="Contraseña",
                                show="•", width=300, height=44,
                                fg_color=C["input_bg"], border_color=C["border"],
                                text_color=C["text"], font=("Segoe UI", 13))
        self.pw.pack(pady=6)

        self.err = ctk.CTkLabel(card, text="", text_color=C["danger"],
                                 font=("Segoe UI", 11))
        self.err.pack(pady=4)

        self.login_btn = ctk.CTkButton(card, text="Iniciar Sesión",
                                        command=self._login,
                                        width=300, height=44,
                                        fg_color=C["accent"], hover_color=C["header"],
                                        text_color=C["text_inv"],
                                        font=("Segoe UI", 13, "bold"), corner_radius=10)
        self.login_btn.pack(pady=8)
        self.pw.bind("<Return>", lambda e: self._login())

    def _login(self):
        self.login_btn.configure(state="disabled", text="Verificando...")
        self.err.configure(text="")
        threading.Thread(target=lambda: self._do_login(), daemon=True).start()

    def _do_login(self):
        try:
            ok = client.login(self.user.get(), self.pw.get())
            self.after(0, lambda: self._result(ok))
        except Exception:
            self.after(0, lambda: self._result(False))

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
    ("⚙️", "Configuración"),
]


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, on_select):
        super().__init__(master, fg_color=C["sidebar"], width=220, corner_radius=0)
        self.on_select = on_select
        self._btns = {}
        self._active = None
        self._build()

    def _build(self):
        self.pack_propagate(False)

        # Logo area at top
        logo_frame = ctk.CTkFrame(self, fg_color=C["sidebar"], corner_radius=0, height=64)
        logo_frame.pack(fill="x")
        logo_frame.pack_propagate(False)
        logo_img = _load_logo(120, 40)
        if logo_img:
            ctk.CTkLabel(logo_frame, image=logo_img, text="").pack(expand=True)
        else:
            ctk.CTkLabel(logo_frame, text="CV TechStore",
                         font=("Segoe UI", 13, "bold"),
                         text_color=C["text_inv"]).pack(expand=True)

        ctk.CTkFrame(self, fg_color="#2A3E66", height=1).pack(fill="x")
        ctk.CTkLabel(self, text="  MENÚ PRINCIPAL", text_color="#8899B3",
                     font=("Segoe UI", 9, "bold")).pack(pady=(16, 4), anchor="w")

        for icon, name in MENU:
            b = ctk.CTkButton(self, text=f"  {icon}  {name}", anchor="w",
                               height=44, fg_color="transparent",
                               hover_color=C["accent2"], text_color="#B0BEC5",
                               font=("Segoe UI", 12), corner_radius=6,
                               command=lambda n=name: self.select(n))
            b.pack(fill="x", padx=8, pady=2)
            self._btns[name] = b

        ctk.CTkFrame(self, fg_color="transparent").pack(fill="both", expand=True)
        ctk.CTkLabel(self, text="FacturaPY v1.0",
                     text_color="#8899B3", font=("Segoe UI", 9)).pack(pady=12)

    def select(self, name):
        if self._active:
            self._btns[self._active].configure(fg_color="transparent",
                                                text_color="#B0BEC5")
        self._active = name
        self._btns[name].configure(fg_color=C["accent"], text_color=C["text_inv"])
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
            card = ctk.CTkFrame(cards_frame, fg_color=C["panel"], corner_radius=12,
                                border_width=1, border_color=C["border"])
            card.grid(row=0, column=i, padx=8, sticky="ew")
            cards_frame.grid_columnconfigure(i, weight=1)
            ctk.CTkLabel(card, text=icon, font=("Segoe UI", 30),
                         text_color=C["text"]).pack(pady=(16, 0))
            v = ctk.CTkLabel(card, text=val, font=("Segoe UI", 18, "bold"),
                             text_color=color)
            v.pack()
            ctk.CTkLabel(card, text=lbl, font=("Segoe UI", 10),
                         text_color=C["muted"]).pack(pady=(0, 14))
            self.m[lbl] = v

        info = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=12,
                            border_width=1, border_color=C["border"])
        info.pack(fill="both", expand=True, padx=24, pady=16)
        ctk.CTkLabel(info, text="FacturaPY — Sistema de Gestión Comercial",
                     font=("Segoe UI", 18, "bold"), text_color=C["text"]).pack(pady=(28, 4))
        ctk.CTkLabel(info,
                     text="Gestión completa de facturas, clientes, productos, caja y reportes.",
                     font=("Segoe UI", 12), text_color=C["muted"]).pack()
        ctk.CTkLabel(info,
                     text="✓ Factura electrónica SIFEN  ·  ✓ PDF automático  ·  ✓ IVA 5% y 10%  ·  ✓ Modo Claro",
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

        tb = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=10, height=52,
                          border_width=1, border_color=C["border"])
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
                     width=240, height=34, fg_color=C["input_bg"], border_color=C["border"],
                     text_color=C["text"],
                     font=("Segoe UI", 12)).pack(side="left", padx=12, pady=8)
        btn(tb, "Nuevo", self._on_new, C["accent"], "➕").pack(side="left", padx=4)
        btn(tb, "Editar", self._on_edit, C["accent2"], "✏️").pack(side="left", padx=4)
        btn(tb, "Eliminar", self._on_delete, C["danger"], "🗑️").pack(side="left", padx=4)
        btn(tb, "↺ Actualizar", self.load, C["border"]).pack(side="right", padx=12)

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
        form = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=12,
                            border_width=1, border_color=C["border"])
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
        btn(bbar, "Cancelar", self.destroy, C["border"]).pack(side="right", padx=4)

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
        form = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=12,
                            border_width=1, border_color=C["border"])
        form.pack(fill="both", expand=True, padx=20, pady=4)
        form.grid_columnconfigure(1, weight=1)
        v = self.item or {}
        self.codigo = field(form, "Código *", 0, default=v.get("codigo",""))
        self.desc   = field(form, "Descripción *", 1, wide=True, default=v.get("descripcion",""))
        self.precio = field(form, "Precio *", 2, default=str(int(float(v.get("precio_unitario",0)))) if v else "")
        self._precio_formatter = format_gs_input(self.precio)
        self.precio.trace_add("write", self._precio_formatter)
        if self.precio.get():
            self._precio_formatter()
        self.iva    = field(form, "IVA %", 3, choices=["10","5","0"],
                            default=str(v.get("tasa_iva","10")))
        self.unidad = field(form, "Unidad", 4, choices=["UNIDAD","KG","LITRO","CAJA","METRO"],
                            default=v.get("unidad_medida","UNIDAD"))
        bbar = ctk.CTkFrame(self, fg_color="transparent")
        bbar.pack(fill="x", padx=20, pady=10)
        btn(bbar, "Guardar", self._save, C["accent"], "💾").pack(side="right", padx=4)
        btn(bbar, "Cancelar", self.destroy, C["border"]).pack(side="right", padx=4)

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

        tb = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=10, height=52,
                          border_width=1, border_color=C["border"])
        tb.pack(fill="x", padx=24, pady=4)
        tb.pack_propagate(False)
        btn(tb, "Nueva Factura", self._nueva, C["accent"], "➕").pack(side="left", padx=12, pady=8)
        btn(tb, "PDF", self._pdf, C["accent2"], "📄").pack(side="left", padx=4)
        btn(tb, "Imprimir", self._imprimir, C["accent"], "🖨️").pack(side="left", padx=4)
        btn(tb, "Anular", self._anular, C["danger"], "❌").pack(side="left", padx=4)
        btn(tb, "↺", self.load, C["border"]).pack(side="right", padx=12)

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
        def do():
            try:
                r = client.get(f"/facturas/{self._sel_id}/pdf")
                if r.status_code == 200:
                    path = f"data/facturas/factura_{self._sel_id}.pdf"
                    os.makedirs("data/facturas", exist_ok=True)
                    with open(path,"wb") as f: f.write(r.content)
                    try:
                        os.startfile(path)
                    except AttributeError:
                        import subprocess
                        subprocess.Popen(["xdg-open", path])
                else:
                    self.after(0, lambda: messagebox.showerror("Error", r.text))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=do, daemon=True).start()

    def _imprimir(self):
        if not self._sel_id:
            return messagebox.showinfo("Aviso", "Seleccione una factura")
        config = load_print_config()
        print_factura(self._sel_id, config["printer_type"])


# ── FacturaForm — Nueva factura con doble modo de carga ──────────────────────
class FacturaForm(ctk.CTkToplevel):
    def __init__(self, parent, on_save, edit_data=None):
        super().__init__(parent)
        self.on_save = on_save
        self.edit_data = edit_data
        self.title("Nueva Factura")
        self.geometry("800x680")
        self.configure(fg_color=C["bg"])
        self.grab_set()
        self._clientes = []
        self._productos = []
        self._detalles = []
        self._modo_ocasional = False
        if edit_data and edit_data.get("detalles"):
            self._detalles = list(edit_data["detalles"])
        self._build()
        threading.Thread(target=self._load_data, daemon=True).start()

    def _build(self):
        ctk.CTkLabel(self, text="➕  Nueva Factura",
                     font=("Segoe UI", 16, "bold"), text_color=C["text"]).pack(pady=(12,4))

        # ── Header: Cliente y condición ──
        top = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=12,
                           border_width=1, border_color=C["border"])
        top.pack(fill="x", padx=16, pady=4)
        top.grid_columnconfigure(1, weight=1)
        top.grid_columnconfigure(3, weight=1)

        # ── Cliente: toggle BD / Ocasional ──
        cli_row = ctk.CTkFrame(top, fg_color="transparent")
        cli_row.grid(row=0, column=0, columnspan=2, sticky="ew", padx=12, pady=8)

        ctk.CTkLabel(cli_row, text="Cliente *", text_color=C["muted"],
                     font=("Segoe UI",11)).pack(side="left", padx=(0,8))

        self._cli_toggle_btn = ctk.CTkButton(
            cli_row, text="🔍 Desde BD", width=120,
            fg_color=C["accent"], hover_color=C["accent2"],
            text_color=C["text_inv"], font=("Segoe UI", 10, "bold"),
            command=self._toggle_cliente_modo)
        self._cli_toggle_btn.pack(side="left", padx=(0,8))

        # Frame BD mode
        self._cli_bd_frame = ctk.CTkFrame(cli_row, fg_color="transparent")
        self._cli_bd_frame.pack(side="left", fill="x", expand=True)
        self.cli_var = ctk.StringVar()
        self.cli_menu = ctk.CTkOptionMenu(self._cli_bd_frame, variable=self.cli_var,
                                           values=["Cargando..."], width=280,
                                           fg_color=C["input_bg"], button_color=C["accent"],
                                           text_color=C["text"],
                                           font=("Segoe UI",11))
        self.cli_menu.pack(side="left", fill="x", expand=True)

        # Frame Ocasional mode (hidden initially)
        self._cli_ocas_frame = ctk.CTkFrame(cli_row, fg_color="transparent")
        ctk.CTkLabel(self._cli_ocas_frame, text="RUC/CI:", text_color=C["muted"],
                     font=("Segoe UI",10)).pack(side="left", padx=(0,2))
        self.cli_ruc_var = ctk.StringVar()
        self._cli_ruc_entry = ctk.CTkEntry(self._cli_ocas_frame, textvariable=self.cli_ruc_var,
                                            width=120, fg_color=C["input_bg"],
                                            text_color=C["text"], font=("Segoe UI",11),
                                            placeholder_text="Ej: 3.456.789-0")
        self._cli_ruc_entry.pack(side="left", padx=2)
        self.cli_ruc_var.trace_add("write", self._format_ruc)

        ctk.CTkLabel(self._cli_ocas_frame, text="Nombre:", text_color=C["muted"],
                     font=("Segoe UI",10)).pack(side="left", padx=(6,2))
        self.cli_nombre_var = ctk.StringVar()
        ctk.CTkEntry(self._cli_ocas_frame, textvariable=self.cli_nombre_var,
                     width=160, fg_color=C["input_bg"],
                     text_color=C["text"], font=("Segoe UI",11),
                     placeholder_text="Razón Social").pack(side="left", padx=2)

        self.cond  = field(top, "Condición", 0, col=1, choices=["CONTADO","CREDITO"])
        self.fecha = field(top, "Fecha", 1, col=0, default=str(date.today()))
        self.obs   = field(top, "Observación", 1, col=1, default="")

        # ── Tabs: Modo Base de Datos / Modo Manual ──
        ctk.CTkLabel(self, text="  Agregar Ítems",
                     font=("Segoe UI",13,"bold"), text_color=C["text"]).pack(anchor="w", padx=16, pady=(4,0))

        tab_frame = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=10,
                                 border_width=1, border_color=C["border"])
        tab_frame.pack(fill="x", padx=16, pady=4)

        # Tab buttons
        tab_bar = ctk.CTkFrame(tab_frame, fg_color=C["border"], height=36)
        tab_bar.pack(fill="x")
        tab_bar.pack_propagate(False)
        self._tab_db_btn = ctk.CTkButton(tab_bar, text="📦 Desde Base de Datos",
                                          fg_color=C["accent"], text_color=C["text_inv"],
                                          hover_color=C["accent2"],
                                          font=("Segoe UI", 11, "bold"),
                                          corner_radius=0, height=36,
                                          command=lambda: self._switch_tab("db"))
        self._tab_db_btn.pack(side="left", padx=(0,1))
        self._tab_manual_btn = ctk.CTkButton(tab_bar, text="✏️ Carga Manual",
                                              fg_color=C["panel"], text_color=C["text"],
                                              hover_color=C["accent2"],
                                              font=("Segoe UI", 11),
                                              corner_radius=0, height=36,
                                              command=lambda: self._switch_tab("manual"))
        self._tab_manual_btn.pack(side="left")

        # Tab content: Database mode
        self._tab_db = ctk.CTkFrame(tab_frame, fg_color=C["panel"])
        self._tab_db.pack(fill="x", padx=8, pady=8)

        db_row = ctk.CTkFrame(self._tab_db, fg_color="transparent")
        db_row.pack(fill="x")

        ctk.CTkLabel(db_row, text="Producto", text_color=C["muted"],
                     font=("Segoe UI",11)).pack(side="left", padx=(0,4))
        self.prod_var = ctk.StringVar()
        self.prod_menu = ctk.CTkOptionMenu(db_row, variable=self.prod_var,
                                            values=["Cargando..."], width=260,
                                            fg_color=C["input_bg"], button_color=C["accent"],
                                            text_color=C["text"],
                                            font=("Segoe UI",11),
                                            command=self._on_prod_select)
        self.prod_menu.pack(side="left", padx=4)

        ctk.CTkLabel(db_row, text="Cant.", text_color=C["muted"],
                     font=("Segoe UI",11)).pack(side="left", padx=4)
        self.cant_db = ctk.CTkEntry(db_row, width=60, fg_color=C["input_bg"],
                                     text_color=C["text"], font=("Segoe UI",11))
        self.cant_db.insert(0,"1")
        self.cant_db.pack(side="left", padx=4)

        ctk.CTkLabel(db_row, text="Precio", text_color=C["muted"],
                     font=("Segoe UI",11)).pack(side="left", padx=4)
        self._precio_db_var = ctk.StringVar()
        self.precio_db = ctk.CTkEntry(db_row, textvariable=self._precio_db_var,
                                       width=110, fg_color=C["input_bg"],
                                       text_color=C["text"], font=("Segoe UI",11))
        self.precio_db.pack(side="left", padx=4)
        self._precio_db_var.trace_add("write", format_gs_input(self._precio_db_var, self.precio_db))

        btn(db_row, "Agregar", self._agregar_db, C["success"], "➕").pack(side="left", padx=8)

        # Tab content: Manual mode
        self._tab_manual = ctk.CTkFrame(tab_frame, fg_color=C["panel"])

        man_row = ctk.CTkFrame(self._tab_manual, fg_color="transparent")
        man_row.pack(fill="x")

        ctk.CTkLabel(man_row, text="Descripción", text_color=C["muted"],
                     font=("Segoe UI",11)).pack(side="left", padx=(0,4))
        self.desc_manual = ctk.CTkEntry(man_row, width=200, fg_color=C["input_bg"],
                                         text_color=C["text"], font=("Segoe UI",11))
        self.desc_manual.pack(side="left", padx=4)

        ctk.CTkLabel(man_row, text="Precio", text_color=C["muted"],
                     font=("Segoe UI",11)).pack(side="left", padx=4)
        self._precio_manual_var = ctk.StringVar()
        self.precio_manual = ctk.CTkEntry(man_row, textvariable=self._precio_manual_var,
                                           width=100, fg_color=C["input_bg"],
                                           text_color=C["text"], font=("Segoe UI",11))
        self.precio_manual.pack(side="left", padx=4)
        self._precio_manual_var.trace_add("write", format_gs_input(self._precio_manual_var, self.precio_manual))

        ctk.CTkLabel(man_row, text="Cant.", text_color=C["muted"],
                     font=("Segoe UI",11)).pack(side="left", padx=4)
        self.cant_manual = ctk.CTkEntry(man_row, width=50, fg_color=C["input_bg"],
                                         text_color=C["text"], font=("Segoe UI",11))
        self.cant_manual.insert(0, "1")
        self.cant_manual.pack(side="left", padx=4)

        ctk.CTkLabel(man_row, text="IVA%", text_color=C["muted"],
                     font=("Segoe UI",11)).pack(side="left", padx=4)
        self.iva_manual = ctk.StringVar(value="10")
        ctk.CTkOptionMenu(man_row, variable=self.iva_manual, values=["10","5","0"],
                          width=60, fg_color=C["input_bg"], button_color=C["accent"],
                          text_color=C["text"],
                          font=("Segoe UI",11)).pack(side="left", padx=4)

        btn(man_row, "Agregar", self._agregar_manual, C["success"], "➕").pack(side="left", padx=8)

        # ── Items table ──
        cols = ["#","Descripción","Cant.","Precio","IVA%","Total"]
        widths = [30,240,60,120,60,130]
        tf, self.items_tree = make_table(self, cols, widths)
        tf.pack(fill="both", expand=True, padx=16, pady=4)
        self.items_tree.bind("<Delete>", lambda e: self._quitar())

        # ── Totals bar ──
        bot = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=10,
                           border_width=1, border_color=C["border"])
        bot.pack(fill="x", padx=16, pady=4)
        self.total_lbl = ctk.CTkLabel(bot, text="Total: Gs. 0",
                                       font=("Segoe UI",14,"bold"), text_color=C["success"])
        self.total_lbl.pack(side="right", padx=16, pady=8)
        ctk.CTkLabel(bot, text="Presione Delete para quitar un ítem",
                     text_color=C["muted"], font=("Segoe UI",10)).pack(side="left", padx=16)

        # ── Bottom buttons ──
        bbar = ctk.CTkFrame(self, fg_color="transparent")
        bbar.pack(fill="x", padx=16, pady=8)
        btn(bbar, "Vista Previa", self._vista_previa, C["accent"], "👁️").pack(side="right", padx=4)
        btn(bbar, "Cancelar", self.destroy, C["border"]).pack(side="right", padx=4)

        # Pre-fill if editing
        if self.edit_data:
            self._prefill_edit()

    def _switch_tab(self, tab):
        if tab == "db":
            self._tab_manual.pack_forget()
            self._tab_db.pack(fill="x", padx=8, pady=8)
            self._tab_db_btn.configure(fg_color=C["accent"], text_color=C["text_inv"],
                                        font=("Segoe UI", 11, "bold"))
            self._tab_manual_btn.configure(fg_color=C["panel"], text_color=C["text"],
                                            font=("Segoe UI", 11))
        else:
            self._tab_db.pack_forget()
            self._tab_manual.pack(fill="x", padx=8, pady=8)
            self._tab_manual_btn.configure(fg_color=C["accent"], text_color=C["text_inv"],
                                            font=("Segoe UI", 11, "bold"))
            self._tab_db_btn.configure(fg_color=C["panel"], text_color=C["text"],
                                        font=("Segoe UI", 11))

    def _toggle_cliente_modo(self):
        self._modo_ocasional = not self._modo_ocasional
        if self._modo_ocasional:
            self._cli_bd_frame.pack_forget()
            self._cli_ocas_frame.pack(side="left", fill="x", expand=True)
            self._cli_toggle_btn.configure(text="✏️ Ocasional", fg_color=C["warning"])
        else:
            self._cli_ocas_frame.pack_forget()
            self._cli_bd_frame.pack(side="left", fill="x", expand=True)
            self._cli_toggle_btn.configure(text="🔍 Desde BD", fg_color=C["accent"])

    def _format_ruc(self, *args):
        # RUC paraguayo: solo numeros y guion — sin formato de puntos
        pass

    def _get_cliente_ocasional_id(self):
        """Get client ID for occasional client: CONSUMIDOR FINAL or first available."""
        for c in self._clientes:
            if "CONSUMIDOR FINAL" in (c.get("razon_social", "") or "").upper():
                return c["id"]
        if self._clientes:
            return self._clientes[0]["id"]
        return None

    def _prefill_edit(self):
        d = self.edit_data
        if d.get("fecha_emision"):
            self.fecha.set(d["fecha_emision"])
        if d.get("condicion_venta"):
            self.cond.set(d["condicion_venta"])
        if d.get("observacion"):
            self.obs.set(d["observacion"])
        # Detalles are already in self._detalles
        self._refresh_items()

    def _load_data(self):
        try:
            self._clientes = client.get("/clientes").json()
            self._productos = client.get("/productos").json()
            cli_opts  = [f"{c['id']} - {c['razon_social']}" for c in self._clientes]
            prod_opts = [f"{p['id']} - {p['descripcion']}" for p in self._productos]
            self.after(0, lambda: self.cli_menu.configure(values=cli_opts or ["Sin clientes"]))
            self.after(0, lambda: self.prod_menu.configure(values=prod_opts or ["Sin productos"]))
            if cli_opts:
                if self.edit_data and self.edit_data.get("cliente_id"):
                    cid = self.edit_data["cliente_id"]
                    match = next((o for o in cli_opts if o.startswith(f"{cid} -")), cli_opts[0])
                    self.after(0, lambda: self.cli_var.set(match))
                else:
                    self.after(0, lambda: self.cli_var.set(cli_opts[0]))
            if prod_opts:
                self.after(0, lambda: self.prod_var.set(prod_opts[0]))
                p0 = self._productos[0]
                self.after(0, lambda: self._precio_db_var.set(str(int(float(p0["precio_unitario"])))))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))

    def _on_prod_select(self, choice):
        try:
            pid = int(choice.split(" - ")[0])
            prod = next((p for p in self._productos if p["id"] == pid), None)
            if prod:
                self._precio_db_var.set(str(int(float(prod["precio_unitario"]))))
        except Exception:
            pass

    def _agregar_db(self):
        ps = self.prod_var.get()
        if not ps or ps in ("Cargando...","Sin productos"): return
        pid = int(ps.split(" - ")[0])
        prod = next((p for p in self._productos if p["id"] == pid), None)
        if not prod: return
        try:
            cant  = float(self.cant_db.get())
            precio = float(self.precio_db.get().replace(".","").replace(",","."))
        except ValueError:
            return messagebox.showerror("Error","Cantidad/precio inválido")

        self._detalles.append({
            "orden": len(self._detalles)+1,
            "producto_id": pid,
            "descripcion": prod["descripcion"],
            "cantidad": cant,
            "precio_unitario": precio,
            "tasa_iva": prod["tasa_iva"],
        })
        self._refresh_items()

    def _agregar_manual(self):
        desc = self.desc_manual.get().strip()
        if not desc:
            return messagebox.showerror("Error", "Ingrese una descripción")
        try:
            cant  = float(self.cant_manual.get())
            precio = float(self.precio_manual.get().replace(".","").replace(",","."))
        except ValueError:
            return messagebox.showerror("Error","Cantidad/precio inválido")

        self._detalles.append({
            "orden": len(self._detalles)+1,
            "producto_id": None,
            "descripcion": desc,
            "cantidad": cant,
            "precio_unitario": precio,
            "tasa_iva": str(self.iva_manual.get()),
        })
        self._refresh_items()
        self.desc_manual.delete(0, "end")
        self._precio_manual_var.set("")

    def _refresh_items(self):
        for i in self.items_tree.get_children():
            self.items_tree.delete(i)
        for idx, d in enumerate(self._detalles):
            total = d["cantidad"] * d["precio_unitario"]
            self.items_tree.insert("", "end", values=(
                idx+1, d["descripcion"],
                int(d["cantidad"]), gs(d["precio_unitario"]),
                f"{d['tasa_iva']}%", gs(total)))
        apply_zebra(self.items_tree)
        self._recalc()

    def _quitar(self):
        sel = self.items_tree.selection()
        if not sel: return
        idx = self.items_tree.index(sel[0])
        self._detalles.pop(idx)
        self._refresh_items()

    def _recalc(self):
        total = sum(d["cantidad"] * d["precio_unitario"] for d in self._detalles)
        self.total_lbl.configure(text=f"Total: {gs(total)}")

    def _vista_previa(self):
        """Save as draft then open preview."""
        if not self._detalles:
            return messagebox.showerror("Error","Agregue al menos un ítem")

        if self._modo_ocasional:
            ruc = self.cli_ruc_var.get().strip()
            nombre = self.cli_nombre_var.get().strip()
            if not ruc or not nombre:
                return messagebox.showerror("Error","Ingrese RUC/CI y Nombre del cliente ocasional")
            cid = self._get_cliente_ocasional_id()
            if cid is None:
                return messagebox.showerror("Error","No hay clientes disponibles en la base de datos")
            obs_base = self.obs.get() or ""
            obs_ocas = f"[Cliente Ocasional] RUC: {ruc} | Nombre: {nombre}"
            observacion = f"{obs_ocas} | {obs_base}" if obs_base else obs_ocas
            cli_name = f"{nombre} (RUC: {ruc})"
        else:
            cs = self.cli_var.get()
            if not cs or cs in ("Cargando...","Sin clientes"):
                return messagebox.showerror("Error","Seleccione cliente")
            cid = int(cs.split(" - ")[0])
            observacion = self.obs.get() or None
            cli_name = cs.split(" - ", 1)[1] if " - " in cs else "—"

        payload = {
            "fecha_emision": self.fecha.get(),
            "cliente_id": cid,
            "condicion_venta": self.cond.get(),
            "observacion": observacion,
            "detalles": self._detalles,
        }
        def do():
            try:
                if self.edit_data and self.edit_data.get("id"):
                    r = client.put(f"/facturas/{self.edit_data['id']}", json=payload)
                else:
                    r = client.post("/facturas", json=payload)
                if r.status_code in (200, 201):
                    factura_data = r.json()
                    self.after(0, lambda: self._open_preview(factura_data, cli_name))
                else:
                    msg = r.json().get("detail", r.text)
                    self.after(0, lambda: messagebox.showerror("Error", str(msg)))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=do, daemon=True).start()

    def _open_preview(self, factura_data, cli_name):
        VistaPreviewFactura(self, factura_data, cli_name,
                            on_emitir_done=lambda: (self.on_save(), self.destroy()),
                            on_edit=lambda data: self._return_to_edit(data))

    def _return_to_edit(self, data):
        # Update edit data and reload detalles
        self.edit_data = data
        if data.get("detalles"):
            self._detalles = list(data["detalles"])
            self._refresh_items()


# ── Vista Previa de Factura ──────────────────────────────────────────────────
class VistaPreviewFactura(ctk.CTkToplevel):
    def __init__(self, parent, factura, cli_name, on_emitir_done, on_edit):
        super().__init__(parent)
        self.factura = factura
        self.cli_name = cli_name
        self.on_emitir_done = on_emitir_done
        self.on_edit = on_edit
        self.title("Vista Previa — Factura")
        self.geometry("700x650")
        self.configure(fg_color=C["bg"])
        self.grab_set()
        self._build()

    def _build(self):
        # Scrollable content
        scroll = ctk.CTkScrollableFrame(self, fg_color=C["bg"])
        scroll.pack(fill="both", expand=True, padx=16, pady=(8, 4))

        # ── Company header ──
        header = ctk.CTkFrame(scroll, fg_color=C["header"], corner_radius=10)
        header.pack(fill="x", pady=(0, 8))
        h_inner = ctk.CTkFrame(header, fg_color="transparent")
        h_inner.pack(fill="x", padx=16, pady=12)
        logo_img = _load_logo(100, 33)
        if logo_img:
            ctk.CTkLabel(h_inner, image=logo_img, text="").pack(side="left")
        ctk.CTkLabel(h_inner, text="  FACTURA", font=("Segoe UI", 18, "bold"),
                     text_color=C["text_inv"]).pack(side="left", padx=8)

        estado = self.factura.get("estado", "BORRADOR")
        estado_color = C["warning"] if estado == "BORRADOR" else C["success"]
        ctk.CTkLabel(h_inner, text=f"  {estado}  ", font=("Segoe UI", 11, "bold"),
                     fg_color=estado_color, text_color=C["text_inv"],
                     corner_radius=6).pack(side="right")

        # ── Factura info ──
        info = ctk.CTkFrame(scroll, fg_color=C["panel"], corner_radius=10,
                            border_width=1, border_color=C["border"])
        info.pack(fill="x", pady=4)
        info.grid_columnconfigure((0,1,2,3), weight=1)

        num = self.factura.get("numero_completo") or "Pendiente"
        pairs = [
            ("Número:", num),
            ("Fecha:", self.factura.get("fecha_emision", "—")),
            ("Cliente:", self.cli_name),
            ("Condición:", self.factura.get("condicion_venta", "—")),
        ]
        for i, (lbl, val) in enumerate(pairs):
            r, c = divmod(i, 2)
            ctk.CTkLabel(info, text=lbl, text_color=C["muted"],
                         font=("Segoe UI", 10)).grid(row=r, column=c*2, padx=(12,4), pady=6, sticky="w")
            ctk.CTkLabel(info, text=val, text_color=C["text"],
                         font=("Segoe UI", 11, "bold")).grid(row=r, column=c*2+1, padx=(0,12), pady=6, sticky="w")

        # ── Items table ──
        items_frame = ctk.CTkFrame(scroll, fg_color=C["panel"], corner_radius=10,
                                   border_width=1, border_color=C["border"])
        items_frame.pack(fill="x", pady=4)

        ctk.CTkLabel(items_frame, text="Detalle de Ítems", font=("Segoe UI", 12, "bold"),
                     text_color=C["text"]).pack(anchor="w", padx=12, pady=(8,4))

        # Table header
        th = ctk.CTkFrame(items_frame, fg_color=C["header"], corner_radius=0)
        th.pack(fill="x", padx=8)
        cols_def = [("#", 30), ("Descripción", 220), ("Cant.", 50), ("P. Unit.", 100),
                    ("IVA%", 50), ("Subtotal", 110)]
        for label, w in cols_def:
            ctk.CTkLabel(th, text=label, text_color=C["text_inv"],
                         font=("Segoe UI", 10, "bold"), width=w).pack(side="left", padx=4, pady=4)

        # Table rows
        detalles = self.factura.get("detalles", [])
        for i, d in enumerate(detalles):
            bg = C["row_even"] if i % 2 == 0 else C["row_odd"]
            row = ctk.CTkFrame(items_frame, fg_color=bg, corner_radius=0)
            row.pack(fill="x", padx=8)
            total_l = float(d.get("total_linea", 0) or (d.get("cantidad",0) * d.get("precio_unitario",0)))
            vals = [
                (str(d.get("orden", i+1)), 30),
                (d.get("descripcion",""), 220),
                (str(int(float(d.get("cantidad",0)))), 50),
                (gs(d.get("precio_unitario",0)), 100),
                (f"{d.get('tasa_iva',10)}%", 50),
                (gs(total_l), 110),
            ]
            for val, w in vals:
                ctk.CTkLabel(row, text=val, text_color=C["text"],
                             font=("Segoe UI", 10), width=w).pack(side="left", padx=4, pady=3)

        # ── Totals ──
        totals = ctk.CTkFrame(scroll, fg_color=C["panel"], corner_radius=10,
                              border_width=1, border_color=C["border"])
        totals.pack(fill="x", pady=4)
        totals.grid_columnconfigure(1, weight=1)

        total_rows = [
            ("Subtotal Exenta:", gs(self.factura.get("subtotal_exenta", 0))),
            ("Subtotal Gravada 5%:", gs(self.factura.get("subtotal_gravada_5", 0))),
            ("Subtotal Gravada 10%:", gs(self.factura.get("subtotal_gravada_10", 0))),
            ("IVA 5%:", gs(self.factura.get("iva_5", 0))),
            ("IVA 10%:", gs(self.factura.get("iva_10", 0))),
            ("Total IVA:", gs(self.factura.get("total_iva", 0))),
        ]
        for r, (lbl, val) in enumerate(total_rows):
            ctk.CTkLabel(totals, text=lbl, text_color=C["muted"],
                         font=("Segoe UI", 10)).grid(row=r, column=0, padx=12, pady=2, sticky="e")
            ctk.CTkLabel(totals, text=val, text_color=C["text"],
                         font=("Segoe UI", 10, "bold")).grid(row=r, column=1, padx=12, pady=2, sticky="e")

        # Grand total
        gt = ctk.CTkFrame(totals, fg_color=C["accent"], corner_radius=6)
        gt.grid(row=len(total_rows), column=0, columnspan=2, sticky="ew", padx=8, pady=(8,12))
        ctk.CTkLabel(gt, text=f"TOTAL:  {gs(self.factura.get('total', 0))}",
                     text_color=C["text_inv"],
                     font=("Segoe UI", 16, "bold")).pack(pady=8)

        # ── Buttons ──
        bbar = ctk.CTkFrame(self, fg_color="transparent")
        bbar.pack(fill="x", padx=16, pady=8)

        emitir_btn = ctk.CTkButton(bbar, text="✅  Emitir Factura",
                                    command=self._emitir,
                                    fg_color=C["accent"], hover_color=C["header"],
                                    text_color=C["text_inv"],
                                    font=("Segoe UI", 14, "bold"),
                                    corner_radius=8, height=44, width=200)
        emitir_btn.pack(side="right", padx=4)

        btn(bbar, "✏️ Editar", self._editar, C["accent2"]).pack(side="right", padx=4)
        btn(bbar, "❌ Cancelar", self._cancelar, C["danger"]).pack(side="right", padx=4)

    def _emitir(self):
        fid = self.factura.get("id")
        if not fid: return
        def do():
            try:
                r = client.post(f"/facturas/{fid}/emitir")
                if r.status_code == 200:
                    num = r.json().get("numero_completo","")
                    self.after(0, lambda: self._emision_ok(num))
                else:
                    msg = r.json().get("detail", r.text)
                    self.after(0, lambda: messagebox.showerror("Error", str(msg)))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=do, daemon=True).start()

    def _emision_ok(self, num):
        messagebox.showinfo("Factura Emitida",
                            f"Factura emitida exitosamente.\nNúmero: {num}")
        # ── Impresión automática según configuración ──
        fid = self.factura.get("id")
        if fid:
            config = load_print_config()
            if config["print_mode"] == "auto":
                print_factura(fid, config["printer_type"])
            elif config["print_mode"] == "ask":
                if messagebox.askyesno("Imprimir", "¿Desea imprimir la factura?"):
                    print_factura(fid, config["printer_type"])
        self.on_emitir_done()
        self.destroy()

    def _editar(self):
        self.on_edit(self.factura)
        self.destroy()

    def _cancelar(self):
        fid = self.factura.get("id")
        if fid and self.factura.get("estado") == "BORRADOR":
            if messagebox.askyesno("Confirmar", "¿Anular el borrador y cerrar?"):
                def do():
                    try:
                        client.post(f"/facturas/{fid}/anular")
                    except Exception:
                        pass
                    self.after(0, lambda: (self.on_emitir_done(), self.destroy()))
                threading.Thread(target=do, daemon=True).start()
        else:
            self.destroy()


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
        form = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=12,
                            border_width=1, border_color=C["border"])
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
        btn(bbar,"Cancelar",self.destroy,C["border"]).pack(side="right",padx=4)

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

        tb = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=10, height=52,
                          border_width=1, border_color=C["border"])
        tb.pack(fill="x", padx=24, pady=4)
        tb.pack_propagate(False)
        btn(tb,"↺",self.load,C["border"]).pack(side="right",padx=12)

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

        card = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=12,
                            border_width=1, border_color=C["border"])
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
        btn(bbar,"↺",           self.load,    C["border"]).pack(side="left",padx=4)

        metrics = ctk.CTkFrame(card, fg_color="transparent")
        metrics.pack(fill="x", padx=16, pady=(0,12))
        self.m = {}
        defs = [("Saldo Inicial",C["muted"]),("Ingresos",C["success"]),
                ("Egresos",C["danger"]),("Saldo Final",C["accent"])]
        for i,(lbl,color) in enumerate(defs):
            f = ctk.CTkFrame(metrics, fg_color=C["input_bg"], corner_radius=8,
                             border_width=1, border_color=C["border"])
            f.grid(row=0, column=i, padx=6, sticky="ew")
            metrics.grid_columnconfigure(i, weight=1)
            ctk.CTkLabel(f, text=lbl, text_color=C["muted"], font=("Segoe UI",10)).pack(pady=(8,0))
            v = ctk.CTkLabel(f, text="Gs. 0", text_color=color, font=("Segoe UI",14,"bold"))
            v.pack(pady=(0,8))
            self.m[lbl] = v

        mv = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=12,
                          border_width=1, border_color=C["border"])
        mv.pack(fill="x", padx=24, pady=4)
        ctk.CTkLabel(mv, text="Registrar Movimiento",
                     font=("Segoe UI",13,"bold"), text_color=C["text"]).pack(anchor="w",padx=16,pady=(12,4))

        row = ctk.CTkFrame(mv, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(0,12))

        ctk.CTkLabel(row,text="Tipo",text_color=C["muted"],font=("Segoe UI",11)).pack(side="left",padx=(0,4))
        self.mv_tipo = ctk.StringVar(value="INGRESO")
        ctk.CTkOptionMenu(row,variable=self.mv_tipo,values=["INGRESO","EGRESO"],
                          width=120,fg_color=C["input_bg"],button_color=C["accent"],
                          text_color=C["text"],
                          font=("Segoe UI",11)).pack(side="left",padx=4)

        ctk.CTkLabel(row,text="Monto Gs",text_color=C["muted"],font=("Segoe UI",11)).pack(side="left",padx=(8,4))
        self.mv_monto = ctk.CTkEntry(row,width=120,fg_color=C["input_bg"],
                                      text_color=C["text"],font=("Segoe UI",11))
        self.mv_monto.pack(side="left",padx=4)

        ctk.CTkLabel(row,text="Concepto",text_color=C["muted"],font=("Segoe UI",11)).pack(side="left",padx=(8,4))
        self.mv_concepto = ctk.CTkEntry(row,width=220,fg_color=C["input_bg"],
                                         text_color=C["text"],font=("Segoe UI",11))
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
        form = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=12,
                            border_width=1, border_color=C["border"])
        form.pack(fill="x", padx=20, pady=4)
        form.grid_columnconfigure(1, weight=1)
        self.usuario = field(form,"Usuario",0,default="admin")
        self.saldo   = field(form,"Saldo Inicial Gs",1,default="0")
        bbar = ctk.CTkFrame(self, fg_color="transparent")
        bbar.pack(fill="x", padx=20, pady=12)
        btn(bbar,"Abrir",self._abrir,C["success"],"🔓").pack(side="right",padx=4)
        btn(bbar,"Cancelar",self.destroy,C["border"]).pack(side="right",padx=4)

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

        filtros = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=12,
                               border_width=1, border_color=C["border"])
        filtros.pack(fill="x", padx=24, pady=8)
        row = ctk.CTkFrame(filtros, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(row,text="Desde:",text_color=C["muted"],font=("Segoe UI",11)).pack(side="left",padx=(0,4))
        self.desde = ctk.CTkEntry(row,width=110,fg_color=C["input_bg"],
                                   text_color=C["text"],font=("Segoe UI",11))
        self.desde.insert(0,f"{date.today().year}-01-01")
        self.desde.pack(side="left",padx=4)

        ctk.CTkLabel(row,text="Hasta:",text_color=C["muted"],font=("Segoe UI",11)).pack(side="left",padx=(8,4))
        self.hasta = ctk.CTkEntry(row,width=110,fg_color=C["input_bg"],
                                   text_color=C["text"],font=("Segoe UI",11))
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


# ── Configuración ─────────────────────────────────────────────────────────────
class ConfiguracionPanel(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=C["bg"])
        self._admin_unlocked = False
        self._empresa = {}
        self._build()
        threading.Thread(target=self._load_empresa, daemon=True).start()

    def _build(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color=C["bg"])
        scroll.pack(fill="both", expand=True, padx=24, pady=(20, 8))

        ctk.CTkLabel(scroll, text="⚙️  Configuración",
                     font=("Segoe UI", 22, "bold"), text_color=C["text"]).pack(anchor="w", pady=(0, 12))

        # ── General section ──
        gen = ctk.CTkFrame(scroll, fg_color=C["panel"], corner_radius=12,
                           border_width=1, border_color=C["border"])
        gen.pack(fill="x", pady=4)
        ctk.CTkLabel(gen, text="Datos Generales de la Empresa",
                     font=("Segoe UI", 14, "bold"), text_color=C["text"]).pack(anchor="w", padx=16, pady=(12,4))

        # Logo display
        logo_frame = ctk.CTkFrame(gen, fg_color="transparent")
        logo_frame.pack(fill="x", padx=16, pady=4)
        logo_img = _load_logo(120, 40)
        if logo_img:
            self._logo_preview_lbl = ctk.CTkLabel(logo_frame, image=logo_img, text="")
            self._logo_preview_lbl.pack(side="left")
        else:
            self._logo_preview_lbl = ctk.CTkLabel(logo_frame, text="[Sin logo]", text_color=C["muted"])
            self._logo_preview_lbl.pack(side="left")
        # Detect current logo filename
        _logo_asset = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "LOGO-CV.jpg")
        _logo_name = os.path.basename(_logo_asset) if os.path.exists(_logo_asset) else "No cargado"
        self._logo_name_lbl = ctk.CTkLabel(logo_frame, text=f"  {_logo_name}",
                     text_color=C["muted"], font=("Segoe UI", 10))
        self._logo_name_lbl.pack(side="left", padx=8)
        btn(logo_frame, "Cambiar logo", self._cambiar_logo, C["accent2"], "🖼️").pack(side="left", padx=4)
        btn(logo_frame, "Eliminar logo", self._eliminar_logo, C["danger"], "🗑️").pack(side="left", padx=4)

        form_gen = ctk.CTkFrame(gen, fg_color="transparent")
        form_gen.pack(fill="x", padx=8, pady=4)
        form_gen.grid_columnconfigure(1, weight=1)
        form_gen.grid_columnconfigure(3, weight=1)

        self.gen_razon = field(form_gen, "Razón Social", 0, default="")
        self.gen_nombre = field(form_gen, "Nombre Comercial", 1, default="")
        self.gen_dir = field(form_gen, "Dirección", 2, wide=True, default="")
        self.gen_tel = field(form_gen, "Teléfono", 3, default="")
        self.gen_email = field(form_gen, "Email", 3, col=1, default="")
        self.gen_ciudad = field(form_gen, "Ciudad", 4, default="")

        gen_btns = ctk.CTkFrame(gen, fg_color="transparent")
        gen_btns.pack(fill="x", padx=16, pady=(4,12))
        btn(gen_btns, "Guardar datos generales", self._save_general, C["accent"], "💾").pack(side="left", padx=4)
        btn(gen_btns, "Probar conexión al servidor", self._test_connection, C["accent2"], "🔌").pack(side="left", padx=4)
        self.conn_lbl = ctk.CTkLabel(gen_btns, text="", font=("Segoe UI", 11))
        self.conn_lbl.pack(side="left", padx=8)

        # ── Print config section ──
        prt = ctk.CTkFrame(scroll, fg_color=C["panel"], corner_radius=12,
                           border_width=1, border_color=C["border"])
        prt.pack(fill="x", pady=4)
        ctk.CTkLabel(prt, text="🖨️  Configuración de Impresión",
                     font=("Segoe UI", 14, "bold"), text_color=C["text"]).pack(anchor="w", padx=16, pady=(12,4))

        form_prt = ctk.CTkFrame(prt, fg_color="transparent")
        form_prt.pack(fill="x", padx=8, pady=4)
        form_prt.grid_columnconfigure(1, weight=1)
        form_prt.grid_columnconfigure(3, weight=1)

        self._print_mode_map = {
            "Preguntar antes de imprimir": "ask",
            "Imprimir automáticamente": "auto",
            "No imprimir": "none",
        }
        self._print_mode_reverse = {v: k for k, v in self._print_mode_map.items()}
        self._printer_type_map = {
            "Normal (A4)": "a4",
            "Térmica POS (80mm)": "pos80",
            "Térmica POS (58mm)": "pos58",
        }
        self._printer_type_reverse = {v: k for k, v in self._printer_type_map.items()}

        pcfg = load_print_config()
        self.prt_mode = field(form_prt, "Al emitir factura", 0,
                              choices=["Preguntar antes de imprimir", "Imprimir automáticamente", "No imprimir"],
                              default=self._print_mode_reverse.get(pcfg.get("print_mode","ask"), "Preguntar antes de imprimir"))
        self.prt_type = field(form_prt, "Tipo de impresora", 1,
                              choices=["Normal (A4)", "Térmica POS (80mm)", "Térmica POS (58mm)"],
                              default=self._printer_type_reverse.get(pcfg.get("printer_type","a4"), "Normal (A4)"))

        prt_btns = ctk.CTkFrame(prt, fg_color="transparent")
        prt_btns.pack(fill="x", padx=16, pady=(4,12))
        btn(prt_btns, "Guardar configuración de impresión", self._save_print, C["accent"], "💾").pack(side="left", padx=4)

        # ── Separator ──
        sep = ctk.CTkFrame(scroll, fg_color="transparent")
        sep.pack(fill="x", pady=12)
        ctk.CTkLabel(sep, text="─────────── 🔒 Configuración Fiscal (requiere clave de administrador) ───────────",
                     text_color=C["muted"], font=("Segoe UI", 10)).pack()

        # ── Fiscal section ──
        self._fiscal_frame = ctk.CTkFrame(scroll, fg_color=C["panel"], corner_radius=12,
                                          border_width=1, border_color=C["border"])
        self._fiscal_frame.pack(fill="x", pady=4)

        # Lock UI
        self._lock_frame = ctk.CTkFrame(self._fiscal_frame, fg_color="transparent")
        self._lock_frame.pack(fill="x", padx=16, pady=16)
        ctk.CTkLabel(self._lock_frame, text="🔒  Sección bloqueada",
                     font=("Segoe UI", 13, "bold"), text_color=C["text"]).pack(anchor="w")
        ctk.CTkLabel(self._lock_frame, text="Ingrese la clave de administrador para acceder a la configuración fiscal",
                     text_color=C["muted"], font=("Segoe UI", 11)).pack(anchor="w", pady=(4,8))
        pw_row = ctk.CTkFrame(self._lock_frame, fg_color="transparent")
        pw_row.pack(anchor="w")
        self.admin_pw = ctk.CTkEntry(pw_row, placeholder_text="Clave de administrador",
                                      show="•", width=250, height=38,
                                      fg_color=C["input_bg"], border_color=C["border"],
                                      text_color=C["text"], font=("Segoe UI", 12))
        self.admin_pw.pack(side="left", padx=(0,8))
        btn(pw_row, "Desbloquear", self._unlock, C["accent"], "🔓").pack(side="left")
        self.admin_err = ctk.CTkLabel(self._lock_frame, text="", text_color=C["danger"],
                                       font=("Segoe UI", 11))
        self.admin_err.pack(anchor="w", pady=4)

        # Unlocked fiscal fields (hidden initially)
        self._fiscal_fields = ctk.CTkFrame(self._fiscal_frame, fg_color="transparent")

        ctk.CTkLabel(self._fiscal_fields, text="🔓  Configuración Fiscal Desbloqueada",
                     font=("Segoe UI", 13, "bold"), text_color=C["success"]).pack(anchor="w", padx=16, pady=(12,4))

        ff = ctk.CTkFrame(self._fiscal_fields, fg_color="transparent")
        ff.pack(fill="x", padx=8, pady=4)
        ff.grid_columnconfigure(1, weight=1)
        ff.grid_columnconfigure(3, weight=1)

        self.f_ruc = field(ff, "RUC del Emisor", 0, default="")
        self.f_timbrado = field(ff, "Timbrado", 0, col=1, default="")
        self.f_timb_inicio = field(ff, "Fecha Inicio Timbrado", 1, default="")
        self.f_timb_fin = field(ff, "Fecha Fin Timbrado", 1, col=1, default="")
        self.f_estab = field(ff, "Establecimiento", 2, default="001")
        self.f_punto = field(ff, "Punto Expedición", 2, col=1, default="001")
        self.f_actividad = field(ff, "Actividad Económica", 3, wide=True, default="")
        self.f_sifen = field(ff, "SIFEN Habilitado", 4, choices=["No","Sí"], default="No")
        self.f_tipo_contrib = field(ff, "Tipo Contribuyente", 4, col=1,
                                     choices=["1 - Física","2 - Jurídica"], default="1 - Física")

        fiscal_btns = ctk.CTkFrame(self._fiscal_fields, fg_color="transparent")
        fiscal_btns.pack(fill="x", padx=16, pady=(4,12))
        btn(fiscal_btns, "Guardar configuración fiscal", self._save_fiscal, C["accent"], "💾").pack(side="left", padx=4)
        btn(fiscal_btns, "Bloquear nuevamente", self._lock, C["danger"], "🔒").pack(side="left", padx=4)

    def _load_empresa(self):
        try:
            r = client.get("/config/empresa")
            if r.status_code == 200:
                self._empresa = r.json()
                self.after(0, self._fill_fields)
        except Exception:
            pass

    def _fill_fields(self):
        e = self._empresa
        if not e or not e.get("id"):
            return
        self.gen_razon.set(e.get("razon_social","") or "")
        self.gen_nombre.set(e.get("nombre_fantasia","") or "")
        self.gen_dir.set(e.get("direccion","") or "")
        self.gen_tel.set(e.get("telefono","") or "")
        self.gen_email.set(e.get("email","") or "")
        self.gen_ciudad.set(e.get("ciudad","") or "")
        # Fiscal fields
        self.f_ruc.set(e.get("ruc","") or "")
        self.f_timbrado.set(e.get("timbrado","") or "")
        self.f_timb_inicio.set(e.get("timbrado_fecha_inicio","") or "")
        self.f_timb_fin.set(e.get("timbrado_fecha_fin","") or "")
        self.f_estab.set(e.get("establecimiento","001") or "001")
        self.f_punto.set(e.get("punto_expedicion","001") or "001")
        self.f_actividad.set(e.get("actividad_economica","") or "")
        self.f_sifen.set("Sí" if e.get("sifen_habilitado") else "No")

    def _save_general(self):
        payload = {
            "razon_social": self.gen_razon.get() or None,
            "nombre_fantasia": self.gen_nombre.get() or None,
            "direccion": self.gen_dir.get() or None,
            "telefono": self.gen_tel.get() or None,
            "email": self.gen_email.get() or None,
            "ciudad": self.gen_ciudad.get() or None,
        }
        def do():
            try:
                r = client.put("/config/empresa", json=payload)
                if r.status_code == 200:
                    self.after(0, lambda: toast(self, "Datos generales guardados"))
                else:
                    msg = r.json().get("detail", r.text)
                    self.after(0, lambda: messagebox.showerror("Error", str(msg)))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=do, daemon=True).start()

    def _eliminar_logo(self):
        """Elimina el logo actual de la empresa."""
        import shutil
        if not messagebox.askyesno("Eliminar logo", "¿Seguro que desea eliminar el logo actual?"):
            return
        try:
            _logo_asset = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "LOGO-CV.jpg")
            if os.path.exists(_logo_asset):
                os.remove(_logo_asset)
            self._logo_preview_lbl.configure(image="", text="[Sin logo]")
            self._logo_name_lbl.configure(text="  No cargado")
            toast(self, "Logo eliminado — reinicia el sistema para aplicar el cambio")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar el logo:\n{e}")

    def _cambiar_logo(self):
        """Abre explorador para seleccionar un nuevo logo y lo copia a app/assets/."""
        from tkinter import filedialog
        from PIL import Image as PILImage
        import shutil
        ruta = filedialog.askopenfilename(
            title="Seleccionar logo de la empresa",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.bmp *.gif *.ico"), ("Todos", "*.*")]
        )
        if not ruta:
            return
        try:
            # Destino: app/assets/LOGO-CV.jpg
            assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
            os.makedirs(assets_dir, exist_ok=True)
            dest = os.path.join(assets_dir, "LOGO-CV.jpg")
            # Convertir a JPG si es necesario
            img = PILImage.open(ruta).convert("RGB")
            img.save(dest, "JPEG", quality=95)
            # Actualizar preview
            new_img = _load_logo(120, 40)
            if new_img:
                self._logo_preview_lbl.configure(image=new_img, text="")
            nombre = os.path.basename(ruta)
            self._logo_name_lbl.configure(text=f"  {nombre}")
            toast(self, "Logo actualizado — reinicia el sistema para ver el cambio en el encabezado")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el logo:\n{e}")

    def _save_print(self):
        config = {
            "print_mode": self._print_mode_map.get(self.prt_mode.get(), "ask"),
            "printer_type": self._printer_type_map.get(self.prt_type.get(), "a4"),
        }
        save_print_config(config)
        toast(self, "Configuración de impresión guardada")

    def _test_connection(self):
        def do():
            try:
                r = requests.get("http://localhost:8000/", timeout=5)
                if r.status_code == 200:
                    self.after(0, lambda: self.conn_lbl.configure(
                        text="✓ Servidor conectado", text_color=C["success"]))
                else:
                    self.after(0, lambda: self.conn_lbl.configure(
                        text="✗ Error de conexión", text_color=C["danger"]))
            except Exception:
                self.after(0, lambda: self.conn_lbl.configure(
                    text="✗ No se pudo conectar", text_color=C["danger"]))
        threading.Thread(target=do, daemon=True).start()

    def _unlock(self):
        pw = self.admin_pw.get()
        if not pw:
            self.admin_err.configure(text="Ingrese la clave")
            return
        def do():
            try:
                r = client.post("/config/verify-admin", json={"password": pw})
                if r.status_code == 200 and r.json().get("valid"):
                    self._admin_unlocked = True
                    self.after(0, self._show_fiscal)
                else:
                    self.after(0, lambda: self.admin_err.configure(text="Clave incorrecta"))
            except Exception as e:
                self.after(0, lambda: self.admin_err.configure(text=str(e)))
        threading.Thread(target=do, daemon=True).start()

    def _show_fiscal(self):
        self._lock_frame.pack_forget()
        self._fiscal_fields.pack(fill="x")
        self.admin_err.configure(text="")

    def _lock(self):
        self._admin_unlocked = False
        self._fiscal_fields.pack_forget()
        self._lock_frame.pack(fill="x", padx=16, pady=16)
        self.admin_pw.delete(0, "end")

    def _save_fiscal(self):
        sifen = self.f_sifen.get() == "Sí"
        payload = {
            "ruc": self.f_ruc.get() or None,
            "timbrado": self.f_timbrado.get() or None,
            "timbrado_fecha_inicio": self.f_timb_inicio.get() or None,
            "timbrado_fecha_fin": self.f_timb_fin.get() or None,
            "establecimiento": self.f_estab.get() or None,
            "punto_expedicion": self.f_punto.get() or None,
            "actividad_economica": self.f_actividad.get() or None,
            "sifen_habilitado": sifen,
        }
        def do():
            try:
                r = client.put("/config/empresa", json=payload)
                if r.status_code == 200:
                    self.after(0, lambda: toast(self, "Configuración fiscal guardada"))
                else:
                    msg = r.json().get("detail", r.text)
                    self.after(0, lambda: messagebox.showerror("Error", str(msg)))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=do, daemon=True).start()


# ── App Principal ─────────────────────────────────────────────────────────────
PANELS = {
    "Dashboard":      DashboardPanel,
    "Facturas":       FacturasPanel,
    "Clientes":       ClientesPanel,
    "Productos":      ProductosPanel,
    "Proveedores":    ProveedoresPanel,
    "Compras":        ComprasPanel,
    "Caja":           CajaPanel,
    "Reportes":       ReportesPanel,
    "Configuración":  ConfiguracionPanel,
}


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("FacturaPY — Sistema de Gestión Comercial")
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

        # Header bar
        header = ctk.CTkFrame(self, fg_color=C["header"], corner_radius=0, height=50)
        header.pack(fill="x")
        header.pack_propagate(False)

        h_left = ctk.CTkFrame(header, fg_color="transparent")
        h_left.pack(side="left", padx=16)
        logo_img = _load_logo(120, 40)
        if logo_img:
            ctk.CTkLabel(h_left, image=logo_img, text="").pack(side="left")
        ctk.CTkLabel(h_left, text="  FacturaPY", font=("Segoe UI", 14, "bold"),
                     text_color=C["text_inv"]).pack(side="left")

        h_right = ctk.CTkFrame(header, fg_color="transparent")
        h_right.pack(side="right", padx=16)
        ctk.CTkLabel(h_right, text=f"👤 {client.username}",
                     font=("Segoe UI", 11), text_color=C["text_inv"]).pack(side="left", padx=8)
        ctk.CTkButton(h_right, text="Cerrar Sesión", command=self._logout,
                      fg_color=C["danger"], hover_color="#8B0000",
                      text_color=C["text_inv"],
                      font=("Segoe UI", 11), corner_radius=6,
                      height=30, width=110).pack(side="left")

        # Body
        body = ctk.CTkFrame(self, fg_color=C["bg"])
        body.pack(fill="both", expand=True)

        self._sidebar = Sidebar(body, on_select=self._navigate)
        self._sidebar.pack(side="left", fill="y")
        ctk.CTkFrame(body, fg_color=C["border"], width=1).pack(side="left", fill="y")

        self._area = ctk.CTkFrame(body, fg_color=C["bg"])
        self._area.pack(side="left", fill="both", expand=True)

        self._header_ref = header
        self._body_ref = body
        self._sidebar.select("Dashboard")

    def _navigate(self, name):
        if self._current:
            self._current.pack_forget()
        if name not in self._cache:
            self._cache[name] = PANELS[name](self._area)
        self._current = self._cache[name]
        self._current.pack(fill="both", expand=True)

    def _logout(self):
        if messagebox.askyesno("Cerrar Sesión", "¿Desea cerrar sesión?"):
            client.token = None
            client.s.headers.pop("Authorization", None)
            self._cache.clear()
            if self._current:
                self._current.pack_forget()
                self._current = None
            self._header_ref.destroy()
            self._body_ref.destroy()
            self._show_login()
