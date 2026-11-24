# Wilber — barberos, agenda y dashboard

## Tu responsabilidad

barbers/ y dashboard/: presentación y gestión de perfiles, agenda personal por fecha, botones de cancelación/finalización y resumen administrativo. Consumes las operaciones de citas de Samuel; no las vuelves a implementar.

## Leer primero

1. docs/INSTALACION_WINDOWS.md para ejecutar el sistema.
2. AGENTS.md y docs/DECISIONES.md.
3. docs/MODELOS.md y docs/CONTRATOS.md.
4. docs/TRABAJO_EN_EQUIPO.md y este archivo.

## Modelos disponibles

- `barbers.models.Barbero`: usuario, descripcion, foto y campos de ModeloBase.
- `appointments.models.Cita`: cliente, barbero, servicio, fechas, snapshots, estado y auditoría.
- `appointments.models.EstadoCita`: opciones compartidas.

barbero.pk y barbero.usuario_id son identificadores distintos. Las citas apuntan a Barbero, no directamente al usuario del barbero. Los clientes se leen de seguridad.Usuario; no crees una tabla paralela.

## Orden sugerido

### 1. Perfiles

Construir consultas y formularios de descripcion/foto sobre el modelo existente. Las asignaciones de rol/perfil las coordina el usuario; no permitir a un visitante o cliente convertirse en barbero mediante un formulario. El modelo admin de Barbero empieza en modo consulta para no crear asignaciones incompletas.

La configuración del horario es común. No crear tablas de turnos individuales, descansos, vacaciones o feriados. Si surge una necesidad nueva, consultar al equipo.

### 2. Agenda propia

- Vista privada en barbers/ con selector de fecha; usar hoy si falta fecha.
- Validar el formato recibido y mostrar un error comprensible cuando sea inválido.
- Consultar únicamente las citas del perfil del barbero autenticado. No aceptar barbero_id de la URL como prueba de propiedad.
- Navegar a fechas anteriores y posteriores.
- Ordenar por fecha_inicio y pk.
- Mostrar hora, cliente, nombre_servicio_reservado, duración y estado; los históricos usan snapshots, no precio/duración actuales del catálogo.
- Empezar con tabla sencilla; no instalar una librería de calendario.

Samuel entrega obtener_agenda_barbero según CONTRATOS.md. Antes de que exista puedes construir la plantilla y probar consultas locales controladas, pero no presentar una pantalla con datos simulados como función terminada.

### 3. Cancelación y finalización

Usar cancelar_cita y completar_cita de appointments/services.py. Tu vista valida sesión, recibe POST+CSRF y delega la operación con actor=request.user. Mostrar ValidationError o PermissionDenied de manera adecuada y refrescar la agenda.

No modificar estado con save/update desde tus vistas. No duplicar permisos o reglas temporales de Samuel. Respetar D-03, ya confirmada. Que un botón esté oculto no sustituye el rechazo del backend ante una petición manipulada.

### 4. Dashboard administrativo

Solo para administrador usando los helpers compartidos. Consultar modelos existentes; dashboard no necesita nuevas tablas. Mostrar cuentas de clientes/barberos según la clasificación aprobada, citas de la fecha elegida, distribución por estado y listado general con filtro por fecha. No inventar ingresos, pagos o ventas: no existen pagos en este MVP.

Definir con el equipo si los conteos son históricos o por fecha y registrar la decisión antes de etiquetar estadísticas. Para contar citas por día, usar la fecha local de fecha_inicio; no cortar días directamente en UTC.

## Archivos y dependencias

Tus URLs ya están incluidas bajo /barberos/ y /panel/. Agrega rutas propias en cada urls.py y usa namespaces. Templates en templates/barbers/ y templates/dashboard/; estilos propios bajo static/<app>/.

No cambiar core/base.html, sidebar, settings, modelos ni firmas ajenas sin coordinar. Reutilizar los helpers de rol/asignación documentados; pedir a Samuel los servicios/selectors de citas. Si faltan, documentar la dependencia y continuar lo independiente.

## Cómo comprobar tu entrega

- Barbero A no ve ni cambia citas del barbero B manipulando una URL o POST.
- Un cliente no entra al panel del barbero ni al dashboard.
- La agenda muestra ayer, hoy y mañana correctamente en hora local.
- Una cancelación conserva el registro y muestra el estado actualizado.
- Completar/cancelar respeta las reglas y los estados terminales.
- Imagen ausente no rompe el perfil.
- El dashboard muestra valores derivados de la base, sin datos simulados.
- Una fecha sin citas muestra un mensaje útil, sin producir un error.

## Prompt para tu IA

```text
Lee AGENTS.md y la documentación obligatoria. Soy Wilber, principiante en Django.
Mi alcance es barbers y dashboard. Sigue WILBER.md.
Mi entrega concreta es: [indicar entrega]. Explícame los pasos y comandos.
Reutiliza Barbero y Cita; no crees otros modelos ni otra lógica de citas.
Las cancelaciones y finalizaciones deben usar los servicios de Samuel.
Ante una duda, contrato faltante o cambio en trabajo ajeno, describe el
impacto y propón qué consultar con el equipo; espera antes de implementarlo.
Entrega cómo probarlo, resultados reales y dependencias pendientes.
```
