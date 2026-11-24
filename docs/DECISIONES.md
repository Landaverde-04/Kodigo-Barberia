# Decisiones y asuntos pendientes

## Acordado por el usuario

- Equipo de cuatro: usuario y Samuel con experiencia; Max y Wilber principiantes.
- Plazo de cinco días y Django con apoyo de IA.
- Usuario: arquitectura y seguridad/core; Samuel: citas; Max: servicios/sitio público; Wilber: barberos/agenda/dashboard.
- Registro público como cliente; solo administrador asigna barbero.
- Roles del negocio: cliente, barbero y administrador.
- Reserva confirmada automáticamente cuando hay disponibilidad.
- Horario fijo común; agenda por barbero con navegación por fecha.
- Cancelación y finalización de citas; catálogo con precio y duración.
- PostgreSQL local. Render se prepara al final.
- Cada integrante debe tener su .md y la IA debe consultar al equipo ante cualquier duda o cambio que pueda generar conflicto.

## Conciliación con la plantilla existente

- El usuario real es seguridad.Usuario; no se crea otro modelo de usuario.
- Se mantiene ModeloBase y el idioma del código existente.
- Las apps asignadas conservan sus nombres services, website, appointments, barbers y dashboard.
- Se añaden Servicio, Barbero y Cita con relaciones protegidas y copias históricas. Los nombres de campos están en docs/MODELOS.md.
- Las pantallas y lógica nuevas son trabajo de cada integrante; esta entrega prepara estructura y datos compartidos.

## Confirmaciones aprobadas por el usuario

| ID | Decisión aprobada | Implementación / responsabilidad |
|---|---|---|
| D-01 | Conservar usuarios y grupos; tres grupos fijos: Cliente, Barbero, Administrador | Helpers, asignación y comando de inicialización entregados en seguridad |
| D-02 | Lunes a sábado, 08:00–17:00; inicios cada 15 min y duraciones múltiplos de 15 | core/horarios.py y validadores/restricciones de duración |
| D-03 | Cliente cancela antes del inicio; barbero/admin cancelan confirmadas y completan al llegar el fin | Contrato aprobado para los servicios que implementará Samuel |

Las tres respuestas se recibieron explícitamente en el chat. No quedan pendientes estas políticas. El código de transiciones de citas sigue siendo una entrega de Samuel.

## Otros límites que requieren acuerdo si se necesitan

- Reprogramación directa, elección de varios servicios por cita y reservas de administrador en nombre de otra persona.
- Atención de un servicio solo por determinados barberos.
- Bloquear también citas simultáneas del cliente con barberos diferentes.
- Política definitiva de imágenes, moneda comercial y almacenamiento para el despliegue.

El modelo admite un servicio y un barbero por cita como diseño ya propuesto; no añadir tablas adicionales sin consultar. No implementar unilateralmente reglas nuevas de cancelación o cobro.

## Cómo registrar una decisión nueva

Copiar y completar cuando el equipo responda:

```text
ID:
Pregunta o conflicto:
Propuesta:
Respuesta del equipo / responsable que la confirmó:
Archivos y módulos afectados:
Migraciones o pruebas necesarias:
Estado: pendiente / aprobada / implementada
```

Conservar la razón del cambio. Si contradice otra decisión, indicar cuál reemplaza y coordinar con todos los afectados antes de escribir código.
