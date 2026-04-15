# Testing Agents - Sistema de Facturación Paraguay

## Agentes de Testing Habilitados

Los siguientes agentes especializados en testing están activos para garantizar la calidad del sistema de facturación:

### 1. **Code Reviewer**
- Revisión de pruebas unitarias
- Validación de cobertura de tests
- Identificación de gaps en testing
- Mejoras en la calidad de code

### 2. **SRE (Site Reliability Engineer)**
- Observabilidad y monitoreo
- SLOs y error budgets
- Estrategias de testing en producción
- Chaos engineering y resilience testing

### 3. **Security Engineer**
- Testing de seguridad
- Pruebas de penetración
- Validación de inputs
- Tests de vulnerabilidades

### 4. **Backend Architect**
- Testing de APIs
- Validación de schemas
- Tests de integración
- Performance testing

### 5. **DevOps Automator**
- Testing en CI/CD
- Automatización de suite de tests
- Testing de infrastructure
- Deployment testing

## Cobertura de Testing

### Unit Tests
- `tests/test_validators.py`: 20 tests para validadores Paraguay
- `tests/test_auth_service.py`: 14 tests para autenticación
- `tests/test_schemas.py`: 33 tests para validación Pydantic

### Integration Tests
- `tests/test_routers_api.py`: 32 tests de endpoints
- Tests de endpoints auth, clientes, productos, facturas, pagos

### Total: 109+ tests automatizados

## Cómo Usar los Agentes de Testing

Para invocar un agente especializado en testing:

```
@SRE - Para observabilidad y confiabilidad
@Code Reviewer - Para validar cobertura de tests
@Security Engineer - Para testing de seguridad
@Backend Architect - Para testing de APIs
@DevOps Automator - Para CI/CD testing
```

### Ejemplos de Uso

**Testing de Seguridad:**
```
@Security Engineer: Realiza testing de seguridad en los 
endpoints de autenticación y pagos del sistema
```

**Cobertura de Tests:**
```
@Code Reviewer: Analiza la cobertura de tests actual
e identifica áreas sin testing
```

**Performance Testing:**
```
@SRE: Diseña tests de carga y performance para 
validar que los endpoints cumplan SLOs
```

## Métricas de Testing Habilitadas

- **Cobertura de código**: pytest con coverage
- **Tests por módulo**:
  - Core validators: 20 tests
  - Auth service: 14 tests
  - Pydantic schemas: 33 tests
  - API routers: 32 tests + 10 adicionales

- **Estrategias de testing**:
  - Unit testing
  - Integration testing
  - Schema validation testing
  - API endpoint testing

## Configuración de Testing

### Pytest Configuration
- Database: SQLite in-memory con StaticPool
- Fixtures: conftest.py con setup/teardown automático
- Mock data: Cliente, Empresa, Producto, Factura de prueba

### Test Execution
```bash
# Ejecutar todos los tests
pytest tests/ -v

# Ejecutar con cobertura
pytest tests/ --cov=app --cov-report=html

# Tests específicos
pytest tests/test_validators.py -v
pytest tests/test_routers_api.py -v
```

## Estado: ACTIVO ✓

Última actualización: 2026-04-15
Rama: `claude/analyze-repo-PhRyC`
