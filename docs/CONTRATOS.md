# Contratos entre módulos

Estado: las funciones de citas de Samuel ya están implementadas en appointments/services.py y appointments/selectors.py (rama feat/samuel-reservas). Ninguna pantalla debe anunciar éxito si el servicio correspondiente aún no existe. Las decisiones D-01/D-02/D-03 ya fueron confirmadas.

## Base técnica ya disponible

- Usuario único: seguridad.Usuario.
- Modelos: services.Servicio, barbers.Barbero y appointments.Cita.
- ModeloBase en core.models.
- Cada app tiene su urls.py, views.py, forms.py, templates/<app>/ y static/<app>/.
- Plantilla autenticada: core/base.html. Bloques reales: titulo, contenido, estilos_extra y scripts_extra.
- No utilizar nombres de bloques ingleses tomados de una propuesta anterior.
- Interfaz en español y código propio en español sin tildes. Las apps mantienen los nombres ingleses ya distribuidos en el chat para no cambiar las responsabilidades.

## Rutas reservadas

| Namespace | Prefijo ya incluido | Responsable |
|---|---|---|
| seguridad | /seguridad/ | Usuario |
| core | / | Usuario |
| services | /servicios/ | Max |
| website | /web/ | Max |
| appointments | /citas/ | Samuel |
| barbers | /barberos/ | Wilber |
| dashboard | /panel/ | Wilber |

Los cinco módulos nuevos empiezan con urlpatterns vacío. Un 404 en sus prefijos es esperado hasta implementar sus vistas; no hay enlaces de navegación a funciones inexistentes. Agregar rutas en la app propia sin cambiar las URLs globales.

La raíz / conserva el inicio privado heredado. Max construye la portada pública en /web/; el usuario coordinará si se desea convertirla después en la raíz. Para un layout público distinto, proponerlo al usuario antes de crear otra plantilla base.

## Samuel: única capa de escritura de citas

Implementado en appointments/services.py. Firmas:

```python
reservar_cita(*, actor, servicio_id, barbero_id, fecha_inicio) -> Cita
cancelar_cita(*, actor, cita_id, motivo='') -> Cita
completar_cita(*, actor, cita_id) -> Cita
```

actor es un Usuario autenticado, no un identificador enviado por el formulario. barbero_id es la clave de Barbero, no la de Usuario. El cliente de la reserva se toma de actor. La función construye fecha_fin y las tres copias históricas usando Servicio.

Cada operación válida devuelve la Cita guardada. Acceso prohibido: PermissionDenied. Datos o reglas inválidas: ValidationError con estos códigos estables (consultar error.code):

| Código | Cuándo |
|---|---|
| servicio_no_disponible | Servicio inexistente o inactivo |
| barbero_no_disponible | Perfil, cuenta o rol del barbero no habilitados |
| horario_ocupado | Se cruza con otra cita no cancelada del barbero (también por concurrencia) |
| transicion_invalida | La cita ya no está CONFIRMED |
| cancelacion_fuera_de_plazo | El cliente cancela a partir de fecha_inicio |
| finalizacion_anticipada | Se completa antes de fecha_fin |
| motivo_largo | Motivo de cancelación de más de 500 caracteres |
| inicio_pasado, dia_cerrado, fuera_horario, inicio_desalineado, zona_horaria_requerida, duracion_invalida | Propagados de core.horarios.calcular_fin_validado |

Solo un usuario con rol Cliente puede reservar; barbero y administrador reciben PermissionDenied (las reservas en nombre de otra persona siguen pendientes de acuerdo). cancelar_cita y completar_cita lanzan Cita.DoesNotExist para un ID inexistente. Un ID inexistente no debe convertirse en un éxito: la vista devuelve 404. Capturar IntegrityError por superposición fuera del bloque atomic fallido y traducirlo a ValidationError; no mostrar errores SQL al usuario.

Toda escritura se realiza en transaction.atomic. Las transiciones bloquean la fila con select_for_update y revalidan estado y actor. La exclusión PostgreSQL evita dos reservas simultáneas del barbero; no sustituye la validación de permisos ni la comprobación amable de disponibilidad.

Para serializar reservas con la desactivación/asignación de barbero, acordar este orden de bloqueo: Usuario del barbero, Barbero y Servicio; revalidar actividad/rol y obtener snapshots después de tomar los bloqueos. seguridad.asignar_rol ya bloquea Usuario y luego Barbero. No invertir ese orden desde otros módulos ni introducir otra estrategia sin coordinar. La cancelación/finalización bloquea Cita y no necesita adquirir esos recursos.

No crear reservas ni cambiar estado desde views de barbers/dashboard, signals, ModelAdmin genérico o update() que evite esta capa. No volver a CONFIRMED desde un estado terminal. No reprogramar editando fechas: el MVP propone cancelar y reservar de nuevo, sujeto a acuerdo del equipo si se necesita otra experiencia.

## Samuel: consultas reutilizables

Implementado en appointments/selectors.py.

```python
obtener_horarios_disponibles(*, servicio_id, barbero_id, fecha) -> list
obtener_agenda_barbero(*, actor, fecha)
obtener_citas_cliente(*, actor)
```

