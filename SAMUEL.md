# Samuel — citas y disponibilidad

## Tu responsabilidad

appointments/: lógica de disponibilidad, creación de reservas, cancelación/finalización, próximas citas e historial del cliente. Tú defines una sola lógica de negocio; Wilber construye la agenda del barbero consumiendo tus funciones.

## Leer primero

AGENTS.md → docs/DECISIONES.md → docs/MODELOS.md → docs/CONTRATOS.md → docs/TRABAJO_EN_EQUIPO.md. D-01/D-02/D-03 ya están aprobadas. Reutilizar los helpers existentes de roles y horario.

## Qué recibes

Usuario existente, Servicio, Barbero y Cita; estados y auditoría; snapshots históricos; restricción PostgreSQL contra superposición del mismo barbero; pruebas de integridad y concurrencia. Apps, rutas globales y carpetas ya registradas. No repetir esos modelos ni crear una tabla de horarios.

## Primera entrega: funciones compartidas

Implementar las firmas de CONTRATOS.md en appointments/services.py y appointments/selectors.py antes de terminar todas tus pantallas. Avisar a Wilber cuando pueda consumirlas. No usar NotImplementedError o resultados simulados como si fueran funcionalidad terminada.

## Flujo de reserva

1. Exigir un cliente autenticado según los helpers compartidos del usuario.
2. Recibir únicamente servicio, barbero e inicio; tomar cliente de actor y precio/duración del servidor.
3. Revalidar que servicio, perfil y usuario del barbero están habilitados.
4. Validar futuro, día laboral, alineación e intervalo completo dentro del horario común aprobado.
5. Calcular fin, nombre_servicio_reservado, precio_reservado y duracion_reservada.
6. Consultar intersecciones con inicio_existente < fin_nuevo y fin_existente > inicio_nuevo. CONFIRMED y COMPLETED bloquean; CANCELLED no.
7. Dentro de una transacción, validar y guardar como CONFIRMED. Traducir un IntegrityError de superposición a un mensaje de disponibilidad, fuera del bloque atomic fallido.
8. Si el horario quedó ocupado desde que se mostró el formulario, refrescar las opciones y mostrar el error. No anunciar confirmación cuando la escritura falló.

El selector de disponibilidad es informativo; la reserva siempre vuelve a validar al guardar. La restricción de PostgreSQL no comprueba por ti permisos, actividad o horario. No quitarla aunque ya tengas un filtro en Python.

## Cancelación y finalización

Usar las reglas confirmadas en D-03. Bloquear la Cita con select_for_update, validar actor y estado y cambiar estado/fecha/actor juntos. Solo partir de CONFIRMED. CANCELLED y COMPLETED son terminales; no volver a confirmar ni borrar la cita. Actualizar fecha_modificacion si se usa update_fields.

## Pantallas del cliente

Formulario por etapas o una sola pantalla con servicio, barbero, fecha y hora; resumen previo de servicio, barbero, inicio, duración y precio; respuesta de confirmación; listado de próximas citas e historial; cancelación propia con POST y CSRF. La vista nunca acepta cliente_id ni snapshots del formulario como verdad.

Usar namespace appointments bajo /citas/ y plantilla core/base.html. Coordinar un enlace con Max después de crear la ruta real de reserva.

## Pruebas que debes añadir

- Rechazo de fechas pasadas, días cerrados, inicio desalineado y servicio que termina después del cierre.
- Rechazo de servicios/barberos/usuarios inactivos.
- Intersecciones parciales y completas; citas contiguas permitidas.
- Dos solicitudes simultáneas producen un éxito y un error comprensible.
- Precio/duración/cliente manipulados no se aceptan.
- Un cliente no ve ni cancela citas ajenas; un barbero solo gestiona las asignadas.
- Límites temporales de cancelar/completar y transición repetida.
- Los snapshots permanecen iguales si Max cambia el catálogo.

Conservar las pruebas de integridad existentes; no sustituirlas por mocks de SQLite. Usar PostgreSQL para concurrencia.

## No te corresponde

Cambiar User, perfiles, catálogo, roles, archivos de configuración o plantilla base sin coordinar. Construir el panel del barbero duplicaría el trabajo de Wilber. No implementar pagos, notificaciones ni calendarios complejos.

## Prompt para tu IA

```text
Lee AGENTS.md y los documentos obligatorios. Soy Samuel y trabajo en appointments.
Sigue SAMUEL.md. Mi entrega de hoy es: [indicar entrega].
No alteres modelos ni funciones acordadas para resolver una pantalla.
Comparte las funciones de reserva/cancelación/finalización con Wilber.
Si falta una decisión o se necesita un cambio ajeno, explica el impacto,
propón una alternativa y espera la respuesta del equipo antes de hacerla.
Entrega código verificable y reporta pruebas reales y pendientes.
```
