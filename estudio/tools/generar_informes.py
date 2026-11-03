"""Genera los dos informes PDF a partir de evidencias reales guardadas."""
import html
import json
import platform
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, PageBreak,
                                Table, TableStyle, Image, Preformatted)
from PIL import Image as PILImage

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
EV = ROOT / 'evidencias'
OUT = REPO / 'output' / 'pdf'
OUT.mkdir(parents=True, exist_ok=True)
results = json.loads((EV / 'resultado.json').read_text(encoding='utf-8'))
ui = json.loads((EV / 'resultado_interfaz.json').read_text(encoding='utf-8'))
first = json.loads((EV / 'primer_resultado.json').read_text(encoding='utf-8'))
assert results['success'] and ui['success'], 'No generar informes de éxito con pruebas fallidas'

fonts = Path('C:/Windows/Fonts')
if (fonts / 'arial.ttf').exists():
    for name, file in [('Body','arial.ttf'),('BodyBold','arialbd.ttf'),('BodyItalic','ariali.ttf')]:
        pdfmetrics.registerFont(TTFont(name, str(fonts / file)))
    pdfmetrics.registerFontFamily('Body', normal='Body', bold='BodyBold', italic='BodyItalic', boldItalic='BodyBold')
else:
    # Alternativa para regenerar en otros equipos.
    pdfmetrics.registerFontFamily('Helvetica', normal='Helvetica', bold='Helvetica-Bold', italic='Helvetica-Oblique', boldItalic='Helvetica-BoldOblique')
BODY = 'Body' if 'Body' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'
BOLD = 'BodyBold' if BODY == 'Body' else 'Helvetica-Bold'
BLACK = colors.HexColor('#161c19')
GRAY = colors.HexColor('#626c65')
styles = getSampleStyleSheet()
styles.add(ParagraphStyle('BodyTextCustom', fontName=BODY, fontSize=10, leading=14.8, textColor=BLACK, spaceAfter=9))
styles.add(ParagraphStyle('TitleCustom', fontName=BOLD, fontSize=26, leading=31, textColor=colors.black, spaceAfter=14))
styles.add(ParagraphStyle('HeadingCustom', fontName=BOLD, fontSize=15, leading=19, textColor=colors.black, spaceBefore=12, spaceAfter=9, keepWithNext=True))
styles.add(ParagraphStyle('SubCustom', fontName=BOLD, fontSize=11, leading=15, textColor=colors.black, spaceBefore=8, spaceAfter=6, keepWithNext=True))
styles.add(ParagraphStyle('SmallCustom', fontName=BODY, fontSize=8.2, leading=11.5, textColor=GRAY, spaceAfter=8))
styles.add(ParagraphStyle('CellCustom', fontName=BODY, fontSize=8.4, leading=12, textColor=BLACK))
styles.add(ParagraphStyle('CodeCustom', fontName='Courier', fontSize=8, leading=11, spaceAfter=10))
WIDTH = A4[0] - 96


def p(text, style='BodyTextCustom'):
    return Paragraph(text, styles[style])


def h(text):
    return p(text, 'HeadingCustom')


def table(headers, rows, widths):
    data = [[p(html.escape(str(c)), 'CellCustom') for c in row] for row in [headers] + rows]
    t = Table(data, colWidths=widths, repeatRows=1, hAlign='LEFT')
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e6ece8')),
        ('GRID', (0,0), (-1,-1), .5, colors.HexColor('#D9D9D9')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 9), ('RIGHTPADDING', (0,0), (-1,-1), 9),
        ('TOPPADDING', (0,0), (-1,-1), 8), ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    return t


def picture(name, max_height=445, width=WIDTH):
    path = EV / name
    with PILImage.open(path) as im:
        w, height = im.size
    scale = min(width / w, max_height / height)
    return Image(str(path), width=w * scale, height=height * scale, hAlign='CENTER')


def code(text):
    return Preformatted(text, styles['CodeCustom'])


def page(title, text):
    return [PageBreak(), h(title), p(text)]


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont(BODY, 8)
    canvas.setFillColor(GRAY)
    canvas.drawString(48, 29, 'Estudio  |  Software con inteligencia artificial  |  3 de noviembre de 2026')
    canvas.drawRightString(A4[0] - 48, 29, str(doc.page))
    canvas.restoreState()


def build(name, title, story):
    doc = SimpleDocTemplate(str(OUT / name), pagesize=A4, rightMargin=48, leftMargin=48,
        topMargin=42, bottomMargin=48, title=title, author='Proyecto Estudio con asistencia de IA')
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


