"""
FacturaPY — Punto de entrada — sincroniza DB, lanza servidor FastAPI y abre la GUI.
"""
import os
import sys
import sqlite3
import subprocess
import threading
import time
import requests

# ── Directorios ───────────────────────────────────────────────────────────────
for d in ["data/facturas", "data/certificados", "data/backups"]:
    os.makedirs(d, exist_ok=True)


# ── Auto-sync DB (agrega columnas faltantes sin borrar datos) ─────────────────
def sync_db():
    db_path = "data/facturacion.db"
    if not os.path.exists(db_path):
        # Crear todas las tablas desde los modelos
        from app.database import engine, Base
        import app.models.empresa, app.models.cliente, app.models.producto
        import app.models.factura, app.models.proveedor, app.models.compra
        import app.models.caja, app.models.pago
        Base.metadata.create_all(bind=engine)
        return

    # Columnas que pueden faltar por diferencia entre migration y modelos
    patches = [
        ("empresa",  "sifen_habilitado", "BOOLEAN DEFAULT 0"),
        ("producto", "stock",            "INTEGER DEFAULT 0"),
        ("caja",     "caj_saldoinicial", "FLOAT DEFAULT 0"),
        ("caja",     "caj_totalingre",   "FLOAT DEFAULT 0"),
        ("caja",     "caj_totalegre",    "FLOAT DEFAULT 0"),
        ("caja",     "caj_saldofinal",   "FLOAT DEFAULT 0"),
    ]
    conn = sqlite3.connect(db_path)
    cur  = conn.cursor()
    for table, col, col_def in patches:
        try:
            cur.execute(f"PRAGMA table_info({table})")
            cols = [r[1] for r in cur.fetchall()]
            if col not in cols:
                cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_def}")
                print(f"  [DB] Columna agregada: {table}.{col}")
        except Exception:
            pass
    conn.commit()
    conn.close()


# ── Servidor FastAPI ──────────────────────────────────────────────────────────
def start_server():
    subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app",
         "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def wait_for_server(timeout=20):
    for _ in range(timeout * 2):
        try:
            requests.get("http://127.0.0.1:8000/", timeout=1)
            return True
        except Exception:
            time.sleep(0.5)
    return False


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Sincronizando base de datos...")
    sync_db()

    print("Iniciando servidor API...")
    threading.Thread(target=start_server, daemon=True).start()

    if not wait_for_server():
        print("Advertencia: servidor tardó — continuando igual")
    else:
        print("Servidor listo en http://127.0.0.1:8000")

    from app.gui.main_window import App
    App().mainloop()
