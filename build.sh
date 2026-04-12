#!/bin/bash
# Script de compilación para Sistema de Facturación Paraguay
# Uso: ./build.sh [--nsis]
# Sin --nsis: genera ejecutable con PyInstaller
# Con --nsis: genera instalador Windows NSIS

set -e

echo "╔════════════════════════════════════════════════════╗"
echo "║   SISTEMA DE FACTURACIÓN PARAGUAY — Build Script   ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "run.py" ]; then
    echo "❌ Error: run.py no encontrado. Ejecutar desde raíz del proyecto."
    exit 1
fi

# Instalar/actualizar dependencias
echo "📦 Instalando dependencias Python..."
pip install -r requirements.txt -q
pip install pyinstaller -q

# Limpiar builds anteriores
echo "🧹 Limpiando builds anteriores..."
rm -rf build dist *.spec

# Generar ejecutable con PyInstaller
echo "🔨 Generando ejecutable con PyInstaller..."
pyinstaller \
    --onedir \
    --windowed \
    --name "FACTURACION" \
    --icon=app/gui/assets/icon.ico 2>/dev/null || \
pyinstaller \
    --onedir \
    --windowed \
    --name "FACTURACION" \
    run.py

echo "✅ Ejecutable generado en: dist/FACTURACION/"

# Si se pide NSIS, generar instalador
if [ "$1" = "--nsis" ]; then
    echo ""
    echo "📦 Generando instalador NSIS..."

    if ! command -v makensis &> /dev/null; then
        echo "❌ Error: NSIS no está instalado."
        echo "   Instalar: sudo apt install nsis"
        exit 1
    fi

    # Verificar que el ejecutable existe
    if [ ! -d "dist/FACTURACION" ]; then
        echo "❌ Error: dist/FACTURACION no encontrado"
        exit 1
    fi

    # Generar instalador
    makensis instalador.nsi

    if [ -f "dist/FACTURACION-setup.exe" ]; then
        echo "✅ Instalador generado: dist/FACTURACION-setup.exe"
        ls -lh dist/FACTURACION-setup.exe
    else
        echo "❌ Error generando instalador NSIS"
        exit 1
    fi
fi

echo ""
echo "╔════════════════════════════════════════════════════╗"
echo "║                    ✅ Listo                        ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""
echo "Próximos pasos:"
echo "  1. Probar en Linux: python run.py"
echo "  2. Generar instalador: ./build.sh --nsis"
echo "  3. Distribuir: dist/FACTURACION-setup.exe a clientes Windows"
echo ""