def activity_one():
    story = [p('ACTIVIDAD 1  /  INFORME TÉCNICO', 'SmallCustom'),
        p('Desarrollo de un gestor de tareas de estudio con IA', 'TitleCustom'),
        p('Estudio es una aplicación web local que reúne tareas de diferentes asignaturas, permite planificar entregas y conserva los datos en SQLite. El prototipo incorpora el filtro de tareas fuera de plazo solicitado tras revisar la primera versión y ha superado 42 métodos de prueba automatizados.'),
        h('Necesidad y alcance'),
        p('El usuario necesita consultar en un único lugar qué debe hacer, qué está realizando y qué ha terminado. La solución se dirige a una persona que trabaja en su propio equipo. No requiere registro, servicios externos ni conexión a internet para su uso habitual.'),
        h('Requisitos funcionales'),
        table(['ID','Función','Aceptación'], [
            ['RF01','Crear tareas','Título obligatorio y campos opcionales validados'],
            ['RF02','Consultar y persistir','Conservar tareas después de reiniciar'],
            ['RF03','Editar','Modificar los seis campos de una tarea'],
            ['RF04','Cambiar estado','Pendiente, en curso, completada y reapertura'],
            ['RF05','Eliminar','Confirmación y posibilidad de cancelar'],
            ['RF06','Buscar','Título, asignatura y notas sin distinguir mayúsculas'],
            ['RF07','Filtrar','Estado y prioridad combinados con búsqueda'],
            ['RF08','Resumen global','Contadores independientes de los filtros'],
            ['RF09','Fuera de plazo','Fecha anterior a hoy y tarea sin completar'],
        ], [43,118,WIDTH-161]), Spacer(1,8),
        p('RF01 a RF08 corresponden al alcance inicial. RF09 se añadió mediante una petición expresa del usuario después del prototipo. La especificación está conservada en documentacion/proyecto_inicial.md.', 'SmallCustom')]
    story += page('Diseño técnico y decisiones', 'La interfaz HTML, CSS y JavaScript se comunica mediante JSON con un servidor HTTP escrito en Python. El servidor valida los datos y utiliza un repositorio SQLite. Todo el código de aplicación y pruebas fue generado por el asistente de IA dentro de esta sesión.')
    story += [p('Flujo de datos', 'SubCustom'), code('Navegador -> API HTTP local -> validación -> SQLite\nNavegador <- respuesta JSON <- repositorio'),
        p('Separación de responsabilidades', 'SubCustom'),
        p('app.py contiene validate, TaskStore y Handler. La validación se puede comprobar sin abrir el navegador. TaskStore concentra las consultas parametrizadas. Handler expone rutas conocidas y sirve únicamente los tres recursos estáticos de la interfaz.'),
        table(['Operación','Ruta','Resultado normal'], [
            ['GET','/api/tasks','200 con listado y filtros de consulta'],
            ['POST','/api/tasks','201 con la tarea creada'],
            ['GET','/api/tasks/{id}','200 con la tarea o 404 si no existe'],
            ['PUT','/api/tasks/{id}','200 con sustitución validada de campos'],
            ['DELETE','/api/tasks/{id}','204 tras el borrado o 404'],
        ], [65,150,WIDTH-215]), Spacer(1,10),
        p('Modelo de datos', 'SubCustom'),
        p('La tabla tasks almacena id, title, subject, notes, due_date, priority, status y created_at. La fecha límite se guarda como AAAA-MM-DD o texto vacío; created_at se registra en UTC. El identificador y la fecha de creación se conservan al editar.'),
        p('Criterios técnicos', 'SubCustom'),
        p('Se eligió SQLite para conservar datos sin instalar un servidor de base de datos. La biblioteca estándar reduce dependencias y facilita ejecutar el ejercicio. El cierre explícito de conexiones evita bloqueos de archivos en Windows. La interfaz inserta datos con textContent y el servidor limita tamaños, valida fechas y restringe orígenes de escritura.'),
        p('El título admite 120 caracteres, la asignatura 80 y las notas 2000. La interfaz usa etiquetas, foco visible y diálogos nativos; el diseño móvil se comprobó a 390 píxeles de ancho.')]
    story += page('Aplicación funcionando', 'El tablero permite revisar las tareas y acceder a las acciones principales. La captura se obtuvo de una ejecución real con Microsoft Edge y una base temporal de cuatro tareas de ejemplo.')
    story += [picture('01_tablero.png', 445), Spacer(1,8),
        p('Figura 1. Vista completa de escritorio. Archivo original: evidencias/01_tablero.png. Los datos de ejemplo se usan solo para las evidencias.', 'SmallCustom'),
        p('Los contadores distinguen tareas pendientes, en curso, completadas y fuera de plazo. La búsqueda y los filtros reducen la lista visible, mientras los contadores siguen mostrando el total. La tarea completada permanece identificable y puede reabrirse.'),
        p('La base de uso habitual se crea vacía en data/estudio.db. No contiene las tareas de las capturas.')]
    story += page('Edición y mejora solicitada', 'El mismo formulario permite crear y editar tareas. El estado en curso se establece desde el selector; el botón circular del tablero completa o reabre la tarea.')
    story += [picture('02_edicion.png', 375), Spacer(1,7),
        p('Figura 2. Formulario de edición con sus valores cargados. Archivo: evidencias/02_edicion.png.', 'SmallCustom'),
        p('Revisión del usuario', 'SubCustom'),
        p('Petición literal: <b>«Añadir un filtro de tareas fuera de plazo»</b>. Se incorporó una casilla que combina este criterio con el resto de filtros. Una fecha anterior al día local del navegador identifica una tarea vencida solo cuando no está completada. Las tareas de hoy y las que no tienen fecha quedan excluidas.'),
        p('La petición se convirtió en RF09 y en una prueba de interfaz con seis tareas que cubre ayer, hoy, mañana, ausencia de fecha, tareas completadas y combinación de filtros.')]
    story += page('Interacción con la IA e iteraciones', 'Se conservan extractos reales de esta sesión y se distingue la participación del usuario de las decisiones del asistente. El historial resumido se incluye en documentacion/interacciones.md.')
    story += [p('Concreción del proyecto', 'SubCustom'),
        p('<b>Usuario:</b> «ayudame a realizar las actividades». Después de que el asistente leyera los enunciados y preguntara por el proyecto, el usuario eligió «Gestor de tareas de estudio con base de datos local (recomendado)».'),
        p('<b>Asistente:</b> «Prepararé un gestor de tareas de estudio con asignaturas, fechas límite, prioridades, búsqueda y estados de progreso. Usará SQLite y se ejecutará en local».'),
        p('Resultado: se fijaron necesidad, campos y ejecución local. La formulación técnica detallada y la elección de las herramientas de prueba fueron propuestas por el asistente.'),
        p('Corrección guiada por resultados', 'SubCustom'),
        p('La primera ejecución de 33 pruebas produjo 12 errores asociados a la limpieza de archivos SQLite en Windows. El contexto de transacción no cerraba las conexiones. El asistente incorporó un gestor de contexto con cierre en finally y la siguiente ejecución terminó sin errores. El log inicial se conserva para verificar el cambio.'),
        p('<b>Asistente:</b> «La primera ejecución ha detectado un fallo real: las conexiones de SQLite quedaban abiertas y Windows impedía borrar las bases de datos temporales».'),
        p('Nueva instrucción y verificación', 'SubCustom'),
        p('<b>Usuario:</b> «Añadir un filtro de tareas fuera de plazo». <b>Asistente:</b> «Mostrará las tareas sin completar cuya fecha límite sea anterior a hoy y podrá combinarse con la búsqueda, el estado y la prioridad».'),
        p('La ampliación se implementó en la interfaz y se comprobó con un nuevo caso de navegador. La batería de interfaz pasó de 8 a 9 métodos.'),
        p('Análisis de la comunicación', 'SubCustom'),
        p('La petición inicial necesitó concreción. La instrucción de mejora fue más eficaz porque identificó una función observable. La dirección técnica recayó ampliamente en el asistente; una mejora del proceso sería indicar desde el inicio criterios de aceptación y pedir explícitamente las pruebas de cada regla. No se atribuyen al usuario prompts técnicos que no escribió.')]
    story += page('Resultados y entrega reproducible', 'El producto final permite completar el ciclo de gestión de una tarea y conservar los datos entre ejecuciones. Las pruebas comprobaron funciones de dominio, persistencia, API y flujos reales del navegador.')
    story += [table(['Nivel','Métodos','Resultado'], [
        ['Validación',8,'Correctos'],['Repositorio SQLite',12,'Correctos'],
        ['API HTTP',13,'Correctos'],['Interfaz Edge',ui['tests'],'Correctos'],
        ['Total',results['tests']+ui['tests'],'Sin fallos ni errores'],
    ], [230,70,WIDTH-300]), Spacer(1,10),
        p('Ejecución local', 'SubCustom'),
        code('cd estudio\npython app.py\n# Abrir http://127.0.0.1:8000'),
        p('Se requiere Python 3.11 o posterior. requirements.txt indica que no hay paquetes externos de ejecución. En Windows también se incluye iniciar.cmd. El README explica puertos alternativos, copias de la base y ejecución de pruebas.'),
        p('Limitaciones y valoración crítica', 'SubCustom'),
        p('La ejecución correcta de 42 métodos no demuestra ausencia de defectos ni cobertura total del código. No hay autenticación, sincronización, avisos ni cifrado de la base. No se evaluaron carga, múltiples navegadores, lectores de pantalla ni despliegue público. El servidor escucha solo en 127.0.0.1 y el alcance es personal y local.'),
        p('La IA permitió producir aplicación, pruebas y documentación, pero también generó inicialmente un defecto de gestión de recursos. Ejecutar las pruebas y conservar el error hizo posible corregirlo con evidencia. La revisión humana aportó una mejora funcional concreta; la siguiente iteración debería reforzar la especificación inicial y evaluar la usabilidad con tareas reales.'),
        p('Material entregado', 'SubCustom'),
        p('Código fuente, instrucciones, dependencias, requisitos, extractos de interacción, pruebas y evidencias se incluyen en el ZIP de entrega. La actividad 2 desarrolla el plan de pruebas y sus resultados. Fuentes de trabajo: enunciados psuiadesoft02_act1.docx y psuiadesoft02_act2.docx; código y logs del proyecto Estudio; extractos reales del chat del 3 de noviembre de 2026.', 'SmallCustom')]
    build('actividad_1_desarrollo.pdf', 'Actividad 1 Desarrollo de un gestor de tareas con IA', story)


