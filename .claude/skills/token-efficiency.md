# Token Efficiency Skill - FacturaPY

## Propósito

Maximizar la eficiencia de tokens en las operaciones del proyeto FacturaPY, reduciendo uso innecesario sin sacrificar calidad o claridad del código.

## Principios de Eficiencia

### 1. Lectura Inteligente de Archivos
- ✅ Lee solo las secciones relevantes del archivo
- ✅ Usa `limit` y `offset` en la herramienta Read
- ✅ Agrupa múltiples lecturas relacionadas en paralelo
- ❌ No leas archivos completos innecesariamente
- ❌ No repitas lecturas del mismo archivo

### 2. Búsqueda Optimizada
- ✅ Usa Glob para búsquedas de archivos por patrón
- ✅ Usa Grep con filtros específicos (--type, glob patterns)
- ✅ Limita resultados con `head_limit`
- ❌ No uses Bash(find) o Bash(grep) innecesariamente
- ❌ No busques sin criterios específicos

### 3. Edición Eficiente
- ✅ Usa Edit para cambios puntuales
- ✅ Combina múltiples ediciones en el mismo archivo
- ✅ Usa `replace_all` para cambios globales de variables
- ❌ No reescribas archivos completos (usa Write solo para crear)
- ❌ No hagas ediciones una por una innecesariamente

### 4. Herramientas Paralelas
- ✅ Ejecuta múltiples operaciones independientes en paralelo
- ✅ Agrupa Bash commands relacionados con &&
- ✅ Paralleliza lecturas, búsquedas, ediciones sin dependencias
- ❌ No ejecutes operaciones secuencialmente si son independientes

### 5. Comunicación Concisa
- ✅ Respuestas cortas y al punto
- ✅ Código comentado solo donde sea necesario
- ✅ Usa formato Markdown eficientemente
- ❌ No repitas información
- ❌ No expliques código obvio

### 6. Git Eficiente
- ✅ Agrupa cambios relacionados en un commit
- ✅ Usa commit messages informativos pero concisos
- ✅ Push inmediatamente después de commit
- ❌ No hagas múltiples commits pequeños
- ❌ No hagas commits incompletos

### 7. Testing Eficiente
- ✅ Ejecuta tests en paralelo: `pytest -n auto`
- ✅ Ejecuta solo tests afectados
- ✅ Usa conftest.py para compartir fixtures
- ❌ No ejecutes suite completa para cambios locales
- ❌ No repitas tests que ya pasaron

## Estrategias por Tipo de Tarea

### Bug Fix (Bajo Costo de Tokens)
1. Grep para localizar el bug
2. Read la sección específica (con límite)
3. Edit para fijar en 1-2 líneas
4. Commit + push

Tokens esperados: 500-2000

### Feature Simple (Medio Costo)
1. Explore estructura relevante (Glob + Grep)
2. Read archivos relacionados en paralelo
3. Edit múltiples archivos o Write si es nuevo
4. pytest para validar
5. Commit + push

Tokens esperados: 5000-15000

### Feature Compleja (Alto Costo)
1. Usa Agent(Explore) para mapeo de dependencias
2. Solicita decisiones arquitectónicas a Software Architect
3. Implementa modularmente
4. Testing comprehensivo
5. Code review antes de merge

Tokens esperados: 20000-50000

## Optimizaciones Específicas para FacturaPY

### Base de Datos
- ✅ Usa conftest.py para fixtures reutilizables
- ✅ SQLite in-memory para tests rápidos
- ❌ No crees BD separada por test

### Validación
- ✅ Pydantic Field() validators en un lugar
- ✅ Reutiliza validadores en múltiples schemas
- ❌ No duplices lógica de validación

### Logging
- ✅ Configuración centralizada en logging_config.py
- ✅ Hereda loggers en módulos
- ❌ No crees logging.getLogger() en cada archivo

### Rate Limiting
- ✅ Decoradores @limiter en routers
- ✅ Configuración centralizada en rate_limit.py
- ❌ No definas límites hardcoded en cada endpoint

### Testing
```bash
# Eficiente: todos los tests en paralelo
pytest tests/ -n auto --tb=short

# Ineficiente: tests secuenciales
pytest tests/ -v (sin -n)
```

## Métricas de Eficiencia

### Por Sesión
- **Tokens input**: < 10% de límite
- **Tokens output**: Respuestas concisas (< 2000)
- **Tiempo**: Tareas completadas en 1-2 "pasos"

### Por Archivo
- **Lecturas**: Máximo 2-3 por archivo
- **Ediciones**: Máximo 2-3 sets de cambios
- **Tamaño**: Cambios focalizados (< 100 líneas por sesión)

## Checklist Pre-Operación

Antes de cada operación:

- [ ] ¿Necesito realmente leer este archivo?
- [ ] ¿Puedo combinar esta lectura con otra?
- [ ] ¿Puedo ejecutar esto en paralelo?
- [ ] ¿Puedo usar una herramienta más eficiente?
- [ ] ¿Necesito responder verbosamente o puedo ser conciso?
- [ ] ¿Hay fixtures o funciones reutilizables?

## Activación

Esta habilidad está **ACTIVA** en el proyecto FacturaPY.

Aplicar en todas las operaciones:
- Lectures de código
- Ediciones de archivo
- Búsquedas de patrón
- Ejecución de tests
- Commits y pushes
- Comunicación con usuario

---

**Status**: ✅ ENABLED
**Última actualización**: 2026-04-15
**Aplicable a**: Todos los agentes del proyecto FacturaPY
