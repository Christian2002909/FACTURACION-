# Microservicio SIFEN Node.js

Microservicio que expone endpoints HTTP para generar, firmar y enviar Documentos Electrónicos (DE) a SIFEN (Servicio de Impuestos Electrónicos) de Paraguay.

## Requisitos

- Node.js 14+ 
- npm

## Instalación

```bash
cd sifen-service
npm install
```

## Librerías Oficiales DNIT

Este microservicio usa las librerías oficiales de código abierto de DNIT:

- `facturacionelectronicapy-xmlgen` - Genera XML según Manual Técnico SIFEN v150
- `facturacionelectronicapy-xmlsign` - Firma XML con certificado PKCS#12
- `facturacionelectronicapy-setapi` - Envía DE al webservice SOAP de SIFEN

Documentación: https://www.dnit.gov.py/web/e-kuatia/documentacion

## Uso

Iniciar el microservicio:

```bash
npm start
```

El servicio escucha en `http://127.0.0.1:3001` (solo localhost por seguridad).

## Endpoints

### POST /generar-xml
Genera XML del Documento Electrónico.

Request:
```json
{
  "params": { ... },
  "data": { ... }
}
```

Response:
```json
{
  "xml": "<?xml version=\"1.0\"?>..."
}
```

### POST /firmar-xml
Firma el XML con certificado PKCS#12.

Request:
```json
{
  "xml": "<?xml version=\"1.0\"?>...",
  "certPath": "data/certificados/cert.p12",
  "certPassword": "PASSWORD"
}
```

Response:
```json
{
  "xmlFirmado": "<?xml version=\"1.0\"?>..."
}
```

### POST /enviar-sifen
Envía el DE firmado a SIFEN.

Request:
```json
{
  "xml": "<?xml version=\"1.0\"?>...",
  "ambiente": "test"
}
```

Response:
```json
{
  "cdc": "...",
  "estado": "Aprobado",
  "protocolo": "...",
  "mensaje": "..."
}
```

### POST /cancelar
Cancela un DE aprobado en SIFEN.

Request:
```json
{
  "cdc": "...",
  "motivo": "...",
  "params": { ... },
  "ambiente": "test"
}
```

### POST /consultar
Consulta estado de un DE en SIFEN.

Request:
```json
{
  "cdc": "...",
  "ambiente": "test"
}
```

## Notas de Seguridad

- El servicio solo escucha en localhost (127.0.0.1) por defecto
- Nunca exponer este servicio a internet directamente
- El certificado PKCS#12 debe estar protegido (no versionado en git)
