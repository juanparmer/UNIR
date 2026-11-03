import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import TaskStore, ValidationError, make_server, validate


class ValidationTests(unittest.TestCase):
    def test_minimal_task_defaults(self):
        result = validate({'title': '  Leer tema 1  '})
        self.assertEqual(result['title'], 'Leer tema 1')
        self.assertEqual(result['priority'], 'media')
        self.assertEqual(result['status'], 'pendiente')
        self.assertEqual(result['due_date'], '')

    def test_required_title(self):
        for data in ({}, {'title': ''}, {'title': '  '}):
            with self.subTest(data=data), self.assertRaises(ValidationError):
                validate(data)

    def test_text_limits(self):
        for field, limit in (('title', 120), ('subject', 80), ('notes', 2000)):
            with self.subTest(field=field):
                validate({'title': 'Tarea', field: 'a' * limit})
                with self.assertRaises(ValidationError):
                    validate({'title': 'Tarea', field: 'a' * (limit + 1)})

    def test_non_text_fields_rejected(self):
        for field in ('title', 'subject', 'notes', 'due_date'):
            for value in (None, 4, [], {}):
                with self.subTest(field=field, value=value), self.assertRaises(ValidationError):
                    validate({'title': 'Tarea', field: value})

    def test_invalid_date(self):
        for value in ('2026-02-30', '03/11/2026', '20261103', 'ayer'):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                validate({'title': 'Tarea', 'due_date': value})

    def test_leap_date(self):
        self.assertEqual(validate({'title': 'Tarea', 'due_date': '2028-02-29'})['due_date'], '2028-02-29')

    def test_invalid_enums(self):
        for field in ('priority', 'status'):
            for value in ('desconocido', None, [], {}):
                with self.subTest(field=field, value=value), self.assertRaises(ValidationError):
                    validate({'title': 'Tarea', field: value})

    def test_non_object(self):
        for data in (None, [], 'tarea', 42):
            with self.subTest(data=data), self.assertRaises(ValidationError):
                validate(data)


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'tasks.db'
        self.store = TaskStore(self.path)

    def tearDown(self):
        self.temp.cleanup()

    def task(self, **kwargs):
        return self.store.create({'title': 'Leer tema', **kwargs})

    def test_empty(self):
        self.assertEqual(self.store.list(), [])

    def test_create_and_read(self):
        task = self.task(subject='Software IA', notes='Repasar', priority='alta')
        self.assertEqual(self.store.get(task['id']), task)
        self.assertEqual(task['subject'], 'Software IA')

    def test_persists_in_new_store(self):
        task = self.task()
        self.assertEqual(TaskStore(self.path).get(task['id']), task)

    def test_update_all_fields_and_preserve_identity(self):
        task = self.task()
        result = self.store.update(task['id'], {'title': 'Entregar', 'subject': 'IA',
            'notes': 'Final', 'priority': 'baja', 'status': 'en curso', 'due_date': '2026-12-10'})
        self.assertEqual(result['id'], task['id'])
        self.assertEqual(result['created_at'], task['created_at'])
        self.assertEqual(result['status'], 'en curso')
        self.assertEqual(result['title'], 'Entregar')

    def test_invalid_update_keeps_original(self):
        task = self.task()
        with self.assertRaises(ValidationError):
            self.store.update(task['id'], {'title': ''})
        self.assertEqual(self.store.get(task['id']), task)

    def test_complete_and_reopen(self):
        task = self.task()
        for state in ('en curso', 'completada', 'pendiente'):
            task = self.store.update(task['id'], {**task, 'status': state})
            self.assertEqual(task['status'], state)

    def test_delete_and_missing_ids(self):
        task = self.task()
        self.assertTrue(self.store.delete(task['id']))
        self.assertIsNone(self.store.get(task['id']))
        self.assertFalse(self.store.delete(task['id']))
        self.assertIsNone(self.store.update(task['id'], {'title': 'Nada'}))

    def test_search_title_subject_notes_case_insensitive(self):
        task = self.task(title='Álgebra', subject='UNIR', notes='Matrices')
        for query in ('álgEBRA', 'unir', 'MATRICES'):
            with self.subTest(query=query):
                self.assertEqual(self.store.list(query=query), [task])
        self.assertEqual(self.store.list(query='ausente'), [])

    def test_combined_filters(self):
        target = self.task(title='IA', status='en curso', priority='alta')
        self.task(title='IA', status='pendiente', priority='alta')
        self.task(title='IA', status='en curso', priority='baja')
        self.assertEqual(self.store.list(query='IA', status='en curso', priority='alta'), [target])

    def test_invalid_filters(self):
        for filters in ({'status': 'extra'}, {'priority': 'extra'}):
            with self.subTest(filters=filters), self.assertRaises(ValidationError):
                self.store.list(**filters)

    def test_order_dates_and_undated_last(self):
        undated = self.task()
        late = self.task(due_date='2026-12-03')
        early = self.task(due_date='2026-11-03')
        self.assertEqual([r['id'] for r in self.store.list()], [early['id'], late['id'], undated['id']])

    def test_sql_like_text_is_literal(self):
        title = "'); DROP TABLE tasks; --"
        task = self.task(title=title)
        self.assertEqual(self.store.get(task['id'])['title'], title)
        self.assertEqual(len(self.store.list()), 1)


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.server = make_server(Path(cls.temp.name) / 'api.db', 0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.temp.cleanup()

    def request(self, path='/api/tasks', method='GET', data=None, raw=None, headers=None):
        body = raw if raw is not None else (json.dumps(data).encode() if data is not None else None)
        request = Request(self.base + path, data=body, method=method,
                          headers={'Content-Type': 'application/json', **(headers or {})})
        try:
            response = urlopen(request, timeout=3)
        except HTTPError as error:
            response = error
        with response:
            payload = response.read()
            return response.status, payload, response.headers

    def create(self, **fields):
        code, body, _ = self.request(method='POST', data={'title': 'API test', **fields})
        self.assertEqual(code, 201)
        return json.loads(body)

    def test_crud_lifecycle(self):
        task = self.create()
        path = f"/api/tasks/{task['id']}"
        self.assertEqual(self.request(path)[0], 200)
        code, body, _ = self.request(path, 'PUT', {'title': 'Modificada', 'status': 'completada'})
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(body)['status'], 'completada')
        self.assertEqual(self.request(path, 'DELETE')[0], 204)
        self.assertEqual(self.request(path)[0], 404)

    def test_invalid_title_is_400(self):
        self.assertEqual(self.request(method='POST', data={'title': ' '})[0], 400)

    def test_malformed_json_is_400(self):
        self.assertEqual(self.request(method='POST', raw=b'{broken')[0], 400)

    def test_non_object_is_400(self):
        self.assertEqual(self.request(method='POST', raw=b'[]')[0], 400)

    def test_invalid_utf8_is_400(self):
        self.assertEqual(self.request(method='POST', raw=b'\xff')[0], 400)

    def test_body_too_large_is_400(self):
        self.assertEqual(self.request(method='POST', raw=b'a' * 16385)[0], 400)

    def test_missing_task_is_404(self):
        for method in ('GET', 'PUT', 'DELETE'):
            with self.subTest(method=method):
                self.assertEqual(self.request('/api/tasks/999999', method,
                    {'title': 'Ausente'} if method == 'PUT' else None)[0], 404)

    def test_invalid_filter_is_400(self):
        self.assertEqual(self.request('/api/tasks?status=incorrecto')[0], 400)

    def test_filter_query(self):
        task = self.create(title='UniqueNeedle', priority='alta')
        code, body, _ = self.request('/api/tasks?q=uniqueneedle&priority=alta')
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(body), [task])

    def test_foreign_origin_is_403(self):
        self.assertEqual(self.request(method='POST', data={'title': 'CSRF'},
            headers={'Origin': 'https://example.invalid'})[0], 403)

    def test_wrong_content_type_is_415(self):
        self.assertEqual(self.request(method='POST', raw=b'{}',
            headers={'Content-Type': 'text/plain'})[0], 415)

    def test_static_assets_and_headers(self):
        for path, mime in (('/', 'text/html'), ('/app.js', 'text/javascript'), ('/styles.css', 'text/css')):
            with self.subTest(path=path):
                code, body, headers = self.request(path)
                self.assertEqual(code, 200)
                self.assertTrue(headers['Content-Type'].startswith(mime))
                self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')
                self.assertIn("default-src 'self'", headers['Content-Security-Policy'])
                self.assertGreater(len(body), 100)

    def test_unknown_and_traversal_paths_are_404(self):
        for path in ('/missing', '/app.py', '/../app.py', '/api/tasks/not-a-number'):
            with self.subTest(path=path):
                self.assertEqual(self.request(path)[0], 404)


if __name__ == '__main__':
    unittest.main(verbosity=2)
