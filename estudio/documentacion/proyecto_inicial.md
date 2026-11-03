# Definición funcional de Estudio

Fecha: 3 de noviembre de 2026. Necesidad: centralizar tareas de diferentes asignaturas y reconocer entregas pendientes sin depender de servicios externos. Usuario: estudiante que utiliza un único ordenador. Producto: aplicación web local con persistencia SQLite.

## Requisitos iniciales

| ID | Requisito | Criterio de aceptación |
| --- | --- | --- |
| RF01 | Crear tareas | Guardar título obligatorio y campos opcionales; rechazar título vacío o de espacios |
| RF02 | Consultar y persistir | Conservar tareas tras reiniciar servidor y navegador |
| RF03 | Editar | Modificar título, asignatura, notas, prioridad, estado y fecha |
| RF04 | Cambiar estado | Pasar entre pendiente, en curso y completada; reabrir |
| RF05 | Eliminar | Confirmar borrado y poder cancelarlo |
| RF06 | Buscar | Buscar sin distinguir mayúsculas en título, asignatura y notas |
| RF07 | Filtrar | Combinar búsqueda con estado y prioridad |
| RF08 | Resumen | Contar pendientes, en curso, completadas y vencidas sobre todas las tareas |

RNF01: ejecución local con Python 3.11 o posterior, sin paquetes externos de ejecución. RNF02: interfaz adaptable a escritorio y móvil, controles etiquetados y diálogos utilizables con teclado. RNF03: validar también en servidor, usar consultas parametrizadas y representar entradas del usuario como texto. RNF04: código y pruebas generados mediante el asistente de IA.

## Cambio solicitado tras el prototipo

RF09: filtro de tareas fuera de plazo. Petición literal del usuario: «Añadir un filtro de tareas fuera de plazo». Regla acordada en la respuesta del asistente: fecha anterior a hoy según el calendario local del navegador y estado distinto de completada. Sin fecha o con vencimiento hoy no se considera vencida. Debe combinarse con RF06 y RF07 y conservar el resumen global RF08.

## Fuera del alcance

Cuentas de usuario, sincronización, calendario externo, avisos y despliegue en internet. Se prioriza un flujo completo y comprobable antes que ampliar funciones.
