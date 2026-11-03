# Extractos reales de la interacción

Sesión del 3 de noviembre de 2026. Se recogen intervenciones reales del chat; no es una transcripción íntegra. Las decisiones técnicas y las instrucciones internas de ejecución pertenecen al asistente y no se atribuyen al usuario.

## Petición inicial

Usuario: «ayudame a realizar las actividades».

El asistente leyó los dos documentos y explicó que la actividad 2 debía probar la misma aplicación de la actividad 1. Preguntó por el proyecto y ofreció alternativas.

Usuario: «Gestor de tareas de estudio con base de datos local (recomendado)».

Asistente: «Prepararé un gestor de tareas de estudio con asignaturas, fechas límite, prioridades, búsqueda y estados de progreso. Usará SQLite y se ejecutará en local».

Resultado: alcance concretado a un gestor local. La propuesta técnica y la generación de código fueron realizadas por el asistente.

## Depuración a partir de una ejecución real

Asistente: «La primera ejecución ha detectado un fallo real: las conexiones de SQLite quedaban abiertas y Windows impedía borrar las bases de datos temporales. Ya he corregido el cierre de las conexiones».

Evidencia: `evidencias/primera_ejecucion.log` contiene 33 pruebas con 12 errores de limpieza de archivos; `primer_resultado.json` registra ese resultado. No se trató de 12 errores distintos de negocio, sino del mismo defecto de gestión de conexiones manifestado en las 12 pruebas de almacenamiento.

Resultado: el asistente añadió un gestor de contexto con cierre explícito en `finally`; la siguiente ejecución terminó sin errores.

## Solicitud de mejora del usuario

El asistente mostró el tablero con datos de ejemplo y pidió un ajuste antes de cerrar la documentación.

Usuario: «Añadir un filtro de tareas fuera de plazo».

Asistente: «Añadiré el filtro “Fuera de plazo”. Mostrará las tareas sin completar cuya fecha límite sea anterior a hoy y podrá combinarse con la búsqueda, el estado y la prioridad».

Resultado: se añadió la casilla de filtrado y la prueba `test_09_overdue_filter_boundaries_and_combination`, que comprueba límites y combinación de filtros.

## Valoración de la comunicación

La petición inicial fue general y necesitó una pregunta de concreción. La mejora posterior fue específica y permitió definir una regla comprobable. El asistente asumió gran parte de la especificación y del diseño del entorno de pruebas. Para mejorar la dirección humana en futuras iteraciones conviene indicar desde el primer prompt los campos, las reglas de validación, la persistencia esperada y los criterios de aceptación. No se atribuyen al usuario prompts técnicos que no escribió.
