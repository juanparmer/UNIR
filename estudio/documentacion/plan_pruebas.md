# Plan de pruebas

Objetivo: comprobar flujos críticos del gestor local y registrar evidencias reproducibles. Estrategia: validación de datos, repositorio SQLite real, servidor HTTP real y navegador Edge mediante Playwright. Los tests no utilizan datos personales.

| Prioridad | Funcionalidad y riesgo | Verificación |
| --- | --- | --- |
| Alta | Crear y editar sin corromper datos | Validación, CRUD y edición inválida sin cambios |
| Alta | Persistencia y liberación de archivos | Nueva instancia, reinicio HTTP y limpieza de temporales |
| Alta | Completar, reabrir y eliminar | Estados y flujo completo de interfaz, cancelación de borrado |
| Alta | Entradas inválidas o con código | Fechas, tamaños, tipos, SQL como texto y HTML sin ejecución |
| Media | Búsqueda y filtros | Combinación por título, asignatura, notas, estado y prioridad |
| Alta | Filtro fuera de plazo | Ayer, hoy, mañana, sin fecha, completada y combinación |
| Media | Presentación y errores | Móvil sin desbordamiento, foco, Escape y fallo de conexión |

Implementación: 8 métodos de validación, 12 de repositorio y 13 de API en `tests/test_app.py`; 9 métodos de navegador en `tests/browser_checks.py`. Algunos métodos contienen subcasos; el total comunicado cuenta métodos, no cada aserción.

Criterio de salida: cero errores y cero fallos en ambas suites, sin omisiones; comprobar capturas y documentar límites. No se mide cobertura de líneas. No se afirma cobertura exhaustiva ni compatibilidad completa entre navegadores.

Ejecución: `python run_tests.py`; para interfaz, instalar `requirements-dev.txt` y ejecutar `python tests/browser_checks.py`. Véase el README para entorno virtual y requisitos.

Evidencias históricas: fallo inicial de conexiones en `primera_ejecucion.log`; resolución en `pruebas.log`; resultado de la ampliación de interfaz en `interfaz.log`. Cada resumen JSON incluye fecha UTC. Las capturas contienen datos de ejemplo.
