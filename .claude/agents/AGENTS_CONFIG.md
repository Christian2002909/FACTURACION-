# Configuración Completa de Agentes - FacturaPY

## 🎯 Agentes Activados por Categoría

### Diseño (Design)
- ✅ `Software Architect` - Arquitectura del sistema
- ✅ `Frontend Developer` - Interfaz Tkinter/Web
- ✅ `Backend Architect` - APIs y base de datos
- ✅ `Code Reviewer` - Calidad de código
- ✅ `Rapid Prototyper` - MVP y prototipado ágil

### Testing (Quality Assurance)
- ✅ `Code Reviewer` - Cobertura de tests
- ✅ `SRE` - Observabilidad y confiabilidad
- ✅ `Security Engineer` - Testing de seguridad
- ✅ `Backend Architect` - Testing de APIs
- ✅ `DevOps Automator` - CI/CD testing

### Programación (Development)
- ✅ `Senior Developer` - Features complejas
- ✅ `Backend Architect` - APIs y servicios
- ✅ `Code Reviewer` - Revisión de código
- ✅ `Software Architect` - Decisiones arquitectónicas
- ✅ `DevOps Automator` - Automatización
- ✅ `Security Engineer` - Seguridad

### Skills Habilitadas
- ✅ `token-efficiency` - Optimización de tokens
- ✅ `coding-workflow` - Workflow de desarrollo
- ✅ `commit-push-pr` - Git operations
- ✅ `code-simplifier` - Simplificación de código

## 📊 Stack Técnico Soportado

```
FacturaPY (Python 3.11+)
├── Backend: FastAPI + SQLAlchemy + Pydantic
├── Frontend: CustomTkinter GUI
├── Database: SQLite (WAL mode)
├── Testing: pytest + fixtures
├── Security: JWT + bcrypt
├── Logging: JSON structured
├── Rate Limiting: slowapi
└── Validation: Paraguay-specific (RUC, cédula)
```

## 🚀 Flujo de Trabajo Recomendado

### Tarea Simple (Bug Fix)
```
→ Code Reviewer (validar)
→ Senior Developer (implementar)
→ Code Reviewer (revisar)
→ Push a rama
```

### Tarea Media (Feature)
```
→ Software Architect (diseño)
→ Backend Architect (APIs)
→ Senior Developer (implementar)
→ Code Reviewer (revisar)
→ DevOps Automator (CI/CD)
→ Push y PR
```

### Tarea Compleja (Arquitectura)
```
→ Software Architect (diseño)
→ Backend Architect (APIs + datos)
→ Senior Developer (implementar)
→ Security Engineer (seguridad)
→ SRE (confiabilidad)
→ Code Reviewer (calidad)
→ DevOps Automator (deployment)
→ PR con revisión completa
```

## 📝 Cómo Invocar Agentes

### Desde Claude Code CLI
```bash
# Activar un agente específico
@Backend Architect: Optimiza los endpoints de facturas

# Múltiples agentes
@Software Architect y @Backend Architect: Rediseña el módulo de pagos
```

### En Mensajes Conversacionales
```
Necesito implementar un nuevo endpoint. 
@Senior Developer: Crea /api/v1/reportes/ventas con validación completa
```

## 🔍 Matriz de Responsabilidades

| Tarea | Agente Responsable | Validadores |
|-------|-------------------|------------|
| Arquitectura | Software Architect | Backend Architect, Code Reviewer |
| API Design | Backend Architect | Software Architect, Code Reviewer |
| Implementación | Senior Developer | Code Reviewer |
| Calidad | Code Reviewer | Senior Developer |
| Seguridad | Security Engineer | Code Reviewer |
| Testing | SRE | Backend Architect |
| CI/CD | DevOps Automator | Code Reviewer |
| UI/UX | Frontend Developer | Code Reviewer |

## ⚙️ Configuración de Cada Agente

### Software Architect
**Responsabilidades:**
- Diseño arquitectónico general
- Patrones de diseño
- Decisiones estratégicas
- Refactoring estructural

**Invoca cuando:**
- Diseñar feature nueva
- Refactorizar módulo completo
- Decidir nuevas tecnologías

