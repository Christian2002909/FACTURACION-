# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['run.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('app', 'app'),
        ('migrations', 'migrations'),
        ('alembic.ini', '.'),
    ],
    hiddenimports=[
        'uvicorn', 'uvicorn.lifespan.on', 'uvicorn.protocols.http.h11_impl',
        'uvicorn.protocols.http.httptools_impl', 'uvicorn.protocols.websockets.websockets_impl',
        'uvicorn.loops.asyncio', 'uvicorn.loops.uvloop',
        'fastapi', 'sqlalchemy', 'sqlalchemy.dialects.sqlite',
        'alembic', 'pydantic', 'passlib', 'jose', 'reportlab',
        'tkinter', 'tkinter.ttk', 'requests',
        'app.models', 'app.models.empresa', 'app.models.cliente',
        'app.models.producto', 'app.models.factura', 'app.models.detalle_factura',
        'app.models.pago', 'app.models.proveedor', 'app.models.compra',
        'app.models.devolucion', 'app.models.caja', 'app.models.cuota',
        'app.models.gasto', 'app.models.cheque',
        'app.routers.auth', 'app.routers.clientes', 'app.routers.productos',
        'app.routers.facturas', 'app.routers.pagos', 'app.routers.proveedores',
        'app.routers.compras', 'app.routers.caja', 'app.routers.reportes',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='FacturaPY',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,       # Sin ventana de terminal
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FacturaPY',
)
