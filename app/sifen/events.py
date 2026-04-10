"""Hook llamado después de emitir una factura. No-op hasta implementar SIFEN."""
from app.config import settings


def on_factura_emitida(factura_id: int) -> None:
    if not settings.SIFEN_ENABLED:
        return
    # TODO Fase 5: construir XML, firmar y enviar a e-kuatia
    raise NotImplementedError("SIFEN no implementado aún")
