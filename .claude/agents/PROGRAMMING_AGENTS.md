# Programming Agents - Sistema de Facturación Paraguay

## Agentes de Programación Habilitados

Los siguientes agentes especializados en programación están activos para el desarrollo y mejora del sistema:

### 1. **Senior Developer**
- Implementación de features complejas
- Optimización de código Python/FastAPI
- Mejoras de rendimiento
- Patrones avanzados de desarrollo

### 2. **Backend Architect**
- Diseño de APIs FastAPI
- Optimización de schemas Pydantic
- Arquitectura de servicios
- Estructura de base de datos

### 3. **Code Reviewer**
- Revisión de código
- Detección de vulnerabilidades
- Mejoras de mantenibilidad
- Buenas prácticas Python

### 4. **Software Architect**
- Decisiones arquitectónicas
- Patrones de diseño
- Refactoring estructural
- Optimización de componentes

### 5. **DevOps Automator**
- CI/CD pipeline
- Automatización de deployments
- Configuration management
- Infrastructure as Code

### 6. **Security Engineer**
- Validación de seguridad
- Testing de vulnerabilidades
- Implementación segura
- Compliance y auditoría

## Stack Técnico Habilitado

### Backend
- **Framework**: FastAPI 0.100+
- **ORM**: SQLAlchemy 2.0+
- **Validation**: Pydantic v2
- **Auth**: JWT + bcrypt
- **Database**: SQLite con WAL mode
- **Rate Limiting**: slowapi

### Servicios
- **Logging**: JSON structured logging
- **Audit**: Sistema de auditoría financiera
- **Validation**: Validadores Paraguay (RUC, cédula, teléfono)

### Testing
- **Framework**: pytest
- **Coverage**: pytest-cov
- **Fixtures**: Bases de datos in-memory

## Cómo Usar los Agentes de Programación

Para invocar un agente especializado:

```
@Senior Developer - Para features complejas
@Backend Architect - Para diseño de APIs
@Code Reviewer - Para calidad de código
@Software Architect - Para arquitectura
@DevOps Automator - Para automatización
@Security Engineer - Para seguridad
```

### Ejemplos de Uso

**Implementar Feature Compleja:**
```
@Senior Developer: Implementa autenticación multi-factor
en el sistema de facturación con soporte para OTP
```

**Optimizar APIs:**
```
@Backend Architect: Rediseña los endpoints de facturas
para mejorar performance y agregar paginación
```

**Code Quality:**
```
@Code Reviewer: Revisa los últimos cambios e identifica
deuda técnica y mejoras de mantenibilidad
```

**Arquitectura:**
```
@Software Architect: Diseña la integración con SIFEN
manteniendo separación de concerns
```

## Áreas de Programación Habilitadas

### 1. Núcleo (app/core/)
- `logging_config.py`: Sistema de logging centralizado
- `rate_limit.py`: Protección de endpoints
- `validators.py`: Validadores Paraguay
- `security.py`: Funciones de seguridad

### 2. Modelos (app/models/)
- Empresa, Cliente, Producto, Factura
- DetalleFactura, Pago
- Enums: TipoDocumento, EstadoFactura, TasaIVA

### 3. Schemas Pydantic (app/schemas/)
- FacturaCreate/Update, DetalleFacturaCreate
- ProductoCreate, ClienteCreate
- PagoCreate, EmpresaCreate
- Validaciones de negocio integradas

### 4. Servicios (app/services/)
- `auth_service.py`: JWT, bcrypt, tokens
- `factura_service.py`: Lógica de facturas
- `pago_service.py`: Cálculo de pagos
- `empresa_service.py`: Configuración empresa

### 5. Routers API (app/routers/)
- `/api/v1/auth`: Login, refresh, logout
- `/api/v1/clientes`: CRUD de clientes
- `/api/v1/productos`: CRUD de productos
- `/api/v1/facturas`: CRUD y emisión de facturas
- `/api/v1/pagos`: Registro de pagos

### 6. Base de Datos (app/database/)
- SQLAlchemy ORM configuration
- Migrations con Alembic
- WAL mode para SQLite

### 7. Testing (tests/)
- `conftest.py`: Fixtures compartidas
- `test_validators.py`: Validadores
- `test_auth_service.py`: Autenticación
- `test_schemas.py`: Pydantic validation
- `test_routers_api.py`: Endpoints

## Flujo de Desarrollo

### 1. Feature Request
Especificar el feature con contexto de negocio

### 2. Design Review
Software Architect revisa y aprueba diseño

### 3. Implementation
Senior Developer implementa el feature

### 4. Testing
Tests unitarios + integración

### 5. Security Review
Security Engineer valida seguridad

### 6. Code Review
Code Reviewer aprueba cambios

### 7. CI/CD
DevOps Automator automatiza deployment

## Requisitos de Código

- Python 3.11+
- Type hints en funciones
- Docstrings en classes/functions
- Tests para cada feature
- Validación en límites
- Logging de operaciones críticas
- Auditoría para transacciones financieras

## Comandos Útiles

```bash
# Ejecutar tests
pytest tests/ -v

# Linting
flake8 app/ tests/

# Type checking
mypy app/

# Cobertura
pytest --cov=app tests/

# Ejecutar servidor
uvicorn app.main:app --reload --port 8000
```

## Estado: ACTIVO ✓

Última actualización: 2026-04-15
Rama: `claude/analyze-repo-PhRyC`
Commits: 5 improvements implemented