### Backend Architect
**Responsabilidades:**
- Diseño de APIs
- Estructura de BD
- Optimización de performance
- Seguridad de datos

**Invoca cuando:**
- Diseñar nuevos endpoints
- Cambios en schema
- Problemas de performance

### Senior Developer
**Responsabilidades:**
- Implementación de code
- Optimizaciones Python
- Patrón avanzados
- Debugging complejo

**Invoca cuando:**
- Implementar feature
- Optimizar código existente
- Resolver bugs complejos

### Code Reviewer
**Responsabilidades:**
- Revisión de código
- Detección de vulnerabilidades
- Mejoras de mantenibilidad
- Validación de tests

**Invoca cuando:**
- Revisar PR
- Validar cobertura
- Auditar seguridad

### Security Engineer
**Responsabilidades:**
- Validación de seguridad
- Testing de vulnerabilidades
- Implementación segura
- Compliance

**Invoka cuando:**
- Revisar feature sensible
- Implementar autenticación
- Validar endpoints de pago

### SRE (Site Reliability Engineer)
**Responsabilidades:**
- Observabilidad
- SLOs y monitoring
- Resilience testing
- Chaos engineering

**Invoca cuando:**
- Definir SLOs
- Performance testing
- Estrategia de monitoreo

### DevOps Automator
**Responsabilidades:**
- CI/CD pipeline
- Automatización
- Infrastructure
- Deployments

**Invoca cuando:**
- Configurar CI/CD
- Automatizar tests
- Deploy procedures

### Frontend Developer
**Responsabilidades:**
- UI/UX design
- Tkinter components
- Formularios
- Validación UI

**Invoka cuando:**
- Redesign GUI
- Componentes interactivos
- Mejoras UX

## 📦 Proyecto: FacturaPY

**Rama:** `claude/analyze-repo-PhRyC`
**Estado:** 5/5 mejoras implementadas ✅
**Tests:** 109 tests, 100% pasando ✅
**Coverage:** Validadores, Auth, Schemas, Routers ✅

## 🔄 Ciclo de Desarrollo

```
Idea → Diseño → Implementación → Testing → Seguridad → Review → Deploy
  ↓       ↓          ↓             ↓         ↓         ↓        ↓
  SA      BA         SD           SRE       SE        CR       DA
```

Donde:
- SA = Software Architect
- BA = Backend Architect
- SD = Senior Developer
- SRE = Site Reliability Engineer
- SE = Security Engineer
- CR = Code Reviewer
- DA = DevOps Automator

## 🎓 Ejemplos de Uso

### Ejemplo 1: Bug Fix
```
Usuario: Hay un error al validar RUC con guión
@Code Reviewer: Encuentra dónde está el bug
@Senior Developer: Implementa el fix
```

### Ejemplo 2: Nuevo Feature
```
Usuario: Necesitamos reportes de ventas
@Software Architect: Diseña la arquitectura
@Backend Architect: Define los endpoints
@Senior Developer: Implementa reportes
@SRE: Define SLOs para reportes
@Code Reviewer: Valida la calidad
```

### Ejemplo 3: Mejora de Performance
```
Usuario: Los reportes son lentos
@SRE: Analiza el performance
@Backend Architect: Optimiza consultas
@Senior Developer: Implementa cache
@Code Reviewer: Valida solución
```

## ✅ Checklist de Activación

- [x] Agentes de Diseño configurados (DESIGN_AGENTS.md)
- [x] Agentes de Testing configurados (TESTING_AGENTS.md)
- [x] Agentes de Programación configurados (PROGRAMMING_AGENTS.md)
- [x] Skill de token-efficiency habilitado
- [x] Documentación de agentes completada
- [x] Ejemplos de uso documentados
- [x] Matriz de responsabilidades definida

## 📞 Soporte

Para usar los agentes:
1. Menciona el agente en tu mensaje: `@AgentName`
2. Describe claramente la tarea
3. El agente asumirá el rol especializado
4. Coordina entre agentes si es necesario

---

**Status**: ✅ COMPLETAMENTE ACTIVADO
**Última actualización**: 2026-04-15
**Autores**: Agentes de IA + Equipo de Desarrollo
