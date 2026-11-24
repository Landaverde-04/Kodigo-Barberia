# Max — servicios y sitio público

## Tu responsabilidad

services/ y website/. Desarrollas formularios, vistas, plantillas y pruebas del catálogo; también la portada pública y la presentación de barberos. No debes implementar reservas ni otro sistema de usuarios.

## Leer primero

1. docs/INSTALACION_WINDOWS.md para levantar el proyecto.
2. AGENTS.md y docs/DECISIONES.md.
3. docs/MODELOS.md y docs/CONTRATOS.md.
4. docs/TRABAJO_EN_EQUIPO.md y este archivo.

Antes de programar, comprobar que puedes iniciar sesión con tu superusuario local. Tu base y tus contraseñas no se suben al repositorio.

## Modelo disponible

Importar `from services.models import Servicio`. Campos reales: nombre, descripcion, precio, duracion_minutos, imagen, activo, fecha_creacion y fecha_modificacion. No crear otra tabla de productos ni traducir los campos al inglés.

Las imágenes son opcionales. Los precios usan Decimal. La duración debe ser positiva y respetar la política aprobada en D-02 ya confirmada.

## Orden sugerido de entregas pequeñas

### 1. Lista pública de servicios

- Agregar la vista en website/views.py y su ruta en website/urls.py.
- Consultar solo Servicio.objects.filter(activo=True).
- Mostrar nombre, descripción, precio y duración; usar texto o recurso visual apropiado si no hay imagen.
- El visitante puede verla sin iniciar sesión. No decorar una página pública con login_required.
- No colocar datos inventados en el código para simular la base; crear tus datos locales desde la administración disponible.

### 2. Administración del catálogo

- Añadir ModelForm de Servicio con una lista explícita de campos editables; nunca fields='__all__'.
- Implementar listado, creación, edición y activación/desactivación solo para administrador usando los helpers compartidos.
- Usar is_valid antes de guardar; mostrar errores por campo.
- No borrar servicios con historial ni alterar citas cuando cambie precio/duración.
- Escribir mediante POST y CSRF; al guardar correctamente, redirigir y mostrar un mensaje.

### 3. Portada pública

- Bajo /web/, mostrar identidad Distrito Barber y accesos a catálogo e inicio de sesión.
- Usar la identidad compartida, Bootstrap y recursos existentes.
- No inventar dirección, teléfono, redes sociales ni horario definitivo. Consultar al usuario los datos comerciales que falten.
- Coordinar la plantilla pública con el usuario antes de crear otro layout general.

### 4. Catálogo de barberos

- Consultar barbers.Barbero y su usuario, sin crear perfiles propios.
- Filtrar perfiles y cuentas habilitados y reutilizar obtener_rol/BARBERO de seguridad.roles.
- Mostrar nombre, descripción y foto opcional. No publicar correo, datos de cuenta ni historial.

### 5. Enlace al flujo de reserva

- Samuel anuncia la ruta real de su formulario.
- Enlazar con el namespace acordado; no inventar una API, un nombre de URL o una segunda pantalla de reservas.
- Hasta que exista, no mostrar un botón de reserva que termine en error ni un mensaje de confirmación simulado.

## Archivos y plantillas

Tu app ya tiene urls.py y está incluida globalmente. Usa templates/services/, templates/website/ y static/<app>/. Las vistas privadas extienden core/base.html y usan bloques titulo/contenido/estilos_extra/scripts_extra. No cambies el CSS o sidebar comunes sin coordinar.

Si habilitas imágenes, el formulario necesita enctype='multipart/form-data' y la vista debe recibir request.FILES. La configuración local de media ya existe; acuerda límites de archivo con el usuario; no elijas un proveedor de almacenamiento o librería nueva por tu cuenta.

## Cómo comprobar cada entrega

- Visitante ve servicios activos, precio y duración.
- Servicio inactivo desaparece de la oferta pública.
- Imagen ausente no rompe la página.
- Precio negativo y duración inválida muestran error y no se guardan.
- Un cliente no entra al CRUD aunque escriba la URL directamente.
- Cambiar un servicio no modifica el precio ni duración de una cita anterior.
- La pantalla se puede usar en móvil y los enlaces llevan a rutas existentes.

Ejecutar pruebas de tu módulo y las comprobaciones generales antes del PR. Integrar tu propia entrega mediante Pull Request, siguiendo GUIA_GITHUB.md, sin esperar revisión de otro compañero. No borrar tests o migraciones para que una comprobación pase.

## Qué debes consultar

Datos comerciales faltantes; moneda definitiva; cualquier cambio a la política de duración aprobada; diseño público que requiera un layout nuevo; cualquier campo, permiso, ruta o función de otro módulo que necesites cambiar. Describe el problema y una propuesta; espera respuesta antes de implementarla.

## Prompt para tu IA

```text
Lee AGENTS.md y la documentación obligatoria. Soy Max, principiante en Django.
Mi alcance es services y website. Sigue MAX.md.
Quiero completar esta entrega pequeña: [indicar entrega].
Explícame los cambios y los comandos paso a paso. Usa los modelos existentes.
No cambies configuración, modelos compartidos ni trabajo de Samuel o Wilber.
Si hay una duda o hace falta un cambio compartido, explícame qué consultar
con el equipo y espera la respuesta; no decidas por tu cuenta.
Al terminar, indica cómo comprobarlo, las pruebas ejecutadas y lo pendiente.
```
