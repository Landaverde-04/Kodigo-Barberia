# Instrucciones comunes para IA — Distrito Barber

## Lectura obligatoria

Antes de modificar código, leer README.md, docs/DECISIONES.md, docs/MODELOS.md, docs/CONTRATOS.md, docs/TRABAJO_EN_EQUIPO.md y el archivo de la persona que solicita el trabajo en docs/tareas/. CLAUDE.md remite a estas mismas reglas; no representa una arquitectura distinta.

Consultar el código real para comprobar qué funciones existen. No confundir un contrato previsto con una implementación. No anunciar como funcional un módulo que solo tenga modelos o carpetas.

## Regla de consulta del equipo

El usuario pidió expresamente que ante dudas o incertidumbre no se tomen decisiones unilaterales. Si falta una regla, hay contradicción, cambia el alcance o se necesita tocar trabajo de otra persona:

1. Leer la documentación y el código afectados.
2. Exponer la duda y su impacto al integrante que está utilizando la IA.
3. Sugerir una alternativa concreta para que consulte con el equipo.
4. Esperar la respuesta antes de implementar la parte afectada. No considerar el silencio una aprobación.
5. Continuar solo las tareas independientes y documentar el acuerdo recibido.

Esta regla incluye decisiones sobre modelos, migraciones, roles, horario, estados, rutas, contratos compartidos, dependencias y archivos comunes. Una decisión marcada pendiente en docs/DECISIONES.md no es permiso para elegir por defecto.

## Responsables

- Usuario: seguridad/, core/, distrito_barber/, configuración e integración.
- Samuel: appointments/.
- Max: services/ y website/.
- Wilber: barbers/ y dashboard/.

Trabajar en el alcance solicitado y coordinar cambios ajenos. Los modelos iniciales están compartidos: su dueño mantiene el archivo, pero no cambia sus campos sin acuerdo del equipo.

## Arquitectura y seguridad

- Conservar seguridad.Usuario, AUTH_USER_MODEL y sus migraciones existentes. No crear accounts.User ni Cliente.
- Modelos propios y nombres de funciones en español sin tildes; interfaces en español. Conservar los nombres de apps ya asignados.
- PostgreSQL local obligatorio, configuración privada en .env y dependencias en requirements.txt. Render se prepara al final.
- Reutilizar ModeloBase salvo Usuario, que hereda de AbstractUser.
- Confirmación automática: CONFIRMED, CANCELLED y COMPLETED. No introducir PENDING.
- Toda escritura de citas debe pasar por appointments/services.py cuando Samuel lo implemente. No crear una segunda lógica desde barbers/dashboard.
- Aplicar permisos y propiedad en backend, no solo botones ocultos. POST + CSRF para escrituras; GET no cancela ni completa.
- Usar precios decimales y conservar snapshots históricos. No borrar referencias del historial.
- No eliminar la restricción de superposición ni la extensión btree_gist para resolver un fallo de migración. Consultar al equipo.
- No borrar ni editar migraciones aplicadas, resetear bases, usar force push, sobrescribir trabajo ajeno ni incluir secretos.
- No añadir pagos, sucursales, notificaciones o horarios individuales al MVP.

## Entrega

Implementar entregas pequeñas en una rama propia. Revisar permisos, casos inválidos y comportamiento real; ejecutar las comprobaciones de docs/TRABAJO_EN_EQUIPO.md. Las pruebas de base/concurrencia requieren PostgreSQL.

Al terminar, informar: qué se implementó, archivos modificados, pruebas realmente ejecutadas, resultados y pendientes. Si existe una incertidumbre sin respuesta, indicarla expresamente. No afirmar que se probó lo que no se ejecutó.
