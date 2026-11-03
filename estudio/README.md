# Estudio

Gestor de tareas de estudio creado con asistencia de IA para las actividades 1 y 2. Permite crear, editar, completar, reabrir y eliminar tareas; buscar en título, asignatura y notas; filtrar por estado, prioridad y tareas fuera de plazo. Los contadores muestran el conjunto completo de tareas, aunque haya filtros activos.

## Requisitos

- Python 3.11 o posterior, con SQLite (distribución habitual de Python).
- Un navegador moderno. Interfaz comprobada con Microsoft Edge.
- No se necesitan paquetes externos para la aplicación ni para las 33 pruebas de lógica y API.
- Las 9 pruebas de interfaz requieren Microsoft Edge instalado y `requirements-dev.txt`.

## Ejecutar la aplicación

Abre una terminal en esta carpeta y ejecuta:

```powershell
python app.py
```

En Windows puedes utilizar `py -3 app.py` si el lanzador de Python está instalado. También puedes abrir `iniciar.cmd`, que busca Python y el runtime local de Codex.

Abre <http://127.0.0.1:8000> en el navegador. Detén el servidor con Ctrl+C en la terminal. El archivo `data/estudio.db` se crea automáticamente. La instalación empieza vacía; las capturas de la entrega utilizan datos de ejemplo en una base temporal.

Si el puerto está ocupado:

```powershell
python app.py --port 8001
```

Se puede elegir otra base mediante `python app.py --db otra_carpeta/tareas.db`. Para conservar las tareas, guarda una copia del archivo SQLite con el servidor detenido.

## Uso

1. Pulsa **Nueva tarea**, introduce el título y guarda. Los demás campos son opcionales.
2. Usa **Editar** para modificar todos los campos, incluido el estado **en curso**.
3. El círculo de cada tarea permite completarla y reabrirla.
4. **Eliminar** pide confirmación. **Conservar** cancela el borrado.
5. La búsqueda y todos los filtros se combinan. Una tarea está fuera de plazo si tiene fecha anterior al día local del navegador y no está completada. Las tareas de hoy y sin fecha quedan excluidas.

## Pruebas de lógica y API

```powershell
python run_tests.py
```

Ejecuta 33 métodos de prueba (8 de validación, 12 de almacenamiento y 13 de API). Guarda `evidencias/pruebas.log` y `evidencias/resultado.json`. Cada prueba de almacenamiento usa una base temporal; las pruebas HTTP usan otro archivo temporal y un puerto libre.

## Pruebas reales de interfaz

Instala las dependencias en un entorno virtual:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe tests/browser_checks.py
```

En macOS o Linux, sustituye `.venv\Scripts\python.exe` por `.venv/bin/python`. Es necesario Microsoft Edge instalado: el script utiliza el canal `msedge`, sin descargar otro navegador. No se ha verificado este proyecto en otros sistemas operativos.

Ejecuta 9 métodos de interfaz. Guarda `evidencias/interfaz.log`, `resultado_interfaz.json` y capturas PNG. El retorno es 0 si las pruebas pasan y 1 si fallan. Cierra los servidores y el navegador que crea. Los logs se sobrescriben al repetir una ejecución; las evidencias del fallo inicial se conservan con otros nombres.

## Estructura

```text
app.py                     Servidor HTTP, validación y repositorio SQLite
static/                    Interfaz HTML, CSS y JavaScript
tests/test_app.py          Pruebas de validación, repositorio y API
tests/browser_checks.py    Pruebas reales de interfaz y capturas
run_tests.py               Ejecutor con log y resumen JSON
requirements.txt           Dependencias de ejecución, sin paquetes externos
requirements-dev.txt       Playwright fijado a la versión utilizada
documentacion/             Requisitos, decisiones e interacciones reales
evidencias/                Resultados y capturas de las ejecuciones
```

## Alcance y límites

Aplicación para una persona en su propio equipo. Escucha exclusivamente en `127.0.0.1`. No incluye autenticación, sincronización, notificaciones ni despliegue público. El servidor de la biblioteca estándar es adecuado para este ejercicio local. No se han realizado pruebas de carga, auditoría completa de seguridad ni evaluación con lectores de pantalla. La búsqueda distingue letras acentuadas y no acentuadas. Los datos no se cifran en disco. Los filtros y contadores se recalculan al cargar o modificar tareas y al interactuar con los filtros.

Todo el código de aplicación y de pruebas fue generado por el asistente. Las intervenciones reales del usuario y las iteraciones se registran en `documentacion/interacciones.md`; las propuestas del asistente no se presentan como prompts escritos por el alumno.

## Informes

Los PDF finales están en `output/pdf/` desde la raíz de la entrega. El generador opcional `tools/generar_informes.py` utiliza los logs y capturas existentes. Para regenerarlos, instala `tools/requirements-informes.txt` y ejecuta `python tools/generar_informes.py` desde esta carpeta. Las dependencias de generación de PDF no son necesarias para ejecutar la aplicación ni sus tests.
