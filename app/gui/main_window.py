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
    ("🏠", "Inicio"),
    ("📄", "Facturas"),
    ("👥", "Clientes"),
    ("📦", "Productos"),
    ("🏭", "Proveedores"),
    ("📦", "Stock"),
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
            self._sidebar_logo_lbl = ctk.CTkLabel(logo_frame, image=logo_img, text="")
        else:
            self._sidebar_logo_lbl = ctk.CTkLabel(logo_frame, text="FacturaPY",
                         font=("Segoe UI", 13, "bold"),
                         text_color=C["text_inv"])
        self._sidebar_logo_lbl.pack(expand=True)

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
        ctk.CTkLabel(hdr, text="Inicio",
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
        self.transient(parent)
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
        self.transient(parent)
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


# ── FacturaForm — Nueva factura con carga unificada ──────────────────────────
class FacturaForm(ctk.CTkToplevel):
    def __init__(self, parent, on_save, edit_data=None):
        super().__init__(parent)
        self.transient(parent)
        self.on_save = on_save
        self.edit_data = edit_data
        self.title("Nueva Factura")
        self.geometry("880x800")
        self.minsize(860, 700)
        self.configure(fg_color=C["bg"])
        self.grab_set()
        self.after(0, lambda: self.state("zoomed"))
        self._clientes = []
        self._detalles = []
        self._cliente_id = None          # int si está en BD, None si es ocasional
        self._prod_id = None             # int si código encontrado en BD, None si manual
        self._cli_search_after = None    # debounce timer
        self._cod_search_after = None    # debounce timer
        if edit_data and edit_data.get("detalles"):
            self._detalles = list(edit_data["detalles"])
        self._build()
        threading.Thread(target=self._load_data, daemon=True).start()

    def _build(self):
        ctk.CTkLabel(self, text="➕  Nueva Factura",
                     font=("Segoe UI", 16, "bold"), text_color=C["text"]).pack(pady=(12, 4))

        # ── Header: Cliente ──
        top = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=12,
                           border_width=1, border_color=C["border"])
        top.pack(fill="x", padx=16, pady=4)
        top.grid_columnconfigure(1, weight=1)
        top.grid_columnconfigure(3, weight=1)

        cli_row = ctk.CTkFrame(top, fg_color="transparent")
        cli_row.grid(row=0, column=0, columnspan=4, sticky="ew", padx=12, pady=8)

        ctk.CTkLabel(cli_row, text="RUC/CI:", text_color=C["muted"],
                     font=("Segoe UI", 11)).pack(side="left", padx=(0, 4))
        self.cli_ruc_var = ctk.StringVar()
        self._cli_ruc_entry = ctk.CTkEntry(
            cli_row, textvariable=self.cli_ruc_var, width=140,
            fg_color=C["input_bg"], text_color=C["text"],
            font=("Segoe UI", 11), placeholder_text="RUC o Cédula")
        self._cli_ruc_entry.pack(side="left", padx=(0, 6))
        self.cli_ruc_var.trace_add("write", self._on_ruc_change)

        ctk.CTkLabel(cli_row, text="Nombre / Razón Social:", text_color=C["muted"],
                     font=("Segoe UI", 11)).pack(side="left", padx=(0, 4))
        self.cli_nombre_var = ctk.StringVar()
        self._cli_nombre_entry = ctk.CTkEntry(
            cli_row, textvariable=self.cli_nombre_var, width=260,
            fg_color=C["input_bg"], text_color=C["text"],
            font=("Segoe UI", 11), placeholder_text="Razón Social del cliente")
        self._cli_nombre_entry.pack(side="left", padx=(0, 8))

        btn(cli_row, "Nuevo cliente", self._nuevo_cliente, C["accent2"], "➕").pack(side="left", padx=4)

        # Estado de búsqueda de cliente
        self._cli_status_lbl = ctk.CTkLabel(cli_row, text="",
                                             font=("Segoe UI", 10), text_color=C["muted"])
        self._cli_status_lbl.pack(side="left", padx=8)

        self.cond  = field(top, "Condición", 1, col=0, choices=["CONTADO", "CREDITO"])
        self.fecha = field(top, "Fecha",     2, col=0, default=str(date.today()))
        self.obs   = field(top, "Observación", 2, col=1, default="")

        # ── Sección Agregar Ítems ──
        ctk.CTkLabel(self, text="  Agregar Ítem",
                     font=("Segoe UI", 13, "bold"), text_color=C["text"]).pack(
                         anchor="w", padx=16, pady=(4, 0))

        item_frame = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=10,
                                  border_width=1, border_color=C["border"])
        item_frame.pack(fill="x", padx=16, pady=4)

        item_row = ctk.CTkFrame(item_frame, fg_color="transparent")
        item_row.pack(fill="x", padx=8, pady=8)

        ctk.CTkLabel(item_row, text="Código:", text_color=C["muted"],
                     font=("Segoe UI", 11)).pack(side="left", padx=(0, 3))
        self._cod_var = ctk.StringVar()
        self._cod_entry = ctk.CTkEntry(item_row, textvariable=self._cod_var, width=90,
                                       fg_color=C["input_bg"], text_color=C["text"],
                                       font=("Segoe UI", 11), placeholder_text="Cód.")
        self._cod_entry.pack(side="left", padx=(0, 6))
        self._cod_var.trace_add("write", self._on_cod_change)

        ctk.CTkLabel(item_row, text="Descripción:", text_color=C["muted"],
                     font=("Segoe UI", 11)).pack(side="left", padx=(0, 3))
        self._desc_var = ctk.StringVar()
        self._desc_entry = ctk.CTkEntry(item_row, textvariable=self._desc_var, width=190,
                                        fg_color=C["input_bg"], text_color=C["text"],
                                        font=("Segoe UI", 11), placeholder_text="Descripción del ítem")
        self._desc_entry.pack(side="left", padx=(0, 6))

        ctk.CTkLabel(item_row, text="Cant.:", text_color=C["muted"],
                     font=("Segoe UI", 11)).pack(side="left", padx=(0, 3))
        self._cant_entry = ctk.CTkEntry(item_row, width=55,
                                        fg_color=C["input_bg"], text_color=C["text"],
                                        font=("Segoe UI", 11))
        self._cant_entry.insert(0, "1")
        self._cant_entry.pack(side="left", padx=(0, 6))

        ctk.CTkLabel(item_row, text="Precio:", text_color=C["muted"],
                     font=("Segoe UI", 11)).pack(side="left", padx=(0, 3))
        self._precio_var = ctk.StringVar()
        self._precio_entry = ctk.CTkEntry(item_row, textvariable=self._precio_var, width=110,
                                          fg_color=C["input_bg"], text_color=C["text"],
                                          font=("Segoe UI", 11), placeholder_text="0")
        self._precio_entry.pack(side="left", padx=(0, 6))
        self._precio_var.trace_add("write", format_gs_input(self._precio_var, self._precio_entry))

        ctk.CTkLabel(item_row, text="IVA%:", text_color=C["muted"],
                     font=("Segoe UI", 11)).pack(side="left", padx=(0, 3))
        self._iva_var = ctk.StringVar(value="10")
        ctk.CTkOptionMenu(item_row, variable=self._iva_var, values=["10", "5", "0"],
                          width=65, fg_color=C["input_bg"], button_color=C["accent"],
                          text_color=C["text"], font=("Segoe UI", 11)).pack(side="left", padx=(0, 8))

        btn(item_row, "Agregar", self._agregar_item, C["success"], "➕").pack(side="left")

        # Status de búsqueda de producto
        self._prod_status_lbl = ctk.CTkLabel(item_frame, text="",
                                              font=("Segoe UI", 10), text_color=C["muted"])
        self._prod_status_lbl.pack(anchor="w", padx=12, pady=(0, 6))

        # ── Botones inferiores (anclados al fondo) ──
        bbar = ctk.CTkFrame(self, fg_color="transparent")
        bbar.pack(side="bottom", fill="x", padx=16, pady=8)
        btn(bbar, "Vista Previa", self._vista_previa, C["accent"], "👁️").pack(side="right", padx=4)
        btn(bbar, "Cancelar", self.destroy, C["border"]).pack(side="right", padx=4)

        # ── Barra de totales (anclada al fondo) ──
        bot = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=10,
                           border_width=1, border_color=C["border"])
        bot.pack(side="bottom", fill="x", padx=16, pady=4)
        self.total_lbl = ctk.CTkLabel(bot, text="Total: Gs. 0",
                                       font=("Segoe UI", 14, "bold"), text_color=C["success"])
        self.total_lbl.pack(side="right", padx=16, pady=8)
        ctk.CTkLabel(bot, text="Presione Delete para quitar un ítem",
                     text_color=C["muted"], font=("Segoe UI", 10)).pack(side="left", padx=16)

        # ── Tabla de ítems (ocupa el espacio restante) ──
        cols = ["#", "Descripción", "Cant.", "Precio", "IVA%", "Total"]
        widths = [30, 260, 60, 120, 60, 130]
        tf, self.items_tree = make_table(self, cols, widths)
        tf.pack(fill="both", expand=True, padx=16, pady=4)
        self.items_tree.bind("<Delete>", lambda e: self._quitar())

        if self.edit_data:
            self._prefill_edit()

    # ── Búsqueda de cliente por RUC ──────────────────────────────────────────
    def _on_ruc_change(self, *args):
        if self._cli_search_after:
            self.after_cancel(self._cli_search_after)
        self._cli_search_after = self.after(600, self._buscar_cliente_ruc)

    def _buscar_cliente_ruc(self):
        ruc = self.cli_ruc_var.get().strip()
        if not ruc:
            self._cliente_id = None
            self._cli_status_lbl.configure(text="", text_color=C["muted"])
            return
        def do():
            try:
                r = client.get("/clientes/buscar", params={"ruc": ruc})
                if r.status_code == 200:
                    c = r.json()
                    self._cliente_id = c["id"]
                    nombre = c.get("razon_social", "")
                    self.after(0, lambda: self.cli_nombre_var.set(nombre))
                    self.after(0, lambda: self._cli_status_lbl.configure(
                        text=f"✓ Cliente encontrado", text_color=C["success"]))
                else:
                    self._cliente_id = None
                    self.after(0, lambda: self._cli_status_lbl.configure(
                        text="⚠ No registrado — se cargará como ocasional", text_color=C["warning"]))
            except Exception:
                self._cliente_id = None
        threading.Thread(target=do, daemon=True).start()

    def _nuevo_cliente(self):
        def on_guardado():
            ruc = self.cli_ruc_var.get().strip()
            if ruc:
                self._buscar_cliente_ruc()
        ClienteForm(self, None, on_save=on_guardado)

    # ── Búsqueda de producto por código ─────────────────────────────────────
    def _on_cod_change(self, *args):
        if self._cod_search_after:
            self.after_cancel(self._cod_search_after)
        self._cod_search_after = self.after(500, self._buscar_producto_codigo)

    def _buscar_producto_codigo(self):
        cod = self._cod_var.get().strip()
        if not cod:
            self._prod_id = None
            self._prod_status_lbl.configure(text="")
            return
        def do():
            try:
                r = client.get("/productos/buscar", params={"codigo": cod})
                if r.status_code == 200:
                    p = r.json()
                    self._prod_id = p["id"]
                    precio_str = str(int(float(p.get("precio_unitario", 0))))
                    iva_str = str(p.get("tasa_iva", "10"))
                    self.after(0, lambda: self._desc_var.set(p.get("descripcion", "")))
                    self.after(0, lambda: self._precio_var.set(precio_str))
                    self.after(0, lambda: self._iva_var.set(iva_str))
                    self.after(0, lambda: self._prod_status_lbl.configure(
                        text=f"✓  {p.get('descripcion', '')}", text_color=C["success"]))
                else:
                    self._prod_id = None
                    self.after(0, lambda: self._prod_status_lbl.configure(
                        text="Código no encontrado — completar datos manualmente",
                        text_color=C["warning"]))
            except Exception:
                self._prod_id = None
        threading.Thread(target=do, daemon=True).start()

    # ── Agregar ítem unificado ───────────────────────────────────────────────
    def _agregar_item(self):
        desc = self._desc_var.get().strip()
        if not desc:
            return messagebox.showerror("Error", "Ingrese una descripción del ítem")
        try:
            cant = float(self._cant_entry.get())
            precio = float(self._precio_var.get().replace(".", "").replace(",", "."))
        except ValueError:
            return messagebox.showerror("Error", "Cantidad y precio deben ser números válidos")
        if cant <= 0 or precio < 0:
            return messagebox.showerror("Error", "Cantidad debe ser mayor a 0")

        self._detalles.append({
            "orden": len(self._detalles) + 1,
            "producto_id": self._prod_id,
            "descripcion": desc,
            "cantidad": cant,
            "precio_unitario": precio,
            "tasa_iva": str(self._iva_var.get()),
        })
        self._refresh_items()

        # Limpiar campos para próximo ítem
        self._cod_var.set("")
        self._desc_var.set("")
        self._cant_entry.delete(0, "end")
        self._cant_entry.insert(0, "1")
        self._precio_var.set("")
        self._iva_var.set("10")
        self._prod_id = None
        self._prod_status_lbl.configure(text="")
        self._cod_entry.focus()

    def _refresh_items(self):
        for i in self.items_tree.get_children():
            self.items_tree.delete(i)
        for idx, d in enumerate(self._detalles):
            total = d["cantidad"] * d["precio_unitario"]
            self.items_tree.insert("", "end", values=(
                idx + 1, d["descripcion"],
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

    def _prefill_edit(self):
        d = self.edit_data
        if d.get("fecha_emision"):
            self.fecha.set(d["fecha_emision"])
        if d.get("condicion_venta"):
            self.cond.set(d["condicion_venta"])
        if d.get("observacion"):
            self.obs.set(d["observacion"])
        self._refresh_items()

    def _load_data(self):
        try:
            self._clientes = client.get("/clientes").json()
            # Pre-fill if editing and client_id known
            if self.edit_data and self.edit_data.get("cliente_id"):
                cid = self.edit_data["cliente_id"]
                cli = next((c for c in self._clientes if c["id"] == cid), None)
                if cli:
                    self._cliente_id = cid
                    self.after(0, lambda: self.cli_ruc_var.set(cli.get("ruc_ci", "")))
                    self.after(0, lambda: self.cli_nombre_var.set(cli.get("razon_social", "")))
        except Exception:
            pass

    def _get_ocasional_cliente_id(self):
        """Fallback: buscar o usar CONSUMIDOR FINAL."""
        for c in self._clientes:
            if "CONSUMIDOR FINAL" in (c.get("razon_social", "") or "").upper():
                return c["id"]
        if self._clientes:
            return self._clientes[0]["id"]
        return None

    def _vista_previa(self):
        """Guarda como borrador y abre vista previa."""
        if not self._detalles:
            return messagebox.showerror("Error", "Agregue al menos un ítem a la factura")

        ruc    = self.cli_ruc_var.get().strip()
        nombre = self.cli_nombre_var.get().strip()

        if self._cliente_id is not None:
            cid = self._cliente_id
            observacion = self.obs.get() or None
            cli_name = nombre or ruc or "—"
        else:
            # Cliente ocasional: guardar datos en observacion
            if not nombre:
                return messagebox.showerror("Error",
                    "Ingrese el Nombre / Razón Social del cliente")
            cid = self._get_ocasional_cliente_id()
            if cid is None:
                return messagebox.showerror("Error",
                    "No hay clientes disponibles. Cree al menos un cliente antes de facturar.")
            obs_ocas = f"[Cliente Ocasional] RUC: {ruc} | Nombre: {nombre}" if ruc else f"[Cliente Ocasional] Nombre: {nombre}"
            obs_base = self.obs.get() or ""
            observacion = f"{obs_ocas} | {obs_base}" if obs_base else obs_ocas
            cli_name = f"{nombre}" + (f" (RUC: {ruc})" if ruc else "")

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
                    try:
                        msg = r.json().get("detail", r.text)
                    except Exception:
                        msg = r.text
                    self.after(0, lambda: messagebox.showerror("Error al guardar factura", str(msg)))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error de conexión", str(e)))
        threading.Thread(target=do, daemon=True).start()

    def _open_preview(self, factura_data, cli_name):
        VistaPreviewFactura(self, factura_data, cli_name,
                            on_emitir_done=lambda: (self.on_save(), self.destroy()),
                            on_edit=lambda data: self._return_to_edit(data))

    def _return_to_edit(self, data):
        self.edit_data = data
        if data.get("detalles"):
            self._detalles = list(data["detalles"])
            self._refresh_items()


# ── Vista Previa de Factura ──────────────────────────────────────────────────
class VistaPreviewFactura(ctk.CTkToplevel):
    """Vista previa de factura con diseño de comprobante real (SET / DNIT Paraguay)."""

    def __init__(self, parent, factura, cli_name, on_emitir_done, on_edit):
        super().__init__(parent)
        self.transient(parent)
        self.factura = factura
        self.cli_name = cli_name
        self.on_emitir_done = on_emitir_done
        self.on_edit = on_edit
        self.title("Vista Previa — Factura")
        self.geometry("820x760")
        self.configure(fg_color=C["bg"])
        self.grab_set()
        # Cargar datos de empresa de forma síncrona (es rápido, está en localhost)
        self._empresa = {}
        try:
            r = client.get("/config/empresa")
            if r.status_code == 200:
                self._empresa = r.json() or {}
        except Exception:
            pass
        self._build()

    def _label(self, parent, text, bold=False, size=10, color=None, **kwargs):
        font = ("Segoe UI", size, "bold") if bold else ("Segoe UI", size)
        return ctk.CTkLabel(parent, text=text, font=font,
                            text_color=color or C["text"], **kwargs)

    def _build(self):
        estado = self.factura.get("estado", "BORRADOR")
        emp = self._empresa

        # ── Scroll container ──
        scroll = ctk.CTkScrollableFrame(self, fg_color=C["bg"])
        scroll.pack(fill="both", expand=True, padx=12, pady=(8, 4))

        # ══════════════════════════════════════════════════
        # BLOQUE 1: Encabezado del emisor
        # ══════════════════════════════════════════════════
        emisor_frame = ctk.CTkFrame(scroll, fg_color=C["header"], corner_radius=10)
        emisor_frame.pack(fill="x", pady=(0, 4))
        em_inner = ctk.CTkFrame(emisor_frame, fg_color="transparent")
        em_inner.pack(fill="x", padx=16, pady=12)

        logo_img = _load_logo(100, 33)
        if logo_img:
            ctk.CTkLabel(em_inner, image=logo_img, text="").pack(side="left", padx=(0, 12))

        em_text = ctk.CTkFrame(em_inner, fg_color="transparent")
        em_text.pack(side="left", fill="x", expand=True)

        razon = emp.get("razon_social") or "— Empresa no configurada —"
        ruc_emisor = emp.get("ruc") or "—"
        dir_emisor = emp.get("direccion") or ""
        ciudad_emisor = emp.get("ciudad") or ""
        tel_emisor = emp.get("telefono") or ""

        self._label(em_text, razon, bold=True, size=14, color=C["text_inv"]).pack(anchor="w")
        self._label(em_text, f"RUC: {ruc_emisor}", size=11, color=C["text_inv"]).pack(anchor="w")
        if dir_emisor:
            self._label(em_text, f"{dir_emisor}{(' — ' + ciudad_emisor) if ciudad_emisor else ''}",
                        size=10, color="#B0BEC5").pack(anchor="w")
        if tel_emisor:
            self._label(em_text, f"Tel.: {tel_emisor}", size=10, color="#B0BEC5").pack(anchor="w")

        # Tipo de documento + estado
        tipo_frame = ctk.CTkFrame(em_inner, fg_color="transparent")
        tipo_frame.pack(side="right", anchor="ne")
        tipo_doc = self.factura.get("tipo_documento", "FACTURA")
        self._label(tipo_frame, tipo_doc, bold=True, size=16, color=C["text_inv"]).pack(anchor="e")
        estado_color = C["warning"] if estado == "BORRADOR" else C["success"]
        ctk.CTkLabel(tipo_frame, text=f"  {estado}  ",
                     font=("Segoe UI", 10, "bold"),
                     fg_color=estado_color, text_color=C["text_inv"],
                     corner_radius=6).pack(anchor="e", pady=(4, 0))

        # ══════════════════════════════════════════════════
        # BLOQUE 2: Aviso BORRADOR (si aplica)
        # ══════════════════════════════════════════════════
        if estado == "BORRADOR":
            aviso = ctk.CTkFrame(scroll, fg_color="#7B1C1C", corner_radius=6)
            aviso.pack(fill="x", pady=2)
            ctk.CTkLabel(aviso,
                         text="⚠  BORRADOR — Este comprobante NO ha sido emitido. No tiene validez fiscal.",
                         font=("Segoe UI", 11, "bold"), text_color="#FFCCCC").pack(pady=6)

        # ══════════════════════════════════════════════════
        # BLOQUE 3: Timbrado / Datos del documento
        # ══════════════════════════════════════════════════
        tim_frame = ctk.CTkFrame(scroll, fg_color=C["panel"], corner_radius=10,
                                 border_width=1, border_color=C["border"])
        tim_frame.pack(fill="x", pady=4)
        tim_frame.grid_columnconfigure((0,1,2,3,4,5), weight=1)

        timbrado    = emp.get("timbrado") or "—"
        tim_inicio  = emp.get("timbrado_fecha_inicio") or "—"
        tim_fin     = emp.get("timbrado_fecha_fin") or "—"
        estab       = emp.get("establecimiento") or "001"
        pto_exp     = emp.get("punto_expedicion") or "001"
        num_doc     = self.factura.get("numero_completo") or "Pendiente"
        fecha_doc   = self.factura.get("fecha_emision") or "—"

        autoimpreso_lbl = ctk.CTkFrame(tim_frame, fg_color=C["accent2"], corner_radius=4)
        autoimpreso_lbl.grid(row=0, column=0, columnspan=6, sticky="ew", padx=8, pady=(8, 4))
        ctk.CTkLabel(autoimpreso_lbl, text="DOCUMENTO AUTOIMPRESO",
                     font=("Segoe UI", 10, "bold"), text_color=C["text_inv"]).pack(pady=3)

        datos_doc = [
            ("Timbrado N°:", timbrado),
            ("Vigencia:", f"{tim_inicio}  al  {tim_fin}"),
            ("Establecimiento:", estab),
            ("Pto. Expedición:", pto_exp),
            ("N° Comprobante:", num_doc),
            ("Fecha:", fecha_doc),
        ]
        for col_idx, (lbl, val) in enumerate(datos_doc):
            r_idx = 1 + col_idx // 2
            c_idx = (col_idx % 2) * 2
            ctk.CTkLabel(tim_frame, text=lbl, text_color=C["muted"],
                         font=("Segoe UI", 9)).grid(row=r_idx, column=c_idx,
                                                     padx=(12, 2), pady=3, sticky="w")
            ctk.CTkLabel(tim_frame, text=val, text_color=C["text"],
                         font=("Segoe UI", 10, "bold")).grid(row=r_idx, column=c_idx+1,
                                                              padx=(0, 12), pady=3, sticky="w")

        # Condicion de venta
        cond_val = self.factura.get("condicion_venta", "CONTADO")
        cond_frame = ctk.CTkFrame(tim_frame, fg_color="transparent")
        cond_frame.grid(row=4, column=0, columnspan=6, sticky="w", padx=8, pady=(2, 8))
        ctk.CTkLabel(cond_frame, text="Condición de Venta:", text_color=C["muted"],
                     font=("Segoe UI", 9)).pack(side="left", padx=(4, 4))
        ctk.CTkLabel(cond_frame, text=cond_val, text_color=C["accent"],
                     font=("Segoe UI", 10, "bold")).pack(side="left")

        # ══════════════════════════════════════════════════
        # BLOQUE 4: Datos del cliente
        # ══════════════════════════════════════════════════
        cli_frame = ctk.CTkFrame(scroll, fg_color=C["panel"], corner_radius=10,
                                 border_width=1, border_color=C["border"])
        cli_frame.pack(fill="x", pady=4)
        ctk.CTkLabel(cli_frame, text="DATOS DEL COMPRADOR",
                     font=("Segoe UI", 9, "bold"), text_color=C["muted"]).pack(
                         anchor="w", padx=12, pady=(8, 2))

        cli_row_frame = ctk.CTkFrame(cli_frame, fg_color="transparent")
        cli_row_frame.pack(fill="x", padx=12, pady=(0, 8))
        ctk.CTkLabel(cli_row_frame, text="Nombre / Razón Social:", text_color=C["muted"],
                     font=("Segoe UI", 10)).pack(side="left")
        ctk.CTkLabel(cli_row_frame, text=f"  {self.cli_name}",
                     text_color=C["text"], font=("Segoe UI", 11, "bold")).pack(side="left")

        # Observación (contiene RUC del cliente ocasional si aplica)
        obs = self.factura.get("observacion") or ""
        if obs:
            obs_row = ctk.CTkFrame(cli_frame, fg_color="transparent")
            obs_row.pack(fill="x", padx=12, pady=(0, 6))
            ctk.CTkLabel(obs_row, text="Obs.:", text_color=C["muted"],
                         font=("Segoe UI", 9)).pack(side="left")
            ctk.CTkLabel(obs_row, text=f"  {obs}", text_color=C["text"],
                         font=("Segoe UI", 9)).pack(side="left")

        # ══════════════════════════════════════════════════
        # BLOQUE 5: Tabla de ítems
        # ══════════════════════════════════════════════════
        items_frame = ctk.CTkFrame(scroll, fg_color=C["panel"], corner_radius=10,
                                   border_width=1, border_color=C["border"])
        items_frame.pack(fill="x", pady=4)

        # Encabezado de tabla
        th = ctk.CTkFrame(items_frame, fg_color=C["header"], corner_radius=0)
        th.pack(fill="x", padx=8, pady=(8, 0))
        cols_def = [("#", 28), ("Descripción", 240), ("Cant.", 52), ("P. Unit.", 110),
                    ("IVA%", 48), ("Subtotal", 115)]
        for label, w in cols_def:
            ctk.CTkLabel(th, text=label, text_color=C["text_inv"],
                         font=("Segoe UI", 9, "bold"), width=w).pack(side="left", padx=3, pady=4)

        detalles = self.factura.get("detalles", [])
        for i, d in enumerate(detalles):
            bg = C["row_even"] if i % 2 == 0 else C["row_odd"]
            row = ctk.CTkFrame(items_frame, fg_color=bg, corner_radius=0)
            row.pack(fill="x", padx=8)
            total_l = float(d.get("total_linea", 0) or
                            (float(d.get("cantidad", 0)) * float(d.get("precio_unitario", 0))))
            vals = [
                (str(d.get("orden", i + 1)), 28),
                (d.get("descripcion", ""), 240),
                (str(int(float(d.get("cantidad", 0)))), 52),
                (gs(d.get("precio_unitario", 0)), 110),
                (f"{d.get('tasa_iva', 10)}%", 48),
                (gs(total_l), 115),
            ]
            for val, w in vals:
                ctk.CTkLabel(row, text=val, text_color=C["text"],
                             font=("Segoe UI", 10), width=w).pack(side="left", padx=3, pady=3)

        ctk.CTkFrame(items_frame, fg_color=C["border"], height=1).pack(fill="x", padx=8, pady=4)

        # ══════════════════════════════════════════════════
        # BLOQUE 6: Totales (IVA desglosado)
        # ══════════════════════════════════════════════════
        totals = ctk.CTkFrame(scroll, fg_color=C["panel"], corner_radius=10,
                              border_width=1, border_color=C["border"])
        totals.pack(fill="x", pady=4)

        totals_left = ctk.CTkFrame(totals, fg_color="transparent")
        totals_left.pack(side="left", fill="both", expand=True, padx=12, pady=8)

        # Notas SET (lado izquierdo)
        act_economica = emp.get("actividad_economica") or ""
        if act_economica:
            ctk.CTkLabel(totals_left, text=f"Actividad: {act_economica}",
                         font=("Segoe UI", 9), text_color=C["muted"],
                         wraplength=300, justify="left").pack(anchor="w")
        ctk.CTkLabel(totals_left,
                     text="Documento Autoimpreso habilitado por la SET",
                     font=("Segoe UI", 9), text_color=C["muted"]).pack(anchor="w", pady=(8, 0))
        if timbrado != "—":
            ctk.CTkLabel(totals_left, text=f"Timbrado N° {timbrado} — Vigente hasta {tim_fin}",
                         font=("Segoe UI", 9), text_color=C["muted"]).pack(anchor="w")

        totals_right = ctk.CTkFrame(totals, fg_color="transparent")
        totals_right.pack(side="right", padx=16, pady=8)
        totals_right.grid_columnconfigure(1, weight=1)

        tax_rows = [
            ("Subtotal Exenta (Gs.):", gs(self.factura.get("subtotal_exenta", 0))),
            ("Subtotal Gravada 5% (Gs.):", gs(self.factura.get("subtotal_gravada_5", 0))),
            ("Subtotal Gravada 10% (Gs.):", gs(self.factura.get("subtotal_gravada_10", 0))),
            ("IVA 5% (Gs.):", gs(self.factura.get("iva_5", 0))),
            ("IVA 10% (Gs.):", gs(self.factura.get("iva_10", 0))),
        ]
        for row_i, (lbl, val) in enumerate(tax_rows):
            ctk.CTkLabel(totals_right, text=lbl, text_color=C["muted"],
                         font=("Segoe UI", 9),
                         anchor="e").grid(row=row_i, column=0, padx=(0, 8), pady=1, sticky="e")
            ctk.CTkLabel(totals_right, text=val, text_color=C["text"],
                         font=("Segoe UI", 9, "bold"),
                         anchor="e").grid(row=row_i, column=1, pady=1, sticky="e")

        # Total final
        gt = ctk.CTkFrame(scroll, fg_color=C["accent"], corner_radius=8)
        gt.pack(fill="x", padx=12, pady=(2, 8))
        ctk.CTkLabel(gt,
                     text=f"TOTAL A PAGAR:  {gs(self.factura.get('total', 0))}",
                     text_color=C["text_inv"],
                     font=("Segoe UI", 16, "bold")).pack(pady=10)

        # ── Botones de acción ──
        bbar = ctk.CTkFrame(self, fg_color="transparent")
        bbar.pack(fill="x", padx=16, pady=8)

        ctk.CTkButton(bbar, text="✅  Emitir Factura",
                      command=self._emitir,
                      fg_color=C["accent"], hover_color=C["header"],
                      text_color=C["text_inv"],
                      font=("Segoe UI", 13, "bold"),
                      corner_radius=8, height=42, width=200).pack(side="right", padx=4)
        btn(bbar, "✏️ Editar", self._editar, C["accent2"]).pack(side="right", padx=4)
        btn(bbar, "❌ Cancelar", self._cancelar, C["danger"]).pack(side="right", padx=4)

    def _emitir(self):
        fid = self.factura.get("id")
        if not fid: return
        def do():
            try:
                r = client.post(f"/facturas/{fid}/emitir")
                if r.status_code == 200:
                    num = r.json().get("numero_completo", "")
                    self.after(0, lambda: self._emision_ok(num))
                else:
                    try:
                        msg = r.json().get("detail", r.text)
                    except Exception:
                        msg = r.text
                    self.after(0, lambda: messagebox.showerror("Error al emitir", str(msg)))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error de conexión", str(e)))
        threading.Thread(target=do, daemon=True).start()

    def _emision_ok(self, num):
        messagebox.showinfo("Factura Emitida",
                            f"Factura emitida exitosamente.\nNúmero: {num}")
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
    COLUMNS = ["Código","RUC","Razón Social","Teléfono","Email","Dirección"]
    COL_WIDTHS = [80,130,240,120,180,150]

    def _insert_row(self, p):
        self.tree.insert("", "end", values=(
            p.get("prov_cod",""), p.get("prov_ruc",""),
            p.get("prov_nom",""), p.get("prov_tel",""),
            p.get("prov_email",""), p.get("prov_dir","")))

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
        self.transient(parent)
        self.item = item; self.on_save = on_save
        self.title("Proveedor")
        self.geometry("500x360")
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
        self.ruc    = field(form,"RUC *",        0, default=v.get("prov_ruc",""))
        self.nombre = field(form,"Nombre / Razón Social *", 1, wide=True, default=v.get("prov_nom",""))
        self.tel    = field(form,"Teléfono",   2, default=v.get("prov_tel",""))
        self.email  = field(form,"Email",      3, default=v.get("prov_email",""))
        self.dir    = field(form,"Dirección",  4, wide=True, default=v.get("prov_dir",""))
        bbar = ctk.CTkFrame(self, fg_color="transparent")
        bbar.pack(fill="x", padx=20, pady=10)
        btn(bbar,"Guardar",self._save,C["accent"],"💾").pack(side="right",padx=4)
        btn(bbar,"Cancelar",self.destroy,C["border"]).pack(side="right",padx=4)

    def _save(self):
        if not self.ruc.get().strip() or not self.nombre.get().strip():
            return messagebox.showerror("Error","RUC y Nombre son obligatorios")
        payload = {
            "prov_ruc": self.ruc.get().strip(),
            "prov_nom": self.nombre.get().strip(),
            "prov_tel": self.tel.get() or None,
            "prov_email": self.email.get() or None,
            "prov_dir": self.dir.get() or None,
            "prov_contacto": None,
            "prov_limite": 0.0,
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
                    try:
                        detail = r.json().get("detail", r.text)
                    except Exception:
                        detail = r.text
                    self.after(0, lambda: messagebox.showerror("Error al guardar", str(detail)))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error de conexión", str(e)))
        threading.Thread(target=do, daemon=True).start()


# ── Stock ─────────────────────────────────────────────────────────────────────
class StockPanel(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=C["bg"])
        self._all_items = []
        self._solo_criticos = False
        self._build()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 4))
        ctk.CTkLabel(hdr, text="📦  Stock / Inventario",
                     font=("Segoe UI", 22, "bold"), text_color=C["text"]).pack(side="left")

        # Toolbar
        tb = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=10, height=52,
                          border_width=1, border_color=C["border"])
        tb.pack(fill="x", padx=24, pady=4)
        tb.pack_propagate(False)

        btn(tb, "↺ Actualizar", self.load, C["border"]).pack(side="right", padx=12)

        self._criticos_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(tb, text="Solo críticos (agotados + bajo stock)",
                        variable=self._criticos_var,
                        font=("Segoe UI", 11), text_color=C["text"],
                        command=self._toggle_filtro).pack(side="left", padx=16)

        # Resumen bar
        self._resumen_lbl = ctk.CTkLabel(self, text="",
                                          font=("Segoe UI", 11), text_color=C["muted"])
        self._resumen_lbl.pack(anchor="w", padx=28, pady=(4, 0))

        # Tabla
        cols = ["Código", "Descripción", "Stock actual", "Precio unit.", "Estado"]
        widths = [100, 300, 110, 130, 100]
        tf, self.tree = make_table(self, cols, widths)
        tf.pack(fill="both", expand=True, padx=24, pady=(4, 8))

        # Leyenda
        leg = ctk.CTkFrame(self, fg_color="transparent")
        leg.pack(fill="x", padx=24, pady=(0, 8))
        for color, label in [(C["danger"], "Sin stock"), (C["warning"], "Stock bajo (< 5)"),
                              (C["success"], "Normal")]:
            f = ctk.CTkFrame(leg, fg_color="transparent")
            f.pack(side="left", padx=8)
            ctk.CTkFrame(f, fg_color=color, width=14, height=14, corner_radius=3).pack(side="left")
            ctk.CTkLabel(f, text=f"  {label}", font=("Segoe UI", 10),
                         text_color=C["muted"]).pack(side="left")

        self.load()

    def load(self):
        def do():
            try:
                r = client.get("/productos", params={"activo": "true", "limit": 500})
                items = r.json() if r.status_code == 200 and isinstance(r.json(), list) else []
                self.after(0, lambda: self._set_data(items))
            except Exception as e:
                self.after(0, lambda: toast(self, f"Error al cargar stock: {e}", False))
        threading.Thread(target=do, daemon=True).start()

    def _set_data(self, items):
        self._all_items = items
        self._render()

    def _toggle_filtro(self):
        self._solo_criticos = self._criticos_var.get()
        self._render()

    def _render(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        agotados = bajo = normales = 0
        for p in self._all_items:
            stk = float(p.get("stock") or 0)
            if stk == 0:
                estado = "Agotado"
                agotados += 1
            elif stk < 5:
                estado = "Bajo stock"
                bajo += 1
            else:
                estado = "Normal"
                normales += 1

        total = len(self._all_items)
        self._resumen_lbl.configure(
            text=f"Total: {total} productos  |  🔴 Sin stock: {agotados}  |  🟡 Bajo stock: {bajo}  |  🟢 Normal: {normales}"
        )

        # Leyenda de colores en el Treeview se hace por tags
        self.tree.tag_configure("agotado", foreground=C["danger"])
        self.tree.tag_configure("bajo",    foreground=C["warning"])
        self.tree.tag_configure("normal",  foreground=C["success"])

        for p in self._all_items:
            stk = float(p.get("stock") or 0)
            if stk == 0:
                estado = "Agotado"; tag = "agotado"
            elif stk < 5:
                estado = "Bajo stock"; tag = "bajo"
            else:
                estado = "Normal"; tag = "normal"

            if self._solo_criticos and tag == "normal":
                continue

            self.tree.insert("", "end", tags=(tag,), values=(
                p.get("codigo", "—"),
                p.get("descripcion", ""),
                f"{stk:g}",
                gs(p.get("precio_unitario", 0)),
                estado
            ))

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
                r = client.post("/caja/cerrar", json={})
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
        payload = {
            "mov_tipo": self.mv_tipo.get().lower(),
            "mov_monto": monto,
            "mov_concepto": self.mv_concepto.get() or "Sin concepto"
        }
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
        self.transient(parent)
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
        payload = {"caj_usuario": self.usuario.get() or "admin", "caj_saldoinicial": saldo}
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

        btn(row,"Ventas período",  self._ventas,        C["accent"],  "📊").pack(side="left",padx=8)
        btn(row,"Más Vendidos",    self._mas_vendidos,  C["success"], "🏆").pack(side="left",padx=4)
        btn(row,"Deudores",        self._deudores,      C["warning"], "⚠️").pack(side="left",padx=4)
        btn(row,"Reporte de Stock",self._reporte_stock, C["accent2"], "📦").pack(side="left",padx=4)

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

    def _reporte_stock(self):
        def do():
            try:
                r = client.get("/reportes/stock")
                if r.status_code == 200:
                    data = r.json()
                    self.after(0, lambda: self._show_stock(data))
                else:
                    self.after(0, lambda: messagebox.showerror("Error", "No se pudo cargar el reporte de stock"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=do, daemon=True).start()

    def _show_stock(self, data):
        self._clear()
        self.result_lbl.configure(text="📦 Reporte de Stock")
        agotados = sum(1 for p in data if p.get("estado") == "agotado")
        bajos    = sum(1 for p in data if p.get("estado") == "bajo")
        for item in data:
            estado = item.get("estado", "")
            estado_lbl = "🔴 Agotado" if estado == "agotado" else "🟡 Bajo" if estado == "bajo" else "🟢 Normal"
            self.tree.insert("", "end", values=(
                item.get("codigo","—"),
                item.get("descripcion",""),
                f"{item.get('stock', 0):g}",
                estado_lbl
            ))
        apply_zebra(self.tree)
        if agotados or bajos:
            self.result_lbl.configure(
                text=f"📦 Reporte de Stock  —  🔴 Agotados: {agotados}  |  🟡 Bajo stock: {bajos}"
            )

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
        if not messagebox.askyesno("Eliminar logo", "¿Seguro que desea eliminar el logo actual?"):
            return
        try:
            _logo_asset = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "LOGO-CV.jpg")
            if os.path.exists(_logo_asset):
                os.remove(_logo_asset)
            # Actualizar preview en configuración
            self._logo_preview_lbl.configure(image="", text="[Sin logo]")
            self._logo_name_lbl.configure(text="  No cargado")
            # Actualizar sidebar y header en tiempo real
            app = self.winfo_toplevel()
            if hasattr(app, '_sidebar') and hasattr(app._sidebar, '_sidebar_logo_lbl'):
                app._sidebar._sidebar_logo_lbl.configure(image="", text="FacturaPY")
            if hasattr(app, '_header_logo_lbl'):
                app._header_logo_lbl.configure(image="", text="")
                app._header_logo_lbl.pack_forget()
            toast(self, "Logo eliminado correctamente")
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
            # Actualizar preview en configuración
            new_img = _load_logo(120, 40)
            if new_img:
                self._logo_preview_lbl.configure(image=new_img, text="")
            nombre = os.path.basename(ruta)
            self._logo_name_lbl.configure(text=f"  {nombre}")
            # Actualizar sidebar y header en tiempo real
            app = self.winfo_toplevel()
            if new_img:
                if hasattr(app, '_sidebar') and hasattr(app._sidebar, '_sidebar_logo_lbl'):
                    sidebar_img = _load_logo(120, 40)
                    app._sidebar._sidebar_logo_lbl.configure(image=sidebar_img, text="")
                if hasattr(app, '_header_logo_lbl'):
                    header_img = _load_logo(120, 40)
                    app._header_logo_lbl.configure(image=header_img, text="")
                    app._header_logo_lbl.pack(side="left", before=app._header_logo_lbl.master.winfo_children()[0])
            toast(self, "Logo actualizado correctamente")
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
    "Inicio":         DashboardPanel,
    "Facturas":       FacturasPanel,
    "Clientes":       ClientesPanel,
    "Productos":      ProductosPanel,
    "Proveedores":    ProveedoresPanel,
    "Stock":          StockPanel,
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
        self._header_logo_lbl = ctk.CTkLabel(h_left, image=logo_img if logo_img else None,
                                              text="" if logo_img else "")
        if logo_img:
            self._header_logo_lbl.pack(side="left")
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
        self._sidebar.select("Inicio")

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
