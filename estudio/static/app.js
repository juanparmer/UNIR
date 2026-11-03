'use strict';
const $ = (selector) => document.querySelector(selector);
let tasks = [], editing = null, deleting = null, loadVersion = 0;
const form = $('#task-form');
const overdueLabel = element('label', 'overdue-filter');
const overdueInput = element('input');
overdueInput.type = 'checkbox'; overdueInput.id = 'overdue-filter';
overdueLabel.append(overdueInput, document.createTextNode('Fuera de plazo'));
$('.filters').append(overdueLabel);
const editor = $('#editor');
const localDate = () => {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')}`;
};
$('#today').textContent = new Intl.DateTimeFormat('es-ES', {day:'numeric',month:'long',year:'numeric'}).format(new Date());
async function api(path, method = 'GET', data) {
  const response = await fetch(path, {method, headers: {'Content-Type':'application/json'}, ...(data ? {body:JSON.stringify(data)} : {})});
  const body = response.status === 204 ? null : await response.json();
  if (!response.ok) throw new Error(body.error || 'No se ha podido completar la operación.');
  return body;
}
function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
function render() {
  const query = $('#search').value.toLocaleLowerCase('es');
  const filtered = tasks.filter(t => (!query || `${t.title} ${t.subject} ${t.notes}`.toLocaleLowerCase('es').includes(query)) && (!$('#status-filter').value || t.status === $('#status-filter').value) && (!$('#priority-filter').value || t.priority === $('#priority-filter').value) && (!overdueInput.checked || (t.status !== 'completada' && t.due_date && t.due_date < localDate())));
  $('#pending-count').textContent = tasks.filter(t => t.status === 'pendiente').length;
  $('#progress-count').textContent = tasks.filter(t => t.status === 'en curso').length;
  $('#done-count').textContent = tasks.filter(t => t.status === 'completada').length;
  $('#overdue-count').textContent = tasks.filter(t => t.status !== 'completada' && t.due_date && t.due_date < localDate()).length;
  $('#result-count').textContent = `${filtered.length} ${filtered.length === 1 ? 'tarea' : 'tareas'}`;
  $('#empty').hidden = filtered.length > 0;
  $('#tasks').replaceChildren();
  for (const task of filtered) {
    const row = element('article', `task ${task.status === 'completada' ? 'completed' : ''}`);
    const toggle = element('button', `toggle ${task.status === 'completada' ? 'done' : ''}`, task.status === 'completada' ? '✓' : '');
    toggle.setAttribute('aria-label', `${task.status === 'completada' ? 'Reabrir' : 'Completar'} ${task.title}`);
    toggle.onclick = async () => { toggle.disabled = true; try { await api(`/api/tasks/${task.id}`, 'PUT', {...task,status:task.status === 'completada' ? 'pendiente' : 'completada'}); await load('Estado actualizado.'); } catch(e) { $('#message').textContent = e.message; toggle.disabled = false; } };
    const body = element('div', 'task-body');
    body.append(element('h3', '', task.title));
    const meta = element('div', 'meta');
    if (task.subject) meta.append(element('span', 'subject', task.subject));
    meta.append(element('span', `badge ${task.priority}`, `Prioridad ${task.priority}`));
    if (task.due_date) {
      const late = task.due_date < localDate() && task.status !== 'completada';
      const formatted = new Intl.DateTimeFormat('es-ES', {day:'numeric',month:'short',year:'numeric'}).format(new Date(`${task.due_date}T12:00:00`));
      meta.append(element('span', late ? 'overdue' : '', `${late ? 'Fuera de plazo · ' : 'Entrega · '}${formatted}`));
    }
    meta.append(element('span', 'status', task.status));
    body.append(meta);
    if (task.notes) body.append(element('p', 'notes', task.notes));
    const actions = element('div', 'actions');
    const edit = element('button', '', 'Editar');
    edit.setAttribute('aria-label', `Editar ${task.title}`); edit.onclick = () => openEditor(task);
    const remove = element('button', '', 'Eliminar');
    remove.setAttribute('aria-label', `Eliminar ${task.title}`); remove.onclick = () => { deleting = task.id; $('#delete-dialog').showModal(); };
    actions.append(edit, remove); row.append(toggle, body, actions); $('#tasks').append(row);
  }
}
async function load(message = '') {
  const version = ++loadVersion;
  try {
    const result = await api('/api/tasks');
    if (version !== loadVersion) return;
    tasks = result; render(); $('#message').textContent = message;
  } catch(e) { if (version === loadVersion) $('#message').textContent = e.message; }
}
function openEditor(task = null) {
  editing = task?.id ?? null; form.reset(); $('#form-error').textContent = '';
  $('#editor-title').textContent = task ? 'Editar tarea' : 'Nueva tarea';
  if (task) for (const name of ['title','subject','due_date','priority','status','notes']) form.elements.namedItem(name).value = task[name];
  editor.showModal(); form.elements.namedItem('title').focus();
}
$('#new-task').onclick = () => openEditor();
$('#close-editor').onclick = $('#cancel').onclick = () => editor.close();
$('#cancel-delete').onclick = () => $('#delete-dialog').close();
$('#confirm-delete').onclick = async () => {
  const button = $('#confirm-delete'); button.disabled = true;
  try { await api(`/api/tasks/${deleting}`, 'DELETE'); $('#delete-dialog').close(); await load('Tarea eliminada.'); }
  catch(e) { $('#delete-dialog').close(); $('#message').textContent = e.message; }
  finally { button.disabled = false; }
};
form.onsubmit = async event => {
  event.preventDefault(); const button = form.querySelector('[type=submit]'); button.disabled = true;
  try {
    await api(editing ? `/api/tasks/${editing}` : '/api/tasks', editing ? 'PUT' : 'POST', Object.fromEntries(new FormData(form)));
    editor.close(); await load(editing ? 'Cambios guardados.' : 'Tarea creada.');
  } catch(e) { $('#form-error').textContent = e.message; }
  finally { button.disabled = false; }
};
for (const selector of ['#search','#status-filter','#priority-filter','#overdue-filter']) $(selector).addEventListener('input', render);
load();
