# Distrito Barber

Sistema web de una barbería. Nombre comercial provisional: **Distrito Barber**.

## Estado real

Base Django adaptada desde Binary Duo: inicio de sesión, panel de bienvenida,
usuarios, roles y permisos, perfil y gestión de contraseñas. Identidad visual
compartida en tonos carbón y cobre. Reservas, catálogo y agenda aún no implementados.

## Preparación en Windows (PowerShell)

Python 3.12 o compatible con las dependencias declaradas.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Editar `.env`: reemplazar SECRET_KEY por una clave local aleatoria. Puede generarse
con `python -c "import secrets; print(secrets.token_urlsafe(50))"`.
No subir ese archivo a Git. DEBUG=True es solo para desarrollo local.

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

Abrir http://127.0.0.1:8000/ e ingresar con la cuenta creada.

## Cambiar el nombre comercial

Cambiar `NOMBRE_BARBERIA` en `.env` y reiniciar el servidor. La marca aparece
en login, navegación, títulos, perfil y administración. El sello decorativo
del inicio contiene además las palabras DISTRITO/BARBER y el lema del login
usa «distrito»; ajustarlos si se cambia de marca. El paquete interno Django
ya fue renombrado a `distrito_barber`.

## Equipo y próximos módulos

- Usuario: arquitectura, core y autenticación.
- Samuel: citas y disponibilidad.
- Max: servicios y sitio público.
- Wilber: barberos, agenda y dashboard.

La plantilla usa `seguridad.Usuario`, Groups de Django y SQLite. No crear
un segundo usuario en accounts: conciliar primero este código con el diseño
propuesto en el chat. SQLite no certifica la prevención de reservas concurrentes.

## Verificación

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test
```

El script heredado `scripts/renombrar_proyecto.sh` solo sirve antes del primer
renombrado del paquete. Ya no es necesario ejecutarlo en este proyecto.
