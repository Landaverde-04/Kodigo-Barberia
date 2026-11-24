# Landaverde-04 — arquitectura, seguridad e integración

## Tu responsabilidad

Mantener core/, seguridad/, distrito_barber/, la instalación y los contratos compartidos. La propuesta original accounts/core se implementa sobre seguridad/core porque la plantilla ya tiene el usuario y sus tablas. No crear un segundo usuario.

## Leer primero

AGENTS.md → docs/DECISIONES.md → docs/MODELOS.md → docs/CONTRATOS.md → docs/TRABAJO_EN_EQUIPO.md. D-01, D-02 y D-03 ya están aprobadas; aplicar sus reglas sin reinterpretarlas.

## Qué recibes

Login/logout, cuentas, perfil y cambio de contraseña; base visual Distrito Barber; PostgreSQL; siete apps; modelos y migraciones comunes. Ya existen helpers de roles, registro y asignación de barbero; grupos fijos y formularios con un solo rol, más horario compartido y comando preparar_roles. No repetir lo entregado.

## Orden de implementación

1. Revisar las decisiones ya aprobadas y coordinar solo requisitos nuevos.
2. Reutilizar los helpers de rol ya entregados en seguridad/roles.py. No deducir un rol del negocio solo por is_staff.
3. Añadir la pantalla pública de registro usando registrar_cliente: formulario con campos permitidos y errores claros. El servicio ya fuerza Cliente; no aceptar campos privilegiados del navegador.
4. Reutilizar asignar_rol, ya integrado en las cuentas administrativas: actualizar rol y crear/reactivar Barbero en una transacción; no crear perfiles mediante signals ocultas.
5. Antes de desactivar un usuario/barbero o retirar su rol, resolver sus citas confirmadas. No cancelar ni reasignar silenciosamente.
6. Mantener la protección ya entregada contra borrado de usuarios referenciados y contra renombrar/crear/eliminar los tres grupos. Revisar la experiencia de baja lógica al integrar sin duplicar la asignación de rol/perfil.
7. Mantener core/horarios.py, que ya implementa el horario aprobado para Samuel. No duplicar constantes por app.
8. Mantener la configuración local de media ya disponible y coordinar validaciones con Max y Wilber.
9. Integrar navegación solo cuando existan las rutas de cada compañero; no añadir enlaces a vistas inexistentes.
10. Mantener el comando preparar_roles ya entregado, posterior a migrate. No crear contraseñas predeterminadas ni un superusuario automático.

## Contratos que debes entregar temprano

Las firmas de identidad/roles, registro, asignación y horario ya están documentadas en CONTRATOS.md; conservarlas. Anunciar esos nombres antes de que los demás construyan permisos o formularios. No cambiar después las firmas sin coordinar.

## Pruebas mínimas

- Registro manipulado no crea staff, superusuario ni barbero.
- Cliente no abre administración aunque cambie la URL.
- Una asignación coherente crea un solo perfil por usuario; repetirla no duplica.
- Roles y perfil no quedan a medias si falla una transacción.
- La baja de una cuenta con historial no borra citas ni produce una página de error SQL.
- El comando de inicialización se puede ejecutar dos veces sin duplicar grupos/permisos.
- Instalación desde una base vacía y migración de una base con las migraciones originales de seguridad.

## Límites

La lógica de citas pertenece a Samuel, el sitio público a Max y la agenda/dashboard a Wilber. Revisar e integrar no significa reescribir módulos ajenos sin avisar. Render, pagos, notificaciones y sucursales quedan fuera de esta etapa.

## Listo para revisión cuando

Las decisiones aprobadas y cualquier acuerdo nuevo están registrados, los helpers existen y son conocidos por el equipo, el registro es seguro y la guía de instalación coincide con los comandos. Informar qué está probado y qué sigue pendiente; no declarar toda la aplicación terminada solo por tener modelos.

## Prompt para tu IA

```text
Lee AGENTS.md y la documentación obligatoria. Soy el responsable de arquitectura,
core y seguridad. Revisa docs/tareas/LANDAVERDE-04.md y el código existente.
Mi entrega concreta de hoy es: [indicar entrega].
Respeta seguridad.Usuario, los modelos y las firmas compartidas.
Ante una duda o cambio que afecte a otro integrante, explica el impacto y
propón una alternativa para consultarla con el equipo. No la implementes
sin respuesta. Continúa únicamente con las tareas independientes.
Al terminar, resume cambios, pruebas ejecutadas y pendientes.
```
