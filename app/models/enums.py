"""
Enums compartidos entre modelos — sin dependencias internas.
Ubicar aquí cualquier enum usado por más de un modelo.
"""
import enum


class TasaIVA(str, enum.Enum):
    """Tasas de IVA válidas en Paraguay. El precio YA incluye el impuesto."""
    EXENTO = "0"
    CINCO = "5"
    DIEZ = "10"
