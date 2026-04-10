from datetime import date
from sqlalchemy.orm import Session
from app.core.exceptions import TimbradoVencidoError


def obtener_siguiente_numero(db: Session) -> tuple[str, str, str, str]:
    """
    Asigna y retorna el siguiente número de factura de forma atómica.
    Retorna: (timbrado, establecimiento, punto_expedicion, numero_formateado)
    """
    from app.models.empresa import Empresa

    empresa = db.query(Empresa).with_for_update().filter(Empresa.id == 1).first()
    if not empresa:
        raise ValueError("La empresa no está configurada")

    hoy = date.today()
    if not (empresa.timbrado_fecha_inicio <= hoy <= empresa.timbrado_fecha_fin):
        raise TimbradoVencidoError(
            f"El timbrado {empresa.timbrado} está vencido (vigente hasta {empresa.timbrado_fecha_fin})"
        )

    numero = empresa.numero_actual
    empresa.numero_actual = numero + 1
    db.flush()

    numero_str = str(numero).zfill(7)
    return empresa.timbrado, empresa.establecimiento, empresa.punto_expedicion, numero_str


def formatear_numero_completo(establecimiento: str, punto_expedicion: str, numero: str) -> str:
    return f"{establecimiento}-{punto_expedicion}-{numero}"
