"""Pruebas reales de interfaz y capturas. Requiere Playwright y Microsoft Edge."""
import html
import io
import json
import sys
import tempfile
import threading
import unittest
from datetime import date, timedelta, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import TaskStore, make_server
from run_tests import Tee
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'evidencias'


class BrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch(channel='msedge', headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / 'browser.db'
        self.server = make_server(self.db, 0)
        self.store = TaskStore(self.db)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f'http://127.0.0.1:{self.server.server_port}'
        self.context = self.browser.new_context(viewport={'width': 1440, 'height': 1050}, locale='es-ES', timezone_id='Europe/Madrid')
        self.page = self.context.new_page()
        self.errors = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))

    def tearDown(self):
        self.context.close()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()
        self.assertEqual(self.errors, [], 'Errores JavaScript inesperados')

    def open(self):
        self.page.goto(self.url)
        expect(self.page.locator('#result-count')).to_be_visible()

    def create_form(self, title):
        self.page.get_by_role('button', name='Nueva tarea').click()
        self.page.get_by_label('Título', exact=True).fill(title)

    def test_01_crud_complete_reopen_and_confirm_delete(self):
        self.open()
        self.create_form('Preparar actividad')
        self.page.get_by_label('Asignatura', exact=True).fill('Software IA')
        self.page.get_by_label('Notas', exact=True).fill('Revisar requisitos')
        self.page.get_by_role('button', name='Guardar tarea').click()
        expect(self.page.get_by_role('heading', name='Preparar actividad')).to_be_visible()
        self.page.get_by_role('button', name='Editar Preparar actividad', exact=True).click()
        self.page.get_by_label('Título', exact=True).fill('Entregar actividad')
        self.page.get_by_role('button', name='Guardar tarea').click()
        expect(self.page.get_by_role('heading', name='Entregar actividad')).to_be_visible()
        self.page.get_by_role('button', name='Completar Entregar actividad', exact=True).click()
        expect(self.page.locator('#done-count')).to_have_text('1')
        self.page.get_by_role('button', name='Reabrir Entregar actividad', exact=True).click()
        expect(self.page.locator('#pending-count')).to_have_text('1')
        self.page.get_by_role('button', name='Eliminar Entregar actividad', exact=True).click()
        self.page.get_by_role('button', name='Conservar', exact=True).click()
        expect(self.page.locator('.task')).to_have_count(1)
        self.page.get_by_role('button', name='Eliminar Entregar actividad', exact=True).click()
        self.page.get_by_role('button', name='Eliminar tarea', exact=True).click()
        expect(self.page.locator('.task')).to_have_count(0)

    def test_02_search_filters_and_global_summary(self):
        self.store.create({'title':'Lectura IA', 'priority':'alta', 'status':'en curso', 'due_date':(date.today()-timedelta(days=1)).isoformat()})
        self.store.create({'title':'Ejercicio SQL', 'priority':'baja', 'status':'completada'})
        self.open()
        expect(self.page.locator('.task')).to_have_count(2)
        expect(self.page.locator('#overdue-count')).to_have_text('1')
        self.page.get_by_label('Buscar tareas', exact=True).fill('ia')
        self.page.get_by_label('Filtrar por estado', exact=True).select_option('en curso')
        self.page.get_by_label('Filtrar por prioridad', exact=True).select_option('alta')
        expect(self.page.locator('.task')).to_have_count(1)
        expect(self.page.locator('#done-count')).to_have_text('1')
        self.page.get_by_label('Buscar tareas', exact=True).fill('inexistente')
        expect(self.page.locator('#empty')).to_be_visible()

    def test_03_whitespace_title_server_validation(self):
        self.open()
        self.create_form('   ')
        self.page.get_by_role('button', name='Guardar tarea').click()
        expect(self.page.locator('#form-error')).to_have_text('Escribe un título para la tarea.')
        expect(self.page.locator('#editor')).to_be_visible()
        self.assertEqual(self.store.list(), [])

    def test_04_html_is_text(self):
        payload = '<img src=x onerror="window.injected=true">'
        self.store.create({'title':payload, 'notes':'<script>alert(1)</script>'})
        self.open()
        expect(self.page.locator('.task h3')).to_have_text(payload)
        self.assertEqual(self.page.locator('.task img, .task script').count(), 0)
        self.assertIsNone(self.page.evaluate('window.injected'))

    def test_05_persistence_after_server_restart(self):
        self.open()
        self.create_form('Persistente')
        self.page.get_by_role('button', name='Guardar tarea').click()
        expect(self.page.locator('.task')).to_have_count(1)
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.server = make_server(self.db, 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.page.goto(f'http://127.0.0.1:{self.server.server_port}')
        expect(self.page.get_by_role('heading', name='Persistente')).to_be_visible()

    def test_06_mobile_has_no_horizontal_overflow(self):
        self.page.set_viewport_size({'width':390,'height':844})
        self.store.create({'title':'Planificar una entrega importante de la asignatura de software', 'subject':'Software IA', 'notes':'Repasar y entregar.'})
        self.open()
        expect(self.page.locator('.task')).to_have_count(1)
        self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'))
        self.create_form('Móvil')
        expect(self.page.get_by_role('button', name='Guardar tarea')).to_be_in_viewport()

    def test_07_connection_error_is_visible(self):
        self.page.route('**/api/tasks', lambda route: route.abort())
        self.open()
        expect(self.page.locator('#message')).not_to_be_empty()

    def test_08_keyboard_escape_and_focus(self):
        self.open()
        self.page.get_by_role('button', name='Nueva tarea').click()
        expect(self.page.get_by_label('Título', exact=True)).to_be_focused()
        self.page.keyboard.press('Escape')
        expect(self.page.locator('#editor')).not_to_be_visible()
        expect(self.page.get_by_role('button', name='Nueva tarea')).to_be_focused()

    def test_09_overdue_filter_boundaries_and_combination(self):
        today = date.today()
        yesterday = (today-timedelta(days=1)).isoformat()
        for fields in (
            {'title':'Vencida IA', 'due_date':yesterday, 'priority':'alta'},
            {'title':'Vencida SQL', 'due_date':yesterday, 'priority':'baja'},
            {'title':'Completada', 'due_date':yesterday, 'status':'completada'},
            {'title':'Hoy', 'due_date':today.isoformat()},
            {'title':'Sin fecha'},
            {'title':'Mañana', 'due_date':(today+timedelta(days=1)).isoformat()},
        ):
            self.store.create(fields)
        self.open()
        expect(self.page.locator('.task')).to_have_count(6)
        self.page.get_by_label('Fuera de plazo', exact=True).check()
        expect(self.page.locator('.task')).to_have_count(2)
        self.page.get_by_label('Filtrar por prioridad', exact=True).select_option('alta')
        self.page.get_by_label('Filtrar por estado', exact=True).select_option('pendiente')
        self.page.get_by_label('Buscar tareas', exact=True).fill('IA')
        expect(self.page.locator('.task h3')).to_have_text('Vencida IA')
        expect(self.page.locator('#overdue-count')).to_have_text('2')
        self.page.get_by_label('Fuera de plazo', exact=True).uncheck()
        self.page.get_by_label('Filtrar por prioridad', exact=True).select_option('')
        self.page.get_by_label('Filtrar por estado', exact=True).select_option('')
        self.page.get_by_label('Buscar tareas', exact=True).fill('')
        expect(self.page.locator('.task')).to_have_count(6)


def screenshots():
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / 'demo.db'
        store = TaskStore(db)
        today = date.today()
        samples = [
            {'title':'Definir los requisitos del gestor de estudio', 'subject':'Software IA', 'priority':'alta', 'status':'completada', 'due_date':today.isoformat()},
            {'title':'Preparar el informe de desarrollo con IA', 'subject':'Software IA', 'priority':'alta', 'status':'en curso', 'due_date':(today+timedelta(days=3)).isoformat(), 'notes':'Incluir capturas de la aplicación y decisiones del proyecto.'},
            {'title':'Repasar estrategias de pruebas automatizadas', 'subject':'Calidad del software', 'priority':'media', 'due_date':(today-timedelta(days=1)).isoformat()},
            {'title':'Diseñar casos de prueba de la API', 'subject':'Calidad del software', 'priority':'baja', 'due_date':(today+timedelta(days=6)).isoformat()},
        ]
        for sample in samples:
            store.create(sample)
        server = make_server(db, 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(channel='msedge', headless=True)
                page = browser.new_page(viewport={'width':1440,'height':1100}, locale='es-ES', timezone_id='Europe/Madrid')
                page.goto(f'http://127.0.0.1:{server.server_port}')
                expect(page.locator('.task')).to_have_count(4)
                page.screenshot(path=str(EVIDENCE / '01_tablero.png'), full_page=True)
                page.get_by_role('button', name='Editar Preparar el informe de desarrollo con IA', exact=True).click()
                page.screenshot(path=str(EVIDENCE / '02_edicion.png'), full_page=True)
                page.keyboard.press('Escape')
                page.set_viewport_size({'width':390,'height':844})
                page.screenshot(path=str(EVIDENCE / '03_movil.png'), full_page=True)
                page.set_viewport_size({'width':1440,'height':1100})
                page.get_by_label('Fuera de plazo', exact=True).check()
                expect(page.locator('.task')).to_have_count(1)
                page.screenshot(path=str(EVIDENCE / '05_fuera_de_plazo.png'), full_page=True)
                page.set_viewport_size({'width':1300,'height':950})
                log = (EVIDENCE / 'pruebas.log').read_text(encoding='utf-8')
                ui_log = (EVIDENCE / 'interfaz.log').read_text(encoding='utf-8')
                # Es una visualización del log real, no una terminal simulada.
                page.set_content('<html lang="es"><meta charset="utf-8"><body style="margin:40px;font:15px Consolas,monospace;color:#173729;background:#f7f8f4"><h1 style="font:30px Segoe UI">Resultados reales de las pruebas</h1><p>Logs generados por unittest y Playwright</p><pre style="white-space:pre-wrap;font-size:14px;line-height:1.5">' + html.escape(log + '\n' + ui_log) + '</pre></body></html>')
                page.screenshot(path=str(EVIDENCE / '04_resultados.png'), full_page=True)
                version = browser.version
                browser.close()
                return version
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


def main():
    EVIDENCE.mkdir(exist_ok=True)
    buffer = io.StringIO()
    output = Tee(sys.stdout, buffer)
    output.write(f'Ejecución de interfaz UTC: {datetime.now(timezone.utc).isoformat()}\n')
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(BrowserTests)
    result = unittest.TextTestRunner(stream=output, verbosity=2).run(suite)
    (EVIDENCE / 'interfaz.log').write_text(buffer.getvalue(), encoding='utf-8')
    summary = {'timestamp_utc':datetime.now(timezone.utc).isoformat(), 'tests':result.testsRun,
        'failures':len(result.failures), 'errors':len(result.errors), 'success':result.wasSuccessful()}
    if result.wasSuccessful():
        summary['browser_version'] = screenshots()
    (EVIDENCE / 'resultado_interfaz.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