def activity_two():
    story = [p('ACTIVIDAD 2  /  INFORME DE PRUEBAS', 'SmallCustom'),
        p('Pruebas automatizadas del gestor de tareas Estudio', 'TitleCustom'),
        p('Se ha generado y ejecutado un entorno de pruebas sobre la aplicación de la actividad 1. El resultado final es de 42 métodos correctos: 33 de validación, almacenamiento y API y 9 de interfaz. El proceso detectó y corrigió un defecto de cierre de conexiones SQLite.'),
        h('Objetivo y alcance'),
        p('El objetivo es comprobar los flujos esenciales y las entradas que podrían comprometer los datos. Se usan SQLite y HTTP reales para integración, y Microsoft Edge para ejecutar la interfaz. Todo el código de pruebas y la configuración del entorno fueron generados por el asistente.'),
        table(['Prioridad','Riesgo','Validación prevista'], [
            ['Alta','Pérdida o corrupción de tareas','CRUD, persistencia y edición inválida'],
            ['Alta','Transiciones incorrectas','Completar, reabrir y cancelar borrado'],
            ['Alta','Entradas inválidas o código','Tipos, límites, fechas, SQL y HTML'],
            ['Alta','Cálculo de tareas vencidas','Ayer, hoy, mañana, sin fecha y completada'],
            ['Media','Búsqueda y filtros incorrectos','Combinación y resumen global'],
            ['Media','Problemas de interfaz','Móvil, teclado y error de conexión'],
        ], [62,175,WIDTH-237]), Spacer(1,10),
        h('Criterio de finalización'),
        p('Ambas suites deben terminar sin fallos, errores ni omisiones, y deben conservarse logs y capturas. La cobertura se expresa por funcionalidades y casos; no se ha medido un porcentaje de cobertura de líneas.')]
    story += page('Entorno reproducible y aislamiento', 'Las pruebas unitarias y de integración utilizan unittest, sqlite3 y urllib de la biblioteca estándar. Las pruebas de interfaz utilizan Playwright 1.64.1 con el canal msedge.')
    story += [table(['Elemento','Entorno utilizado'], [
        ['Sistema','Windows y ejecución local'],
        ['Python',platform.python_version()],
        ['Framework base','unittest incluido en Python'],
        ['Interfaz','Playwright 1.64.1'],
        ['Edge',ui.get('browser_version','no registrado')],
        ['Reloj del navegador','Europe/Madrid; idioma es-ES'],
    ], [140,WIDTH-140]), Spacer(1,10),
        p('Ejecución de validación e integración', 'SubCustom'),
        code('cd estudio\npython run_tests.py'),
        p('Ejecución de interfaz en Windows', 'SubCustom'),
        code('python -m venv .venv\n.venv\\Scripts\\python.exe -m pip install -r requirements-dev.txt\n.venv\\Scripts\\python.exe tests/browser_checks.py'),
        p('Se requiere Microsoft Edge instalado. Los ejecutores devuelven código 0 al pasar y 1 al fallar. run_tests.py escribe pruebas.log y resultado.json; browser_checks.py escribe interfaz.log, resultado_interfaz.json y las capturas.'),
        p('Aislamiento de datos y procesos', 'SubCustom'),
        p('Cada prueba de repositorio crea un directorio temporal. La suite de API utiliza otro archivo SQLite y un puerto asignado por el sistema. Cada método de interfaz dispone de una base temporal, un servidor y un contexto de navegador propios. El cierre de conexiones, páginas y servidores permite limpiar los archivos sin afectar la base del usuario.')]
    story += page('Casos y trazabilidad', 'Los identificadores RF01 a RF09 proceden de la definición del proyecto. Los nombres completos de los métodos se encuentran en los logs y en los dos archivos de pruebas.')
    story += [table(['Requisito','Casos implementados','Evidencia'], [
        ['RF01 y RF03','Título vacío o espacios; tipos; límites; fechas; edición inválida sin cambios','ValidationTests y StoreTests'],
        ['RF02','Nueva instancia de repositorio y reinicio real del servidor','test_persists_in_new_store y UI 05'],
        ['RF03 a RF05','CRUD HTTP; estados; completar y reabrir; cancelar y confirmar borrado','test_crud_lifecycle y UI 01'],
        ['RF06 y RF07','Búsqueda en tres campos; mayúsculas; filtros combinados','StoreTests, API y UI 02'],
        ['RF08','Resumen global independiente de la lista filtrada','UI 02 y UI 09'],
        ['RF09','Fechas ayer, hoy y mañana; sin fecha; completada; combinación','UI 09'],
        ['RNF','Entrada SQL literal; HTML como texto; origen ajeno; móvil; Escape; red','StoreTests, API y UI 04, 06, 07, 08'],
    ], [68,252,WIDTH-320]), Spacer(1,12),
        p('Resultados esperados relevantes', 'SubCustom'),
        p('Una edición inválida debe rechazar la petición y conservar el registro original. Un identificador inexistente debe producir 404. El borrado confirmado debe devolver 204. Una petición con JSON no válido debe producir 400; un origen ajeno, 403; y un tipo de contenido incorrecto, 415.'),
        p('La prueba del filtro vencido crea seis tareas: solo las dos pendientes con fecha de ayer se muestran inicialmente. Al combinar búsqueda, prioridad y estado queda una. Las tareas completadas, de hoy, de mañana y sin fecha quedan fuera de esa selección.'),
        p('El total cuenta métodos de prueba; los bucles de subcasos y las múltiples aserciones no se contabilizan como pruebas adicionales.', 'SmallCustom')]
    story += page('Fallo encontrado y corrección', 'La primera ejecución reveló un defecto de gestión de recursos. Los métodos de almacenamiento alcanzaban sus comprobaciones, pero Windows impedía borrar las bases temporales durante tearDown porque permanecían conexiones abiertas.')
    story += [table(['Ejecución','Métodos','Fallos','Errores','Resultado'], [
        ['Inicial de lógica y API',first['tests'],first['failures'],first['errors'],'No correcta'],
        ['Tras cerrar conexiones',results['tests'],results['failures'],results['errors'],'Correcta'],
        ['Interfaz final',ui['tests'],ui['failures'],ui['errors'],'Correcta'],
    ], [175,59,53,53,WIDTH-340]), Spacer(1,12),
        p('Extracto del error real', 'SubCustom'),
        code('PermissionError: [WinError 32]\n... el archivo está siendo utilizado por otro proceso\n... tasks.db\nRan 33 tests ...\nFAILED (errors=12)'),
        p('Los 12 errores comparten causa: with sqlite3.connect gestiona la transacción, pero el diseño inicial no cerraba explícitamente la conexión. La corrección añadió un gestor de contexto que asegura close en finally después de la transacción.'),
        code('@contextmanager\ndef connect(self):\n    db = sqlite3.connect(self.path)\n    db.row_factory = sqlite3.Row\n    try:\n        with db:\n            yield db\n    finally:\n        db.close()'),
        p('La siguiente ejecución de las 33 pruebas pasó. Se conservan primera_ejecucion.log y primer_resultado.json, además de los resultados correctos posteriores. No se ocultó el fallo ni se retiraron las pruebas que lo detectaron.'),
        p('Comprobación de regresión', 'SubCustom'),
        p('Tras la solicitud del filtro fuera de plazo se añadió UI 09 y se repitió completa la suite de navegador. Los nueve métodos pasaron. La mejora afectó a la selección de tareas en la interfaz y no modificó la API ni el esquema de base de datos.')]
    story += page('Evidencias de ejecución', 'Las capturas se obtuvieron de la aplicación ejecutándose. El filtro fuera de plazo deja una tarea visible en la base de ejemplo, mientras el resumen mantiene los totales generales.')
    story += [picture('05_fuera_de_plazo.png', 355), Spacer(1,8),
        p('Figura 1. Filtro solicitado por el usuario en funcionamiento. Archivo: evidencias/05_fuera_de_plazo.png.', 'SmallCustom'),
        p('Extractos de los logs finales', 'SubCustom'),
        code('\n'.join((EV/'pruebas.log').read_text(encoding='utf-8').strip().splitlines()[-4:]) + '\n\n' + '\n'.join((EV/'interfaz.log').read_text(encoding='utf-8').strip().splitlines()[-4:])),
        p(f"Ejecución de lógica y API: {results['timestamp_utc']} UTC. Ejecución de interfaz: {ui['timestamp_utc']} UTC. Los archivos JSON conservan las marcas temporales completas.", 'SmallCustom'),
        p('Se adjuntan los logs completos y una captura de su visualización en evidencias/04_resultados.png. Las capturas adicionales muestran escritorio, formulario de edición y móvil.')]
    story += page('Interacción y análisis crítico', 'La interacción partió de la aplicación desarrollada en la actividad 1. El usuario eligió el proyecto y solicitó una mejora tras ver el prototipo; el asistente generó el entorno, las pruebas y la corrección del defecto detectado.')
    story += [p('Extractos reales de la conversación', 'SubCustom'),
        p('<b>Usuario:</b> «Gestor de tareas de estudio con base de datos local (recomendado)».'),
        p('<b>Asistente:</b> «Después añadiré pruebas unitarias y de integración, comprobaré la interfaz y prepararé los dos informes en PDF».'),
        p('<b>Asistente, tras la primera ejecución:</b> «Las conexiones de SQLite quedaban abiertas y Windows impedía borrar las bases de datos temporales. Ya he corregido el cierre de las conexiones».'),
        p('<b>Usuario, tras ver el tablero:</b> «Añadir un filtro de tareas fuera de plazo».'),
        p('<b>Asistente:</b> «Añadiré una prueba para comprobar que excluye las tareas completadas, las que vencen hoy y las que no tienen fecha».'),
        p('Estas intervenciones se conservan en documentacion/interacciones.md. No hubo un prompt técnico de pruebas redactado por el usuario: la propuesta del entorno fue del asistente. La petición de mejora sí produjo un criterio concreto y una prueba nueva.'),
        p('Interpretación de los resultados', 'SubCustom'),
        p('Las pruebas validan los flujos críticos y muestran que la automatización permitió detectar un defecto que no era visible al usar el tablero. La limpieza de temporales comprobó indirectamente la liberación de recursos. El caso RF09 introdujo límites de fecha y evitó equiparar cualquier tarea antigua con una tarea pendiente vencida.'),
        p('Límites y mejoras', 'SubCustom'),
        p('No se midió cobertura de líneas ni se aplicaron pruebas de mutación. No se probaron carga, concurrencia sostenida, varias versiones de navegador, accesibilidad completa ni recuperación de una base corrupta. El caso de fallo de red verifica que aparece un mensaje, pero no compara su traducción. El entorno ejecutado fue Windows con Edge; otros sistemas no están verificados.'),
        p('Como siguiente mejora conviene ampliar la revisión humana de los casos y evaluar accesibilidad y recuperación de datos. La calidad no debe deducirse solo de un resultado verde: también depende de que las reglas y los resultados esperados expresen lo que necesita el usuario.'),
        p('Fuentes de trabajo: enunciado psuiadesoft02_act2.docx; tests/test_app.py; tests/browser_checks.py; evidencias de ejecución y extractos reales del chat del 3 de noviembre de 2026.', 'SmallCustom')]
    build('actividad_2_pruebas.pdf', 'Actividad 2 Pruebas automatizadas del gestor Estudio', story)


if __name__ == '__main__':
    activity_one()
    activity_two()
    print('Informes generados en', OUT)
