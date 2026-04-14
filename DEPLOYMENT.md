# Guía de Despliegue — FacturaPY

## En tu Linux (Cahyos KDE)

### 1. Probar la aplicación

```bash
python run.py
```

Se abre la GUI Tkinter. Puedes:
- Crear empresa
- Agregar clientes
- Emitir facturas autoimpresa
- Generar PDFs

### 2. Generar ejecutable Windows

```bash
./build.sh
```

Crea: `dist/FacturaPY/FacturaPY.exe` (≈150MB con Python embebido)

### 3. Generar instalador Windows

```bash
# Primero instalar NSIS
sudo apt install nsis

# Luego generar instalador
./build.sh --nsis
```

Crea: `dist/FacturaPY-setup.exe` (≈80MB, comprimido)

---

## Para tus Clientes (Windows)

### Instalación

1. Cliente descarga `FacturaPY-setup.exe`
2. Ejecuta el instalador
3. Se instala en `C:\Program Files\FacturaPY\`
4. Crea acceso directo en Inicio y Escritorio
5. Al abrir, configura su empresa y empieza a facturar

### Estructura de carpetas (después de instalar)

```
C:\Program Files\FacturaPY\
├── FacturaPY.exe          ← ejecutable
├── python*                   ← runtime Python embebido
└── ...

C:\Users\{Usuario}\AppData\Roaming\FacturaPY\
└── data/
    ├── facturas/            ← PDFs generados
    ├── certificados/        ← Si quiere SIFEN
    └── backups/
```

### Si cliente quiere SIFEN

1. Obtiene certificado `.p12` del DNIT
2. Coloca en `C:\Users\{Usuario}\AppData\Roaming\FacturaPY\data\certificados\cert.p12`
3. Tú activas: `POST /admin/activar-sifen?empresa_id=1`
4. Cliente puede usar facturación electrónica

---

## Comandos útiles

```bash
# Probar en Linux
python run.py

# Compilar ejecutable
./build.sh

# Compilar + instalador
./build.sh --nsis

# Limpiar builds
rm -rf build dist *.spec

# Ver tamaño de archivos
ls -lh dist/
```

---

## Requisitos

**Para desarrollar (en tu Linux):**
- Python 3.11+
- pip
- tkinter
- PostgreSQL (opcional, si usas BD en lugar de SQLite)

**Para generar instalador:**
- NSIS: `sudo apt install nsis`

**Cliente necesita:**
- Windows 7+ (el .exe lleva Python embebido)
- 300MB de espacio en disco

---

## Estructura del .exe

PyInstaller genera:
- `FacturaPY.exe` - ejecutable principal
- Carpeta `_internal/` - librerías Python + dependencias
- Total: ≈150-200MB

Para distribución usar NSIS, que comprime a ≈80MB.

---

## Notas de Seguridad

- Base de datos SQLite se guarda en `%APPDATA%\FacturaPY\data\`
- Certificados digitales NUNCA en carpeta de programa
- Crear acceso restringido a certificados (permisos Windows)
- Base de datos cliente NO debe estar en Dropbox/Cloud (corrupción)

---

## Actualizar en futuro

Si haces cambios:
1. Commit en git
2. `./build.sh --nsis`
3. Distribuir nuevo `.exe` a clientes

PyInstaller regenera con último código Python.

