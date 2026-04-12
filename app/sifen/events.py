"""
Eventos disparados después de operaciones de facturación.
Solo activos si SIFEN_ENABLED=true en .env Y sifen_habilitado=true para la empresa.
"""
from app.config import settings


def on_factura_emitida(factura_id: int) -> None:
    """Disparado por factura_service.emitir_factura() luego de guardar en BD."""
    if not settings.SIFEN_ENABLED:
        return

    from app.database import SessionLocal
    from app.models.factura import Factura, EstadoSIFEN
    from app.models.empresa import Empresa
    from app.sifen.client import generar_y_enviar_de

    db = SessionLocal()
    try:
        factura = db.query(Factura).filter(Factura.id == factura_id).first()
        empresa = db.query(Empresa).first()

        if not factura or not empresa:
            return

        # Verificar si SIFEN está habilitado para esta empresa
        if not empresa.sifen_habilitado:
            return

        factura.sifen_estado = EstadoSIFEN.PENDIENTE
        db.commit()

        resultado = generar_y_enviar_de(factura, empresa)
        cdc = resultado.get("cdc") or resultado.get("id")
        estado_sifen = resultado.get("estado", "")

        factura.sifen_cdc = cdc
        if "Aprobado" in estado_sifen or "aprobado" in estado_sifen:
            factura.sifen_estado = EstadoSIFEN.APROBADO
        elif "Rechazado" in estado_sifen or "rechazado" in estado_sifen:
            factura.sifen_estado = EstadoSIFEN.RECHAZADO
            factura.observacion = resultado.get("mensaje", "Rechazado por SIFEN")
        else:
            factura.sifen_estado = EstadoSIFEN.ENVIADO

        db.commit()

    except Exception as e:
        if factura:
            factura.sifen_estado = EstadoSIFEN.RECHAZADO
            factura.observacion = f"Error SIFEN: {str(e)[:200]}"
            db.commit()
    finally:
        db.close()
