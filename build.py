#!/usr/bin/env python3
"""
FacturaPY — Build Script
Uso: python build.py [--nsis]
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_header(msg):
    print("\n" + "="*60)
    print(f"  {msg}")
    print("="*60)

def run_command(cmd, description=""):
    """Ejecuta comando y retorna True si tuvo éxito."""
    if description:
        print(f"\n📦 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Error: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"❌ Error ejecutando comando: {e}")
        return False

def main():
    print_header("FacturaPY — Build Script")

    # Verificar directorio
    if not Path("run.py").exists():
        print("❌ Error: run.py no encontrado. Ejecutar desde raíz del proyecto.")
        sys.exit(1)

    # Instalar dependencias
    if not run_command("pip install -r requirements.txt -q", "Instalando dependencias Python"):
        sys.exit(1)

    if not run_command("pip install pyinstaller -q", "Instalando PyInstaller"):
        sys.exit(1)

    # Limpiar builds anteriores
    print("\n🧹 Limpiando builds anteriores...")
    for item in ["build", "dist"]:
        if Path(item).exists():
            shutil.rmtree(item)
    for f in Path(".").glob("*.spec"):
        f.unlink()

    # Convertir logo a .ico para el ejecutable
    icon_flag = ""
    try:
        from PIL import Image
        img = Image.open("app/assets/LOGO-CV.jpg")
        img.save("app/assets/favicon.ico", format="ICO", sizes=[(256,256),(128,128),(64,64),(32,32),(16,16)])
        icon_flag = "--icon app/assets/favicon.ico "
        print("✓ Ícono generado desde LOGO-CV.jpg")
    except Exception as e:
        print(f"⚠ No se pudo generar ícono: {e}")

    # Generar ejecutable
    print("\n🔨 Generando ejecutable con PyInstaller...")
    cmd = (
        "pyinstaller "
        "--onedir "
        "--windowed "
        "--name FacturaPY "
        f"{icon_flag}"
        "--add-data 'app/assets:app/assets' "
        "run.py"
    )
    if not run_command(cmd, "PyInstaller"):
        sys.exit(1)

    print(f"✅ Ejecutable generado en: dist/FacturaPY/")

    # Si se pide NSIS
    if "--nsis" in sys.argv:
        print_header("Generando Instalador NSIS")

        # Verificar NSIS
        result = subprocess.run("which makensis", shell=True, capture_output=True)
        if result.returncode != 0:
            print("❌ Error: NSIS no está instalado.")
            print("   Instalar: sudo apt install nsis")
            sys.exit(1)

        # Verificar ejecutable
        if not Path("dist/FacturaPY").exists():
            print("❌ Error: dist/FacturaPY no encontrado")
            sys.exit(1)

        # Generar instalador
        if not run_command("makensis instalador.nsi", "NSIS"):
            sys.exit(1)

        if Path("dist/FacturaPY-setup.exe").exists():
            size = Path("dist/FacturaPY-setup.exe").stat().st_size / (1024*1024)
            print(f"\n✅ Instalador generado: dist/FacturaPY-setup.exe ({size:.1f}MB)")
        else:
            print("❌ Error generando instalador NSIS")
            sys.exit(1)

    print_header("✅ Listo")
    print("\nPróximos pasos:")
    print("  1. Probar en Linux: python run.py")
    print("  2. Generar instalador: python build.py --nsis")
    print("  3. Distribuir: dist/FacturaPY-setup.exe a clientes Windows")
    print()

if __name__ == "__main__":
    main()
