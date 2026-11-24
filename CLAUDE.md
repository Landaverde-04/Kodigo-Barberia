# Distrito Barber — contexto para asistentes

La fuente común de instrucciones es [AGENTS.md](AGENTS.md). Leerla antes de modificar código. No aplicar convenciones de una copia antigua de la plantilla que contradigan estos contratos.

## Lectura obligatoria

1. [README](README.md): estado real y estructura.
2. [Decisiones](docs/DECISIONES.md): acuerdos aprobados y límites.
3. [Modelos](docs/MODELOS.md): campos y restricciones.
4. [Contratos](docs/CONTRATOS.md): funciones entregadas y pendientes.
5. [Trabajo en equipo](docs/TRABAJO_EN_EQUIPO.md): Git y consulta de dudas.
6. Documento individual en la raíz: LANDAVERDE-04.md, SAMUEL.md, MAX.md o WILBER.md.

## Base fija

Django 6.0.4, Python 3.12, PostgreSQL 18 local, django-environ, templates Django, Bootstrap y JavaScript vanilla. Conservar seguridad.Usuario, ModeloBase y middleware de cambio de contraseña. Nombres propios de código en español sin tildes; conservar las apps asignadas.

Roles fijos sobre Groups: Cliente, Barbero, Administrador. Usar seguridad/roles.py y seguridad/services.py; no crear otro campo de rol ni otro usuario. Horario común aprobado en core/horarios.py. Los servicios de negocio de citas son responsabilidad de Samuel y aún no están implementados.

Ante una duda o cambio compartido, exponer problema e impacto, sugerir una opción para consultar al equipo y esperar respuesta antes de implementarla. No asumir aprobación por silencio. Mantener los contratos actualizados con cada decisión aceptada.

Instalación detallada en docs/INSTALACION_WINDOWS.md. Render se prepara al final.
