# Distrito Barber: instalación local en Windows

Guía para Max, Wilber y cualquier integrante que instale el proyecto por primera vez.

Al terminar podrás abrir Distrito Barber en tu navegador, iniciar sesión con tu propio superusuario y comprobar que Django guarda la información en PostgreSQL.

## Antes de empezar

- Esta guía usa Windows, pgAdmin para administrar PostgreSQL y PowerShell para ejecutar Django. Cada paso indica dónde trabajar.
- Ejecuta los pasos en orden. Si un paso falla, resuélvelo antes de seguir.
- Copia solo el contenido de los bloques de comandos. No copies los resultados de ejemplo ni el indicador de PowerShell, como `PS C:\...>`.
- Cada compañero tiene su propia base, contraseñas y superusuario locales. Clonar GitHub descarga el código; no descarga los usuarios ni la base de los demás.
- Instalar las herramientas y descargar las dependencias requiere conexión a internet.

Tres cosas distintas que usaremos:

| Elemento | Para qué sirve |
|---|---|
| Git/GitHub | Descargar y actualizar el código |
| Python/Django | Ejecutar la aplicación |
| PostgreSQL | Guardar usuarios y demás información |
| pgAdmin | Crear y revisar la base desde una interfaz visual |

## 1. Instalar Git