fecha es datetime.date en la zona horaria del negocio. La lista de horarios contiene datetime con zona horaria, ordenados. Los listados son QuerySets de Cita, ordenados por fecha_inicio y pk, limitados al actor correspondiente; no entregan toda la tabla para filtrar después en JavaScript.

No depender de un formato JSON antes de acordarlo. Django Templates y formularios son suficientes para el MVP. Website consulta el catálogo; el botón de reservar enlaza con la ruta real de Samuel una vez creada y anunciada.

Notas de implementación: obtener_horarios_disponibles devuelve [] si el servicio o el barbero no están habilitados o si el día está cerrado. obtener_agenda_barbero exige rol Barbero (PermissionDenied en otro caso) e incluye todos los estados; filtrar en la vista si solo se desean confirmadas.

Rutas de cliente ya disponibles (namespace appointments, rol Cliente):

| Ruta | Nombre | Uso |
|---|---|---|
| /citas/ | appointments:mis_citas | Próximas citas e historial |
| /citas/reservar/ | appointments:reservar | Elegir servicio, barbero, fecha y hora |
| /citas/reservar/confirmar/ | appointments:confirmar_reserva | Resumen (GET) y reserva (POST) |
| /citas/<pk>/ | appointments:detalle_cita | Detalle de una cita propia |
| /citas/<pk>/cancelar/ | appointments:cancelar_cita | Cancelación propia (solo POST) |

## Seguridad y horario: funciones ya implementadas

```python
from seguridad.roles import CLIENTE, BARBERO, ADMINISTRADOR
from seguridad.roles import obtener_rol, es_administrador, rol_requerido
from seguridad.services import registrar_cliente, asignar_rol
from core.horarios import calcular_fin_validado, validar_duracion
```

- obtener_rol(usuario): devuelve uno de los tres nombres; None si no está autenticado/activo. Sin grupo, es Cliente; un superusuario es Administrador. Grupos de negocio múltiples producen PermissionDenied, no una elección arbitraria.
- es_administrador(usuario): clasificación por rol; is_staff por sí solo no concede ese rol.
- rol_requerido(*roles): decorador de rol; combinar con login_required y permission_required para una vista privada. Además filtrar propiedad cuando corresponda. Un rol no autoriza consultar citas ajenas.
- registrar_cliente(*, username, password, first_name='', last_name='', email=''): valida usuario/contraseña, crea una cuenta no privilegiada y la asigna a Cliente. No admite campos de rol/staff/superusuario. Ya existe el servicio; falta el formulario y la vista públicos.
- asignar_rol(*, actor, usuario, rol): solo administrador; conserva un grupo de negocio y crea/reactiva/desactiva el perfil según corresponda dentro de una transacción. Rechaza retirar o desactivar un barbero con citas CONFIRMED. Si se actualizan otros campos de la cuenta, envolver guardado y asignación en una misma atomic, como hacen las vistas de seguridad.
- calcular_fin_validado(fecha_inicio, duracion_minutos, *, ahora=None): exige fecha consciente de zona horaria, inicio futuro, día abierto, alineación y cita completa en 08:00–17:00; devuelve el fin. Las constantes están en core/horarios.py. Ahora solo se pasa desde pruebas; la reserva usa el tiempo real del servidor.
- validar_duracion(valor): exige entero positivo múltiplo de 15. Los formularios/modelos de Servicio y Cita ya lo incorporan; existe además una restricción en PostgreSQL.

Después de migrate y createsuperuser, ejecutar preparar_roles. Establece los tres grupos y su matriz canónica de permisos; repetirlo no duplica grupos ni crea cuentas. Un grupo heredado/ambiguo exige revisión del equipo. No ejecutarlo esperando conservar cambios experimentales a los permisos.

Las pantallas heredadas de cuentas solo admiten un rol. La creación/eliminación/renombrado de grupos está bloqueada; la membresía se modifica desde la edición de cuenta para mantener coherente el perfil. Django Admin de usuarios, grupos, barberos y citas es de consulta; servicios se administran sin borrado físico.

## Reglas de transición aprobadas para Samuel

Cliente: cancelar su propia cita CONFIRMED solo antes de fecha_inicio. Barbero asignado o administrador: cancelar CONFIRMED, también si quedó atrasada; completar únicamente a partir de fecha_fin. Solo las operaciones de appointments/services.py implementarán estas transiciones. No volver desde CANCELLED o COMPLETED.

## Datos públicos y privados

Catálogo público: nombre/descripcion/imagen/precio/duración de servicios activos y presentación de barberos habilitados. No publicar email, historial ni datos de cuentas por consultar perfiles públicos. Agenda y datos del cliente requieren sesión, permiso y filtro de propiedad en backend.

## Imágenes locales

Pillow está declarado en requirements.txt. MEDIA_ROOT apunta a media/ y MEDIA_URL es /media/; Django sirve archivos subidos solo con DEBUG=True y media/ está ignorada por Git. Max y Wilber implementan formularios multipart y acuerdan límites de imagen con el usuario; no agregan un segundo almacenamiento. El despliegue y la persistencia de imágenes en Render se deciden al final.

## Cambiar este contrato

Si falta una función, ruta o requisito, informar al dueño del módulo y al usuario. Registrar propuesta, impacto y respuesta en docs/DECISIONES.md. Mientras no exista respuesta, no cambiar unilateralmente el contrato ni crear una alternativa con otro nombre.
