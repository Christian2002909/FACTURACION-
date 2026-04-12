"""
Punto de entrada principal — lanza el servidor FastAPI en background
y abre la interfaz gráfica de escritorio.
"""
import os
import subprocess
import sys
import time
import threading
import requests
from app.gui.main_window import App


# ── Crear directorios necesarios ───────────────────────────────────────────
os.makedirs("data/facturas", exist_ok=True)
os.makedirs("data/certificados", exist_ok=True)
os.makedirs("data/backups", exist_ok=True)


def start_server():
    subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8000"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


def wait_for_server(timeout=15):
    for _ in range(timeout * 2):
        try:
            requests.get("http://localhost:8000/", timeout=1)
            return True
        except Exception:
            time.sleep(0.5)
    return False


if __name__ == "__main__":
    print("Iniciando servidor...")
    threading.Thread(target=start_server, daemon=True).start()

    if not wait_for_server():
        print("Advertencia: servidor no respondió — continuando igual")

    App().mainloop()
