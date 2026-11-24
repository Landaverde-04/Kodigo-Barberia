# Trabajo en equipo y uso de IA

## Objetivo de esta base

Permitir que cuatro integrantes desarrollen módulos distintos sobre los mismos modelos, configuración y contratos. La existencia de una app o un modelo no significa que sus pantallas y procesos estén terminados. Consultar README.md para distinguir entregado de pendiente.

## Propiedad de los archivos

| Responsable | Puede desarrollar | Debe coordinar antes de cambiar |
|---|---|---|
| Usuario | seguridad/, core/, configuración e integración | Modelos y contratos de los demás módulos |
| Samuel | appointments/ | Usuarios, servicios, perfiles, horario, rutas globales y plantilla base |
| Max | services/, website/ | Modelos ya establecidos, seguridad, citas, perfiles y recursos compartidos |
| Wilber | barbers/, dashboard/ | Modelos establecidos, roles, lógica de citas y recursos compartidos |

Cada integrante desarrolla backend, formularios, pantallas y pruebas de su alcance. Nadie crea otro modelo de usuario, servicio, barbero o cita para evitar una dependencia.

Archivos comunes: distrito_barber/, requirements.txt, .env.example, .gitignore, core/templates/core/base.html, core/templates/core/sidebar.html, core/static/core/, AGENTS.md y documentación de contratos. La integración de cambios comunes corresponde al usuario.

## Regla obligatoria ante dudas

Si existe una duda de requisitos, datos, permisos, estados, horario, precio, contrato o responsabilidad, la IA no decide por su cuenta. Debe:

1. Leer el código y la documentación aplicable para comprobar si ya existe respuesta.
2. Explicar la duda y señalar el requisito o archivo afectado.
3. Proponer una opción con sus consecuencias, sin implementarla todavía.
4. Consultar al equipo a través del integrante que usa la IA.
5. Dejar pendiente únicamente la parte afectada y continuar tareas independientes.
6. Cuando el equipo responda, registrar el acuerdo y actualizar el código de forma coordinada.

El silencio no es aprobación. No modificar otra app «para que compile», añadir dependencias, cambiar campos, crear estados nuevos o sustituir PostgreSQL sin acuerdo. Los detalles ya definidos en los contratos se implementan sin volver a debatirlos. Para una duda puramente de sintaxis, consultar la documentación oficial antes de proponer cambios al equipo.

## Git: ramas y Pull Request

Base inicial de integración: main, hasta que el usuario publique una rama develop y lo anuncie. Ningún documento debe dar por existente una rama que no se haya creado. Cuando develop esté publicada, las nuevas tareas parten de develop y sus PR apuntan a develop; main conserva entregas estables.

Antes de empezar una tarea nueva, sin cambios pendientes:

```powershell
git status
git switch main
git pull --ff-only origin main
git switch -c feat/max-catalogo
```

El ejemplo usa main mientras no exista develop. Sustituir la rama de trabajo según la entrega: feat/samuel-reservas, feat/max-catalogo, feat/wilber-agenda o feat/usuario-registro. No copiar una rama que ya se usó para otra entrega.

Antes de crear un commit, revisar `git status` y `git diff`. Desde la raíz, añadir todos los cambios de la entrega con `git add .` y comprobar lo añadido. Ejemplo para Max:

```powershell
git add .
git diff --cached --stat
git commit -m "feat: agrega catálogo público de servicios"
git push -u origin feat/max-catalogo
```

Abrir un solo Pull Request por entrega con todos sus cambios. El mismo autor comprueba los archivos y las pruebas y pulsa Merge pull request → Confirm merge, sin esperar revisión ni aprobación de otro compañero. Close pull request lo cierra sin integrar los cambios. Los cambios compartidos siguen requiriendo coordinación previa con el equipo. No usar force push ni borrar cambios ajenos.

Si el equipo integra cambios mientras trabajas, guarda primero tu trabajo en un commit, ejecuta `git fetch origin` y coordina la incorporación de la rama base. Si aparece un conflicto, consulta al dueño del archivo; no elijas automáticamente todo lo propio o todo lo ajeno.

## Migraciones

Los modelos iniciales y sus migraciones forman una entrega común. Cada base local se crea con esas migraciones. Actualiza la rama antes de generar una nueva. Un cambio de esquema requiere acuerdo y revisión de dependencias; no editar, borrar o regenerar una migración ya compartida. No subir archivos .sqlite3 ni volcar bases con datos privados.

## Validación antes del PR

Con .env y PostgreSQL configurados:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py test
git diff --check
```

Agregar pruebas pertinentes a la entrega. Un botón oculto no sustituye el permiso del backend. Verificar casos permitidos, acceso de otro usuario y errores esperados. Las pruebas de concurrencia deben ejecutarse en PostgreSQL.

En el PR indicar comportamiento entregado, archivos compartidos afectados, comandos realmente ejecutados, resultados y limitaciones. Las capturas no deben mostrar .env, contraseñas ni datos reales.

## Plan de cinco días

| Día | Entrega |
|---|---|
| 1 | Base compartida, modelos, migraciones y lectura de documentos |
| 2 | Primer recorrido funcional de cada módulo |
| 3 | Integración: registro, catálogo, reserva y agenda conectados |
| 4 | Cerrar funcionalidades, permisos, validaciones y pruebas |
| 5 | Corregir errores, preparar demostración y versión estable |

No dejar toda la integración para el último día. Samuel entrega primero el núcleo compartido de citas; Wilber consume esas funciones. Max puede avanzar primero en catálogo y sitio público.
