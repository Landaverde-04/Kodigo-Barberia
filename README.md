# Distrito Barber

Sistema de una barbería desarrollado por cuatro integrantes en cinco días. Esta entrega prepara la base compartida: modelos, migraciones, estructura, utilidades de seguridad/horario y documentación para trabajar en paralelo. Las funcionalidades de cada módulo se desarrollan a partir de esta base.

## Empieza por tu documento

| Integrante | Aplicaciones | Documento |
|---|---|---|
| Landaverde-04 | seguridad, core y arquitectura | [Tu trabajo](docs/tareas/LANDAVERDE-04.md) |
| Samuel | appointments | [Citas y disponibilidad](docs/tareas/SAMUEL.md) |
| Max | services, website | [Servicios y sitio público](docs/tareas/MAX.md) |
| Wilber | barbers, dashboard | [Barberos, agenda y dashboard](docs/tareas/WILBER.md) |

Antes de pasar tu tarea a una IA, indícale que lea [AGENTS.md](AGENTS.md), los documentos comunes y tu archivo individual. Cada tarea incluye un prompt. Ante dudas, incertidumbre o cambios que afecten trabajo ajeno, consultar al equipo antes de implementarlos.

## Documentación común

- [Instalación Windows paso a paso](docs/INSTALACION_WINDOWS.md).
- [Decisiones aprobadas y límites](docs/DECISIONES.md).
- [Modelos y relaciones](docs/MODELOS.md).
- [Contratos entre módulos](docs/CONTRATOS.md).
- [Trabajo en equipo y Git](docs/TRABAJO_EN_EQUIPO.md).
- [CLAUDE.md](CLAUDE.md): entrada a las mismas reglas para Claude.

## Estado real

Disponible: login/logout, administración heredada de cuentas/permisos, perfil y contraseñas; marca Distrito Barber; PostgreSQL; modelos Servicio/Barbero/Cita; migraciones; restricciones de integridad y superposición; clasificación de roles, asignación transaccional de barbero, servicio seguro de registro y validación del horario común; inicialización de roles; pruebas automatizadas.

Pendiente: pantalla pública de registro, portada/catálogo, flujo completo de reservas/disponibilidad/transiciones, agenda del barbero y dashboard. Los modelos y helpers no sustituyen esas funcionalidades. Las cinco apps nuevas tienen URLs globales incluidas y urlpatterns vacío: sus pantallas las construye cada responsable. No hay enlaces ficticios a vistas inexistentes.

El catálogo se puede cargar desde Django Admin con un superusuario. Allí usuarios, grupos, perfiles y citas se ofrecen en modo consulta para evitar escrituras que omitan reglas. Las cuentas y sus roles se editan desde /seguridad/; la asignación Barbero crea/reactiva el perfil. No se crean superusuarios ni contraseñas predeterminadas.

## Estructura

```text
distrito_barber/  configuración y rutas generales — usuario
core/             ModeloBase, horario, identidad y layout — usuario
seguridad/        Usuario, roles, autenticación y permisos — usuario
services/         Servicio y catálogo — Max
website/          sitio público, sin tablas propias — Max
appointments/     Cita, disponibilidad y transiciones — Samuel
barbers/          Barbero y agenda propia — Wilber
dashboard/        consultas administrativas, sin tablas propias — Wilber
docs/             decisiones, contratos, instalación y tareas
```

Usuario único: seguridad.Usuario. No crear accounts.User ni una tabla Cliente. Las apps conservan los nombres distribuidos; los modelos/campos/funciones nuevos siguen el español sin tildes de la plantilla.

## Acuerdos básicos

- Grupos fijos: Cliente, Barbero y Administrador. Superusuario equivale a administrador; is_staff por sí solo no es rol del negocio.
- Horario común: lunes a sábado, 08:00–17:00, zona America/El_Salvador; comienzos y duraciones en intervalos de 15 minutos.
- Reserva disponible: CONFIRMED automáticamente. Solo se pasa a CANCELLED o COMPLETED.
- Cliente cancela su cita antes del inicio. Barbero asignado/admin cancelan confirmadas y completan a partir de la hora de fin.
- Precio/duración/nombre se conservan en la cita al reservar. No recalcular históricos al editar el catálogo.
- PostgreSQL local; Render se prepara al final.

## Instalación rápida (PowerShell)

Para principiantes, seguir la guía detallada enlazada arriba. Aquí se asumen Python 3.12 y PostgreSQL 18 instalados.

```powershell
git clone https://github.com/Landaverde-04/Kodigo-Barberia.git
cd Kodigo-Barberia
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

En pgAdmin, conectar al servidor local como postgres. En Login/Group Roles → Create → Login/Group Role, crear barberia, asignarle una contraseña y activar Can login? y Create databases? (para pruebas locales). Mantener Superuser? y Create roles? en No. En Databases → Create → Database, crear distrito_barber y seleccionar Owner: barberia.

La guía detallada explica cada pestaña, valor y comprobación. Si el usuario o la base ya existen, revisar sus propiedades; no borrarlos ni recrearlos.

En PowerShell, copiar .env.example a .env solo si todavía no existe. Completar SECRET_KEY y DATABASE_URL con los valores de tu equipo. Generar una clave con:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(50))"
```

No subir .env ni compartir sus credenciales. Conservar DEBUG=True y los hosts locales para desarrollo.

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py preparar_roles
.\.venv\Scripts\python.exe manage.py runserver
```

Abrir http://127.0.0.1:8000/ e ingresar con la cuenta creada. Django Admin está en /admin/. preparar_roles es idempotente: inicializa los tres grupos y establece la matriz canónica de permisos; no crea cuentas. No ejecutarlo para conservar cambios experimentales de permisos: coordinar antes cualquier modificación de esa matriz.

La migración de appointments instala btree_gist, necesaria para evitar intervalos superpuestos. La cuenta propietaria de la base puede instalar esta extensión trusted. Si falla, consultar permisos/instalación con el equipo; no quitar la operación ni la restricción. Las migraciones anteriores de seguridad se conservan intactas.

## Actualización y comprobaciones

Después de incorporar una actualización coordinada, instalar requirements.txt y aplicar migrate. No ejecutar makemigrations solo por descargar código.

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test
git diff --check
```

Las pruebas usan PostgreSQL y crean/destruyen su propia base temporal. No borrar migraciones o datos de otros compañeros. La instalación no importa automáticamente información desde SQLite.

## Imágenes y despliegue

Las imágenes locales van a media/ y se sirven bajo /media/ únicamente con DEBUG=True. media/, .venv/ y .env están ignorados por Git. La marca se configura con NOMBRE_BARBERIA; el sello del inicio contiene además las palabras DISTRITO/BARBER.

Render y la persistencia de imágenes en producción se prepararán al final. No añadir archivos ni dependencias de despliegue en esta etapa.