1. Abre [Git para Windows](https://git-scm.com/install/win).
2. Descarga el instalador adecuado para tu equipo; en una PC Windows habitual será x64.
3. Ejecuta el instalador. Conserva las opciones predeterminadas; Git debe quedar disponible desde la línea de comandos y otras aplicaciones.
4. Al terminar, cierra las terminales que tenías abiertas.
5. Abre Inicio, escribe **PowerShell** y ábrelo. Para los comandos del proyecto no necesitas abrirlo como administrador.
6. Ejecuta:

```powershell
git --version
```

**Resultado esperado:** una línea que comienza con `git version`. El número exacto puede variar.

## 2. Instalar y comprobar Python 3.12

Para trabajar con la misma versión principal que el proyecto, utilizaremos Python 3.12.

1. Abre [la página oficial de Python](https://www.python.org/downloads/).
2. Instala **Python install manager** para Windows. Sigue los pasos de su instalador.
3. Cierra y vuelve a abrir PowerShell.
4. Con el administrador de instalación disponible, ejecuta:

```powershell
py install 3.12
```

5. Comprueba la versión:

```powershell
py -3.12 --version
```

**Resultado esperado:** `Python 3.12.x`, donde la última cifra puede cambiar.

Si ya tenías Python y el último comando funciona, no tienes que reinstalarlo. Si `py install` falla pero `py -3.12 --version` funciona, puedes continuar: probablemente estás usando el lanzador anterior de Python.

No uses Python 3.11 o anterior: Django 6.0 requiere una versión compatible más reciente. Referencias: [Python en Windows](https://docs.python.org/3/using/windows.html) y [compatibilidad de Django 6.0](https://docs.djangoproject.com/en/6.0/releases/6.0/#python-compatibility).

## 3. Instalar PostgreSQL 18 y abrir pgAdmin

**En esta parte trabajaremos con ventanas y menús de pgAdmin.** Los comandos de PowerShell se utilizarán después para Django.

PostgreSQL es el servidor que guarda los datos. **pgAdmin es la aplicación visual para administrarlo**: instalar pgAdmin por sí solo no instala necesariamente el servidor PostgreSQL.

### 3.1. Instalar las herramientas

1. Abre [PostgreSQL para Windows](https://www.postgresql.org/download/windows/).
2. Sigue el enlace al instalador de EDB y selecciona PostgreSQL **18** para Windows.
3. Ejecuta el instalador. Si Windows pide autorización para instalar, confírmala.
4. Conserva la carpeta propuesta, normalmente `C:\Program Files\PostgreSQL\18`.
5. Instala **PostgreSQL Server** y sus herramientas. Instala también **pgAdmin 4** si aparece entre los componentes o como descarga adicional.
6. Cuando pida la contraseña del usuario `postgres`, elige una y guárdala: la necesitarás para conectar pgAdmin al servidor local.
7. Conserva el puerto **5432**. Si ya está ocupado, revisa si PostgreSQL ya está instalado antes de crear otra instalación. Si usas otro puerto, anótalo para usarlo también en la conexión del proyecto.
8. Conserva la configuración regional propuesta y termina la instalación.
9. Si ofrece abrir **Stack Builder**, puedes desmarcarlo; no hace falta para el proyecto.

Si pgAdmin no quedó instalado, descárgalo desde [pgAdmin 4 para Windows](https://www.pgadmin.org/download/pgadmin-4-windows/) e instálalo aparte. Los instaladores pueden mostrar pantallas distintas según su versión.

### 3.2. Abrir pgAdmin y conectar al servidor

1. Abre Inicio de Windows, escribe **pgAdmin 4** y ábrelo.
2. A la izquierda encontrarás el explorador de objetos, normalmente llamado **Object Explorer** o **Browser**.
3. Expande **Servers**. Si aparece **PostgreSQL 18**, haz doble clic o clic derecho → **Connect Server**.
4. Cuando solicite la contraseña, escribe la del usuario `postgres` que elegiste al instalar PostgreSQL.
5. Espera a que el servidor se despliegue y puedas ver **Databases** y **Login/Group Roles**.

**Si Servers está vacío:** registra la conexión con estos pasos:

1. Clic derecho en **Servers** → **Register** → **Server...**.
2. En la pestaña **General**, escribe `PostgreSQL 18 local` en **Name**. Este es solo el nombre visible de la conexión.
3. En la pestaña **Connection**, completa:

| Campo de pgAdmin | Valor |
|---|---|
| Host name/address | `localhost` |
| Port | `5432` o tu puerto de instalación |
| Maintenance database | `postgres` |
| Username | `postgres` |
| Password | La contraseña elegida al instalar PostgreSQL |

4. Presiona **Save**. El servidor debe aparecer bajo **Servers** y permitir desplegar sus objetos.

**Si pide Master Password:** es una clave de pgAdmin para proteger las contraseñas guardadas; no es la contraseña del servidor. Puede que tu versión no la pida porque utiliza el almacén de contraseñas de Windows. Cuando pida la contraseña de `postgres`, utiliza la de PostgreSQL, no la clave maestra.

**Comprobación:** si puedes expandir el servidor y ver **Databases**, la conexión de pgAdmin funciona. Esto todavía no crea la base del proyecto: la crearemos en el paso siguiente.

## 4. Crear el usuario y la base desde pgAdmin

Mantén pgAdmin conectado con el usuario administrador `postgres`. Crearemos un usuario de base de datos llamado **barberia** y una base llamada **distrito_barber** mediante sus formularios.

### 4.1. Crear el usuario barberia

1. En el panel izquierdo, expande tu servidor PostgreSQL.
2. Busca **Login/Group Roles**.
3. Haz clic derecho en **Login/Group Roles** → **Create** → **Login/Group Role...**.
4. En la pestaña **General**, escribe `barberia` en **Name**.
5. Abre la pestaña **Definition** y completa **Password** con una contraseña propia. Guárdala: después irá en `.env`.
6. Abre la pestaña **Privileges** y deja estos valores:

| Opción | Valor | Motivo |
|---|---|---|
| Can login? | Yes | Permite que Django se conecte con esta cuenta |
| Create databases? | Yes | Permite crear la base temporal de las pruebas locales |
| Superuser? | No | La aplicación no necesita ser administradora de PostgreSQL |
| Create roles? | No | No necesita crear otros usuarios de PostgreSQL |

7. Conserva los demás valores predeterminados y presiona **Save**.
8. Expande **Login/Group Roles** y comprueba que aparezca **barberia**. Si no aparece, clic derecho en la carpeta → **Refresh**.

Una contraseña larga con letras, números, guion y guion bajo facilita su uso en la URL. Si utilizas caracteres especiales, el paso 7 explica cómo codificarlos.

**Importante:** este usuario de PostgreSQL `barberia` no es el rol Barbero del sistema. Son conceptos distintos. Los roles Cliente/Barbero/Administrador de Django se inicializan después con el comando `preparar_roles`.

### 4.2. Crear la base distrito_barber

1. En el mismo servidor, haz clic derecho sobre **Databases**.
2. Selecciona **Create** → **Database...**.
3. En **General**, completa:

| Campo | Valor |
|---|---|
| Database | `distrito_barber` |
| Owner | `barberia` |

4. En **Owner**, elige expresamente **barberia**. No dejes `postgres` como propietario por accidente.
5. Conserva el resto de la configuración y presiona **Save**.
6. Expande **Databases** y comprueba que aparezca **distrito_barber**. Si no aparece, utiliza **Refresh**.
7. Para comprobar el propietario, haz clic derecho en **distrito_barber** → **Properties** → **General** y revisa **Owner: barberia**. Cierra la ventana sin cambiar otros datos.

**Resultado esperado:** ves el usuario **barberia** en Login/Group Roles y la base **distrito_barber** en Databases, con ese usuario como propietario.

Todavía no debes crear tablas manualmente. Django las construirá mediante sus migraciones en el paso 8.

Si la cuenta o la base ya existen porque intentaste instalar antes, revisa sus propiedades. No uses Delete/Drop para empezar de nuevo: podrías borrar información.

## 5. Descargar el proyecto desde GitHub

Vuelve a **PowerShell**.

Crearemos una carpeta `Proyectos` en tus Documentos. Estos comandos usan automáticamente tu nombre de usuario de Windows:

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\Documents\Proyectos" | Out-Null
```

```powershell
cd "$env:USERPROFILE\Documents\Proyectos"
```

Descarga el repositorio:

```powershell
git clone https://github.com/Landaverde-04/Kodigo-Barberia.git
```

Si el repositorio es privado, debes haber aceptado la invitación del equipo. Cuando Git solicite iniciar sesión, utiliza tu propia cuenta de GitHub. No escribas tu contraseña de GitHub dentro de los comandos del proyecto.

Entra a la carpeta descargada:

```powershell
cd Kodigo-Barberia
```

Comprueba los archivos:

```powershell
Get-ChildItem
```

**Debes ver:** `manage.py`, `requirements.txt`, `core`, `seguridad` y `distrito_barber`.

Desde este punto, ejecuta todos los comandos del proyecto en esta carpeta, donde está `manage.py`.

**Si ya lo habías clonado:** no vuelvas a usar `git clone` dentro del proyecto. Entra a tu carpeta existente. Si no tienes cambios locales y estás en `main`, actualiza con:

```powershell
git status
```

```powershell
git pull --ff-only origin main
```

Si tienes cambios propios, coordina con el equipo antes de actualizar. No los descartes.

## 6. Crear el entorno e instalar las dependencias

El entorno virtual es una carpeta que separa las librerías de este proyecto de las de otros programas. Cada integrante crea el suyo; no se comparte por GitHub.

Ejecuta:

```powershell
py -3.12 -m venv .venv
```

Si termina sin mostrar texto, puede estar correcto. Compruébalo:

```powershell
Test-Path .\.venv\Scripts\python.exe
```

**Resultado esperado:** `True`.

Comprueba el Python del entorno:

```powershell
.\.venv\Scripts\python.exe --version
```

Instala las dependencias:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Espera hasta que regrese el indicador de PowerShell. Si la descarga termina correctamente, verás paquetes instalados o mensajes `Requirement already satisfied`.

Comprueba que las dependencias son compatibles:

```powershell
.\.venv\Scripts\python.exe -m pip check
```

**Resultado esperado:** `No broken requirements found.`

Comprueba Django:

```powershell
.\.venv\Scripts\python.exe -m django --version
```

**Resultado esperado para esta versión del repositorio:** `6.0.4`.

Usaremos siempre `.\.venv\Scripts\python.exe`. No necesitas activar el entorno ni cambiar las políticas de ejecución de PowerShell.

## 7. Crear y completar el archivo .env

Este archivo contiene la configuración privada de tu equipo.

Primero comprueba si ya existe:

```powershell
Test-Path .env
```

Si devuelve **False**, créalo copiando el ejemplo:

```powershell
Copy-Item .env.example .env
```

Si devuelve **True**, conserva el archivo existente y revisa sus datos. No lo sobrescribas cada vez que abras el proyecto.

Genera una clave privada para Django:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(50))"
```

Copia el valor completo que aparezca. No es la contraseña de ninguna cuenta; es la clave de configuración de Django.

Abre el archivo:

```powershell
notepad .env
```

Debe tener esta estructura:

```dotenv
DEBUG=True
SECRET_KEY=PEGA_AQUI_LA_CLAVE_GENERADA
ALLOWED_HOSTS=localhost,127.0.0.1
NOMBRE_BARBERIA=Distrito Barber
DATABASE_URL=postgresql://barberia:TU_PASSWORD_DE_BARBERIA@127.0.0.1:5432/distrito_barber
```

Reemplaza los dos textos en mayúsculas:

- `PEGA_AQUI_LA_CLAVE_GENERADA`: la clave que acabas de generar.
- `TU_PASSWORD_DE_BARBERIA`: la contraseña que escribiste en Definition → Password al crear `barberia` en pgAdmin. No uses la de `postgres` ni la del futuro superusuario Django.

No agregues espacios alrededor de `=` ni dividas DATABASE_URL en varias líneas. Guarda con **Ctrl + S** y cierra el Bloc de notas. El nombre del archivo debe ser exactamente `.env`, no `.env.txt`.

Si la contraseña contiene caracteres como `@`, `:`, `/`, `#` o `%`, deben codificarse para una URL. Puedes obtener la versión codificada sin escribir la contraseña directamente en el comando:

```powershell
.\.venv\Scripts\python.exe -c "from getpass import getpass; from urllib.parse import quote; print(quote(getpass('Password de barberia: '), safe=''))"
```

Escribe la contraseña cuando se solicite. Copia el resultado en el lugar de la contraseña dentro de DATABASE_URL. El resultado sigue siendo un dato privado.

Comprueba el nombre del archivo:

```powershell
Get-Item -Force .env
```

Comprueba que Git lo ignore:

```powershell
git check-ignore .env
```

**Resultado esperado:** `.env`. No compartas ese archivo ni capturas que muestren contraseñas o la clave.

## 8. Comprobar la conexión y crear las tablas

Primero revisa la configuración:

```powershell
.\.venv\Scripts\python.exe manage.py check
```

**Resultado esperado:** `System check identified no issues (0 silenced).`

Este comando revisa la configuración, pero por sí solo no demuestra que conecte a PostgreSQL. Comprueba la conexión con:

```powershell
.\.venv\Scripts\python.exe manage.py shell -c "from django.db import connection; connection.ensure_connection(); print('Motor:', connection.vendor); print('Base:', connection.settings_dict['NAME'])"
```

Entre los mensajes de salida deben aparecer:

```text
Motor: postgresql
Base: distrito_barber
```

Ahora crea las tablas aplicando las migraciones del repositorio:

```powershell
.\.venv\Scripts\python.exe manage.py migrate
```

**Resultado esperado en una base nueva:** varias líneas `Applying ... OK`. Si ya las aplicaste, puede decir `No migrations to apply`.

Comprueba el resultado:

```powershell
.\.venv\Scripts\python.exe manage.py showmigrations
```

Las migraciones existentes de `admin`, `auth`, `contenttypes`, `sessions`, `seguridad`, `services`, `barbers` y `appointments` deben tener `[X]`. Una casilla `[ ]` indica una migración pendiente.

**Comprobación visual en pgAdmin:** vuelve a pgAdmin y expande Databases → distrito_barber → Schemas → public → Tables. Haz clic derecho en Tables → Refresh. Ahora deben aparecer tablas como `seguridad_usuario`, `services_servicio`, `barbers_barbero` y `appointments_cita`. Django las creó; no hace falta agregarlas a mano.


La migración de citas instala btree_gist para evitar citas superpuestas. Si falla por permisos o por una extensión no disponible, consulta al equipo; no quites la operación ni la restricción.

**Para instalar el proyecto no necesitas ejecutar `makemigrations`.** Ese comando se usa cuando cambia un modelo; las migraciones iniciales ya están incluidas. No borres la carpeta `migrations` ni cambies a SQLite si hay un error.

## 9. Crear tu superusuario

El superusuario es una cuenta administradora **de Django**, con la que podrás entrar al sistema. Es diferente del administrador `postgres` y del usuario de base `barberia`.

Ejecuta:

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
```

Responde a las preguntas:

| Pregunta | Qué ingresar |
|---|---|
| Username / Nombre de usuario | Un nombre propio, por ejemplo `max_admin` o `wilber_admin` |
| Email address / Dirección de correo electrónico | Tu correo; el modelo actual permite dejarlo vacío |
| Password / Contraseña | Una contraseña personal y segura |
| Password (again) | La misma contraseña de nuevo |

La contraseña no se muestra mientras escribes. Si Django indica que es demasiado corta, común o similar al usuario, elige una mejor; no omitas la validación para resolverlo.

**Resultado esperado:** un mensaje como `Superuser created successfully` o su traducción.

Recuerda el **nombre de usuario** y la **contraseña Django**: son los que usarás en el navegador. No se crea un superusuario automáticamente al clonar o migrar.

Ahora inicializa los tres roles y los permisos compartidos:

```powershell
.\.venv\Scripts\python.exe manage.py preparar_roles
```

Debe indicar que preparó Cliente, Barbero y Administrador. No crea otras cuentas ni contraseñas. Si detecta grupos heredados/ambiguos, informa el caso al equipo antes de modificarlos. Repetir el comando restablece la matriz canónica de permisos sin duplicar grupos.


## 10. Iniciar el servidor y abrir el sistema

Ejecuta:

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

Debe aparecer una dirección similar a:

```text
Starting development server at http://127.0.0.1:8000/
```

**Deja esta ventana abierta.** El servidor se mantiene trabajando allí; que no vuelva el indicador de PowerShell es normal.

Abre el navegador y entra a [Distrito Barber local](http://127.0.0.1:8000/).

1. El sistema debe mostrar el inicio de sesión.
2. Introduce el superusuario y la contraseña creados en el paso 9.
3. Debes llegar al inicio de **Distrito Barber**, con la bienvenida y contenido de barbería.
4. Abre **Mi perfil** y comprueba que sea tu cuenta.
5. Como superusuario, debes poder abrir **Cuentas de la barbería** y **Roles y permisos**.
6. También puedes abrir [Django Admin local](http://127.0.0.1:8000/admin/) e ingresar con la misma cuenta.

Después de preparar_roles deben aparecer los tres grupos. Es normal que todavía no existan otras cuentas: cada equipo crea sus propios datos. Los módulos de catálogo, reservas y agenda todavía están pendientes de desarrollo.

## 11. Comprobación final

Marca cada punto después de verificarlo:

- [ ] `git --version` funciona.
- [ ] `py -3.12 --version` funciona.
- [ ] Las dependencias se instalaron y `pip check` no informa incompatibilidades.
- [ ] `.env` existe, tiene valores propios y está ignorado por Git.
- [ ] La comprobación de conexión imprime `Motor: postgresql`.
- [ ] `migrate` termina sin errores y `showmigrations` muestra `[X]`.
- [ ] Creaste un superusuario.
- [ ] Puedes iniciar sesión y abrir Mi perfil y Cuentas de la barbería.

Para comprobar que los datos permanecen guardados:

1. En la terminal del servidor, presiona **Ctrl + C** para detenerlo.
2. Ejecuta otra vez `.\.venv\Scripts\python.exe manage.py runserver`.
3. Abre nuevamente el sistema e inicia sesión con el mismo superusuario.

Si puedes entrar, la cuenta sigue guardada después de reiniciar la aplicación.

Opcionalmente, con el servidor detenido, puedes ejecutar:

```powershell
.\.venv\Scripts\python.exe manage.py test
```

Si aparece `Ran 0 tests`, significa que esa versión aún no tiene pruebas automatizadas definidas. No equivale a haber probado todas las funciones; completa también la comprobación manual anterior.

## 12. Cómo volver a abrirlo otro día

No repitas la instalación de Git, Python, PostgreSQL ni la creación de la base y del superusuario.

1. Comprueba que PostgreSQL esté iniciado.
2. Abre PowerShell y entra al proyecto:

```powershell
cd "$env:USERPROFILE\Documents\Proyectos\Kodigo-Barberia"
```

3. Inicia el servidor:

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

4. Abre `http://127.0.0.1:8000/`.

Si el equipo publicó una actualización, guarda primero tu trabajo y coordina la actualización de tu rama. Después de descargar código nuevo, vuelve a instalar `requirements.txt` si cambió y ejecuta `manage.py migrate` si hay migraciones nuevas. Conserva tu `.env`.

## 13. Errores frecuentes y soluciones

### «git no se reconoce»

Cierra y abre PowerShell después de instalar Git. Si continúa, repara su instalación y comprueba que se integre con la línea de comandos de Windows.

### «py no se reconoce» o «No suitable Python runtime found»

Instala Python install manager y Python 3.12 según el paso 2. Cierra y abre PowerShell. Antes de continuar, `py -3.12 --version` debe funcionar. Si tienes el lanzador antiguo, `py install` puede no estar disponible; no lo confundas con la comprobación de una versión ya instalada.

### GitHub dice «Repository not found»

Comprueba la URL, que estás usando la cuenta correcta y que aceptaste la invitación si el repositorio es privado. Pide acceso al responsable del repositorio.

### «destination path ... already exists» al clonar

La carpeta ya existe. Entra a ella y comprueba `git status` y que esté `manage.py`. No borres el trabajo existente ni clones repetidamente dentro de la misma carpeta.

### «can't open file ... manage.py» o no encuentra requirements.txt

Estás en otra carpeta. Ejecuta `Get-ChildItem` y entra a `Kodigo-Barberia`, donde deben estar ambos archivos.

### No encuentra `.venv\Scripts\python.exe`

Comprueba que estés en la raíz del proyecto y ejecuta `Test-Path .\.venv\Scripts\python.exe`. Si devuelve False y aún no existe el entorno, créalo con `py -3.12 -m venv .venv`.

### «No module named django» o «No module named psycopg»

Utiliza el Python del entorno y vuelve a instalar sus dependencias:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Si requirements.txt no incluye `psycopg[binary]` o `.env.example` no contiene DATABASE_URL, tienes una versión anterior del proyecto: pide al responsable que publique la actualización de PostgreSQL antes de continuar.

### «Set the SECRET_KEY environment variable» o «Set the DATABASE_URL environment variable»

Revisa que `.env` esté junto a `manage.py`, que no se llame `.env.txt` y que las variables tengan los nombres correctos. Completa los valores del paso 7 y reinicia el servidor.

### «connection refused» al conectar a PostgreSQL

Comprueba que PostgreSQL esté iniciado y que DATABASE_URL use el puerto correcto. En Windows puedes abrir **Servicios** desde Inicio, buscar el servicio de PostgreSQL 18 y revisar si está en ejecución. Iniciarlo puede requerir permisos de administrador. No cambies reglas de autenticación para resolver un servidor detenido.

### «password authentication failed for user barberia»

Revisa la contraseña de `barberia` en `.env`. No es la contraseña de `postgres` ni la de Django. Para restablecerla, conecta pgAdmin como `postgres`, abre Login/Group Roles, clic derecho en barberia → Properties → Definition, escribe la contraseña nueva en Password y guarda con Save. Actualiza también `.env` y reinicia Django. Revisa la codificación URL si contiene caracteres especiales.

### «database distrito_barber does not exist»

Falta crear la base del paso 4, o DATABASE_URL tiene otro nombre. Comprueba ambas cosas antes de volver a migrar.

### «role barberia already exists» o «database ... already exists»

Ya se crearon en un intento anterior. Revísalos en Login/Group Roles y Databases de pgAdmin, mediante clic derecho → Properties. No los borres: podrías perder datos. Si la base no pertenece a barberia, pide apoyo al responsable antes de modificar propietarios o permisos.

### «permission denied to create database» al ejecutar pruebas

Conecta pgAdmin como postgres. En Login/Group Roles, clic derecho en barberia → Properties → Privileges. Activa Create databases? en Yes y guarda con Save. Es un permiso para las pruebas locales; no necesitas cambiar las migraciones.

### «relation ... does not exist»

Normalmente faltan las tablas. Detén el servidor, confirma que la conexión apunta a tu base y ejecuta `.\.venv\Scripts\python.exe manage.py migrate`.

### «That username is already taken» al crear el superusuario

La cuenta ya existe. Prueba iniciar sesión con ella. Si olvidaste su contraseña, con el servidor detenido ejecuta:

```powershell
.\.venv\Scripts\python.exe manage.py changepassword max_admin
```

Cambia `max_admin` por el nombre real de tu cuenta local.

### El navegador no conecta al sistema

Comprueba que la terminal del servidor siga abierta y sin errores. Usa **http**, no https: `http://127.0.0.1:8000/`. Si acabas de detenerlo con Ctrl + C, vuelve a ejecutar runserver.

### «That port is already in use»

Puede que ya tengas otra terminal ejecutando el servidor. Úsala o detenla con Ctrl + C. También puedes ejecutar:

```powershell
.\.venv\Scripts\python.exe manage.py runserver 8001
```

En ese caso abre `http://127.0.0.1:8001/`.

### Necesito pedir ayuda

Envía al equipo el comando ejecutado y el mensaje de error, indicando el paso de esta guía. Antes de compartir capturas, oculta contraseñas, SECRET_KEY y DATABASE_URL. No compartas `.env`.

## Contraseñas: recordatorio

| Cuenta o clave | Dónde se usa |
|---|---|
| GitHub | Descargar o publicar código con tu propia cuenta |
| Administrador `postgres` | Conectar pgAdmin para administrar PostgreSQL |
| Usuario `barberia` | Conectar Django a la base mediante DATABASE_URL |
| Superusuario Django | Entrar a Distrito Barber y a `/admin/` |
| SECRET_KEY | Configuración privada de Django; no se escribe en el login |

Referencias oficiales: [Git](https://git-scm.com/install/win), [Python](https://docs.python.org/3/using/windows.html), [PostgreSQL Windows](https://www.postgresql.org/download/windows/), [usuarios en pgAdmin](https://www.pgadmin.org/docs/pgadmin4/latest/role_dialog.html), [bases en pgAdmin](https://www.pgadmin.org/docs/pgadmin4/latest/database_dialog.html).
