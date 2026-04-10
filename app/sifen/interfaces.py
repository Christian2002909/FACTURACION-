"""Protocols para la integración SIFEN. Implementar en Fase 5."""
from typing import Protocol


class SifenDocumentoBuilder(Protocol):
    def build(self, factura_id: int) -> bytes: ...


class SifenSigner(Protocol):
    def sign(self, xml_bytes: bytes) -> bytes: ...


class SifenClient(Protocol):
    def submit(self, signed_xml: bytes) -> dict: ...


class SifenEventHandler(Protocol):
    def on_factura_emitida(self, factura_id: int) -> None: ...
