"""Estudio: gestor local de tareas. Solo utiliza la biblioteca estándar de Python."""
import argparse
import json
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timezone
from functools import partial
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parent
STATUSES = ('pendiente', 'en curso', 'completada')
PRIORITIES = ('baja', 'media', 'alta')


class ValidationError(ValueError):
    pass


def validate(data):
    """Valida el registro completo; no modifica la entrada."""
    if not isinstance(data, dict):
        raise ValidationError('Se esperaba un objeto JSON.')
    result = {}
    for field, maximum in (('title', 120), ('subject', 80), ('notes', 2000)):
        value = data.get(field, '')
        if not isinstance(value, str):
            raise ValidationError(f'{field} debe ser texto.')
        value = value.strip()
        if field == 'title' and not value:
            raise ValidationError('Escribe un título para la tarea.')
        if len(value) > maximum:
            raise ValidationError(f'{field} admite como máximo {maximum} caracteres.')
        result[field] = value
    for field, allowed, default in (('status', STATUSES, 'pendiente'),
                                     ('priority', PRIORITIES, 'media')):
        value = data.get(field, default)
        if value not in allowed:
            raise ValidationError(f'Valor de {field} no válido.')
        result[field] = value
    due = data.get('due_date', '')
    if not isinstance(due, str):
        raise ValidationError('La fecha debe ser texto AAAA-MM-DD.')
    if due:
        try:
            if date.fromisoformat(due).isoformat() != due:
                raise ValueError()
        except ValueError:
            raise ValidationError('La fecha debe ser válida y tener formato AAAA-MM-DD.')
    result['due_date'] = due
    return result


class TaskStore:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL, subject TEXT NOT NULL, notes TEXT NOT NULL,
                due_date TEXT NOT NULL, priority TEXT NOT NULL, status TEXT NOT NULL,
                created_at TEXT NOT NULL)''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def list(self, query='', status='', priority=''):
        if status and status not in STATUSES:
            raise ValidationError('Filtro de estado no válido.')
        if priority and priority not in PRIORITIES:
            raise ValidationError('Filtro de prioridad no válido.')
        with self.connect() as db:
            rows = [dict(r) for r in db.execute('''SELECT * FROM tasks
                ORDER BY CASE WHEN due_date = '' THEN 1 ELSE 0 END, due_date, id''')]
        return [r for r in rows if (not query or query.casefold() in
                (r['title'] + ' ' + r['subject'] + ' ' + r['notes']).casefold())
                and (not status or r['status'] == status)
                and (not priority or r['priority'] == priority)]

    def get(self, task_id):
        with self.connect() as db:
            row = db.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
        return dict(row) if row else None

    def create(self, data):
        task = validate(data)
        task['created_at'] = datetime.now(timezone.utc).isoformat(timespec='seconds')
        with self.connect() as db:
            cursor = db.execute('''INSERT INTO tasks
                (title,subject,notes,due_date,priority,status,created_at)
                VALUES (:title,:subject,:notes,:due_date,:priority,:status,:created_at)''', task)
            task_id = cursor.lastrowid
        return self.get(task_id)

    def update(self, task_id, data):
        if not self.get(task_id):
            return None
        task = validate(data)
        task['id'] = task_id
        with self.connect() as db:
            db.execute('''UPDATE tasks SET title=:title, subject=:subject, notes=:notes,
                due_date=:due_date, priority=:priority, status=:status WHERE id=:id''', task)
        return self.get(task_id)

    def delete(self, task_id):
        with self.connect() as db:
            return db.execute('DELETE FROM tasks WHERE id = ?', (task_id,)).rowcount > 0


class Handler(BaseHTTPRequestHandler):
    server_version = 'Estudio/1.0'

    def __init__(self, *args, store, **kwargs):
        self.store = store
        super().__init__(*args, **kwargs)

    def send(self, status, body, content_type='application/json; charset=utf-8'):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Security-Policy', "default-src 'self'; style-src 'self'; script-src 'self'; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers()
        self.wfile.write(body)

    def json_body(self):
        try:
            length = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            raise ValidationError('Longitud de petición no válida.')
        if not 0 < length <= 16384:
            raise ValidationError('El cuerpo debe contener entre 1 y 16384 bytes.')
        try:
            return json.loads(self.rfile.read(length).decode('utf-8'))
        except (ValueError, UnicodeError):
            raise ValidationError('El cuerpo no contiene JSON válido.')

    def route(self):
        # El navegador debe escribir desde el propio origen; no se habilita CORS.
        if self.command in ('POST', 'PUT', 'DELETE'):
            expected = 'http://' + self.headers.get('Host', '')
            origin = self.headers.get('Origin')
            if origin and origin != expected:
                return self.send(403, {'error': 'Origen no permitido.'})
            if self.command != 'DELETE' and self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                return self.send(415, {'error': 'Utiliza application/json.'})
        url = urlsplit(self.path)
        if url.path == '/api/tasks' and self.command == 'GET':
            q = parse_qs(url.query)
            return self.send(200, self.store.list(q.get('q', [''])[0],
                            q.get('status', [''])[0], q.get('priority', [''])[0]))
        if url.path == '/api/tasks' and self.command == 'POST':
            return self.send(201, self.store.create(self.json_body()))
        parts = url.path.strip('/').split('/')
        if len(parts) == 3 and parts[:2] == ['api', 'tasks'] and parts[2].isdigit():
            task_id = int(parts[2])
            if self.command == 'GET':
                task = self.store.get(task_id)
            elif self.command == 'PUT':
                task = self.store.update(task_id, self.json_body())
            elif self.command == 'DELETE':
                if self.store.delete(task_id):
                    return self.send(204, b'')
                task = None
            else:
                return self.send(405, {'error': 'Método no permitido.'})
            return self.send(200, task) if task else self.send(404, {'error': 'Tarea no encontrada.'})
        files = {'/': ('index.html', 'text/html'), '/app.js': ('app.js', 'text/javascript'),
                 '/styles.css': ('styles.css', 'text/css')}
        if self.command == 'GET' and url.path in files:
            name, mime = files[url.path]
            return self.send(200, (ROOT / 'static' / name).read_bytes(), mime + '; charset=utf-8')
        return self.send(404, {'error': 'Ruta no encontrada.'})

    def handle_request(self):
        try:
            self.route()
        except ValidationError as error:
            self.send(400, {'error': str(error)})
        except sqlite3.Error:
            self.send(500, {'error': 'No se ha podido acceder a la base de datos.'})

    do_GET = do_POST = do_PUT = do_DELETE = handle_request


def make_server(db_path, port=8000):
    return ThreadingHTTPServer(('127.0.0.1', port), partial(Handler, store=TaskStore(db_path)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--db', type=Path, default=ROOT / 'data' / 'estudio.db')
    args = parser.parse_args()
    server = make_server(args.db, args.port)
    print(f'Estudio disponible en http://127.0.0.1:{server.server_port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
