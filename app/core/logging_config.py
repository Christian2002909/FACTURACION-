"""
Logging centralizado — FacturaPY
Tres canales: app.log (todo), errors.log (errores), audit.log (transacciones financieras)
"""
import logging
import logging.handlers
import json
import os
from datetime import datetime, timezone
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """Formatea logs en JSON estructurado para parsing automático."""

    def format(self, record):
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if hasattr(record, "user"):
            log_data["user"] = record.user
        if hasattr(record, "factura_id"):
            log_data["factura_id"] = record.factura_id
        if hasattr(record, "cliente_id"):
            log_data["cliente_id"] = record.cliente_id
        if hasattr(record, "action"):
            log_data["action"] = record.action
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data, ensure_ascii=False)


def setup_logging():
    """Configura logging centralizado con rotación de archivos."""
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    # Evitar duplicar handlers si se llama múltiples veces
    if root_logger.handlers:
        return
    root_logger.setLevel(logging.DEBUG)

    json_fmt = JSONFormatter()

    # Handler 1: Archivo general (INFO+)
    app_handler = logging.handlers.RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(json_fmt)
    root_logger.addHandler(app_handler)

    # Handler 2: Archivo de errores (ERROR+)
    error_handler = logging.handlers.RotatingFileHandler(
        log_dir / "errors.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=10,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(json_fmt)
    root_logger.addHandler(error_handler)

    # Handler 3: Auditoría financiera (logger separado)
    audit_handler = logging.handlers.RotatingFileHandler(
        log_dir / "audit.log",
        maxBytes=50 * 1024 * 1024,
        backupCount=20,
        encoding="utf-8",
    )
    audit_handler.setFormatter(json_fmt)
    audit_logger = logging.getLogger("audit")
    audit_logger.addHandler(audit_handler)
    audit_logger.setLevel(logging.INFO)
    audit_logger.propagate = False

    # Handler 4: Consola (desarrollo)
    if os.getenv("ENVIRONMENT") != "production":
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(
            logging.Formatter("%(levelname)-8s | %(asctime)s | %(name)s | %(message)s")
        )
        root_logger.addHandler(console)
