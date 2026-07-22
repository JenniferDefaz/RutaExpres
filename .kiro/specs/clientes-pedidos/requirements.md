# Requirements Document

## Introduction

RutaExpres es una aplicación web de logística y transporte desarrollada con Django. Actualmente cuenta con una vista de inicio y una estructura básica. Esta funcionalidad añade un sistema completo de registro de clientes y pedidos, incluyendo seguimiento de envíos, administración y notificaciones mediante SweetAlert2. Toda la interfaz de usuario extiende la plantilla base existente (`plantillaPrin.html`) sin alterar el diseño visual.

## Glossary

- **Sistema**: La aplicación web Django RutaExpres.
- **Cliente**: Persona natural o jurídica registrada en el sistema con datos de contacto.
- **Pedido**: Solicitud de transporte creada por o para un Cliente, con número de tracking único.
- **Número_de_Tracking**: Identificador único auto-generado asignado a cada Pedido para su rastreo.
- **Tipo_de_Servicio**: Modalidad de transporte elegida: aéreo, marítimo, terrestre o tren.
- **Estado_del_Pedido**: Fase actual del Pedido: pendiente, en_tránsito, entregado o cancelado.
- **Formulario**: Componente Django (ModelForm) que valida y procesa la entrada del usuario.
- **Vista**: Función de Django que procesa peticiones HTTP y devuelve respuestas.
- **Plantilla**: Archivo HTML de Django que extiende `plantillaPrin.html`.
- **SweetAlert2**: Biblioteca JavaScript para mostrar alertas, confirmaciones y mensajes de error con estilo.
- **Admin**: Panel de administración de Django accesible solo por staff/superusuarios.
- **Staff**: Usuario de Django con el atributo `is_staff=True`.

---

## Requirements

### Requisito 1: Modelos de Datos

**Historia de Usuario:** Como administrador del sistema, quiero modelos de datos bien definidos para Clientes y Pedidos, para que la información se almacene de forma estructurada y consistente en la base de datos.

#### Criterios de Aceptación

1. THE Sistema SHALL definir un modelo `Cliente` con los campos: `nombre` (CharField, máx. 100 caracteres), `apellido` (CharField, máx. 100 caracteres), `email` (EmailField, único), `telefono` (CharField, máx. 20 caracteres), `direccion` (TextField), `fecha_registro` (DateTimeField, auto_now_add=True).
2. THE Sistema SHALL definir un modelo `Pedido` con los campos: `cliente` (ForeignKey a Cliente, on_delete=CASCADE), `numero_tracking` (CharField, único, máx. 20 caracteres), `tipo_servicio` (CharField con choices: aereo/maritimo/terrestre/tren), `origen` (CharField, máx. 200 caracteres), `destino` (CharField, máx. 200 caracteres), `descripcion_carga` (TextField), `peso_kg` (DecimalField, max_digits=8, decimal_places=2), `estado` (CharField con choices: pendiente/en_transito/entregado/cancelado, default='pendiente'), `fecha_creacion` (DateTimeField, auto_now_add=True), `fecha_actualizacion` (DateTimeField, auto_now=True).
3. WHEN un nuevo Pedido es creado sin `numero_tracking`, THE Sistema SHALL auto-generar un número de tracking único con el formato `RX-YYYYMMDD-XXXX` donde `XXXX` es un sufijo alfanumérico aleatorio de 6 caracteres en mayúsculas.
4. THE modelo `Cliente` SHALL implementar el método `__str__` retornando el nombre completo del cliente en formato `"{nombre} {apellido}"`.
5. THE modelo `Pedido` SHALL implementar el método `__str__` retornando el número de tracking del pedido.
6. IF el campo `peso_kg` recibe un valor menor o igual a cero, THEN THE Sistema SHALL rechazar el valor con un error de validación.
7. THE Sistema SHALL usar `DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'` en `settings.py`.

---

### Requisito 2: Formularios de Entrada

**Historia de Usuario:** Como usuario, quiero formularios con validación robusta para registrar clientes y pedidos, para que los datos ingresados sean correctos antes de guardarse en la base de datos.

#### Criterios de Aceptación

1. THE Sistema SHALL implementar `ClienteForm` (ModelForm de Cliente) que valide que el campo `email` tenga formato de correo electrónico válido según RFC 5322.
2. WHEN el campo `email` del `ClienteForm` ya existe en la base de datos, THE Sistema SHALL rechazar el formulario y retornar el mensaje de error "Ya existe un cliente registrado con este correo electrónico."
3. THE Sistema SHALL implementar validación del campo `telefono` en `ClienteForm` que rechace valores con caracteres no numéricos, espacios, guiones o paréntesis fuera de los permitidos, retornando el mensaje "El teléfono solo puede contener números, espacios, guiones y paréntesis."
4. THE Sistema SHALL implementar `PedidoForm` (ModelForm de Pedido) que valide que todos los campos requeridos estén presentes antes de guardar.
5. WHEN el campo `peso_kg` del `PedidoForm` recibe un valor menor o igual a cero, THE Sistema SHALL rechazar el formulario con el mensaje de error "El peso debe ser mayor que cero."
6. THE Sistema SHALL implementar `BuscarPedidoForm` con un campo `numero_tracking` (CharField) para buscar pedidos por número de tracking.
7. WHERE el campo `numero_tracking` del `BuscarPedidoForm` esté vacío al enviar, THE Sistema SHALL retornar el mensaje de error "Por favor ingrese un número de tracking."

---

### Requisito 3: Vistas y Lógica de Negocio

**Historia de Usuario:** Como usuario, quiero vistas funcionales para registrar clientes, registrar pedidos, rastrear envíos y ver detalles, para que pueda interactuar con el sistema de logística desde el navegador.

#### Criterios de Aceptación

1. THE Sistema SHALL mantener la vista `inicio` existente que renderiza `inicio.html` sin cambios funcionales.
2. WHEN el usuario accede a `cliente/registro/` con GET, THE Sistema SHALL mostrar el formulario `ClienteForm` vacío en la plantilla `registro_cliente.html`.
3. WHEN el usuario envía `ClienteForm` con datos válidos mediante POST, THE Sistema SHALL guardar el cliente, añadir un mensaje de éxito de Django y redirigir a `registrar_pedido`.
4. IF el usuario envía `ClienteForm` con datos inválidos mediante POST, THEN THE Sistema SHALL re-renderizar `registro_cliente.html` con los errores de validación correspondientes.
5. WHEN el usuario accede a `pedido/nuevo/` con GET, THE Sistema SHALL mostrar el formulario `PedidoForm` vacío en la plantilla `registro_pedido.html`.
6. WHEN el usuario envía `PedidoForm` con datos válidos mediante POST, THE Sistema SHALL guardar el pedido con número de tracking auto-generado, añadir un mensaje de éxito de Django y redirigir a `detalle_pedido` con el tracking generado.
7. IF el usuario envía `PedidoForm` con datos inválidos mediante POST, THEN THE Sistema SHALL re-renderizar `registro_pedido.html` con los errores de validación correspondientes.
8. WHEN el usuario accede a `pedido/rastrear/` con GET, THE Sistema SHALL mostrar el formulario `BuscarPedidoForm` vacío en la plantilla `rastrear_pedido.html`.
9. WHEN el usuario envía `BuscarPedidoForm` con un número de tracking válido mediante POST, THE Sistema SHALL buscar el pedido y mostrar el resultado en `rastrear_pedido.html`.
10. IF el número de tracking enviado en `BuscarPedidoForm` no existe en la base de datos, THEN THE Sistema SHALL mostrar un mensaje de error "No se encontró ningún pedido con el tracking ingresado." en `rastrear_pedido.html`.
11. WHEN el usuario accede a `pedido/<str:tracking>/`, THE Sistema SHALL recuperar el pedido por `numero_tracking` y mostrarlo en la plantilla `detalle_pedido.html`.
12. IF el número de tracking en la URL no existe, THEN THE Sistema SHALL retornar una respuesta HTTP 404.
13. WHEN un usuario con `is_staff=True` accede a `pedido/lista/`, THE Sistema SHALL mostrar todos los pedidos en la plantilla `lista_pedidos.html`.
14. IF un usuario sin `is_staff=True` intenta acceder a `pedido/lista/`, THEN THE Sistema SHALL redirigir al usuario a la página de inicio de sesión de Django.

---

### Requisito 4: URLs y Enrutamiento

**Historia de Usuario:** Como desarrollador, quiero URLs bien definidas y con nombres, para que las plantillas y vistas puedan referenciarse de forma consistente con `{% url %}`.

#### Criterios de Aceptación

1. THE Sistema SHALL registrar la ruta `''` hacia la vista `inicio` con el nombre `'inicio'` en `pedido/urls.py`.
2. THE Sistema SHALL registrar la ruta `'cliente/registro/'` hacia la vista `registrar_cliente` con el nombre `'registrar_cliente'`.
3. THE Sistema SHALL registrar la ruta `'pedido/nuevo/'` hacia la vista `registrar_pedido` con el nombre `'registrar_pedido'`.
4. THE Sistema SHALL registrar la ruta `'pedido/rastrear/'` hacia la vista `rastrear_pedido` con el nombre `'rastrear_pedido'`.
5. THE Sistema SHALL registrar la ruta `'pedido/lista/'` hacia la vista `lista_pedidos` con el nombre `'lista_pedidos'`.
6. THE Sistema SHALL registrar la ruta `'pedido/<str:tracking>/'` hacia la vista `detalle_pedido` con el nombre `'detalle_pedido'`.
7. THE Sistema SHALL incluir las URLs de `pedido.urls` en el archivo `RutaExpres/urls.py` mediante `include('pedido.urls')`.

---

### Requisito 5: Plantillas y Diseño Visual

**Historia de Usuario:** Como usuario final, quiero plantillas HTML funcionales y visualmente consistentes con el diseño existente, para que la experiencia de uso sea coherente en toda la aplicación.

#### Criterios de Aceptación

1. THE Sistema SHALL crear las plantillas `registro_cliente.html`, `registro_pedido.html`, `rastrear_pedido.html`, `detalle_pedido.html` y `lista_pedidos.html` extendiendo `plantillaPrin.html` usando `{% extends './plantillaPrin.html' %}`.
2. THE Sistema SHALL usar únicamente clases CSS de Bootstrap 5 y las clases personalizadas del tema existente en las plantillas nuevas, sin agregar estilos CSS adicionales ni modificar `style.css`.
3. THE Sistema SHALL incluir el token CSRF `{% csrf_token %}` en todos los formularios POST de las plantillas.
4. THE Sistema SHALL reemplazar los enlaces del navbar en `plantillaPrin.html` con `{% url 'nombre_vista' %}` en lugar de rutas hardcodeadas con extensión `.html`.
5. THE Sistema SHALL agregar enlaces de navegación en el navbar de `plantillaPrin.html` para las vistas `registrar_cliente`, `registrar_pedido` y `rastrear_pedido`, sin modificar el estilo visual del navbar.
6. THE Sistema SHALL mostrar en `detalle_pedido.html` todos los campos del pedido: número de tracking, cliente, tipo de servicio, origen, destino, descripción de carga, peso, estado, fecha de creación y fecha de actualización.
7. THE Sistema SHALL mostrar en `lista_pedidos.html` una tabla con columnas para: número de tracking, cliente, tipo de servicio, origen, destino, estado y fecha de creación, con un enlace al detalle de cada pedido.

---

### Requisito 6: Notificaciones con SweetAlert2

**Historia de Usuario:** Como usuario, quiero que todas las alertas, confirmaciones y mensajes de error se muestren con SweetAlert2, para que la experiencia de notificaciones sea visualmente atractiva y coherente.

#### Criterios de Aceptación

1. THE Sistema SHALL incluir `<script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>` en las plantillas que muestran mensajes al usuario.
2. WHEN el framework de mensajes de Django contiene mensajes tras un POST exitoso, THE Sistema SHALL renderizar un bloque `{% if messages %}` en la plantilla que dispare `Swal.fire(...)` con tipo `'success'` y el texto del mensaje.
3. WHEN el framework de mensajes de Django contiene mensajes de error, THE Sistema SHALL renderizar `Swal.fire(...)` con tipo `'error'` y el texto del mensaje correspondiente.
4. THE Sistema SHALL usar `messages.success()` en las vistas para mensajes de éxito y `messages.error()` para mensajes de error, antes de redirigir.
5. THE Sistema SHALL configurar `MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'` en `settings.py` para que los mensajes persistan correctamente en redirecciones.

---

### Requisito 7: Panel de Administración

**Historia de Usuario:** Como administrador, quiero gestionar clientes y pedidos desde el panel de administración de Django, para que pueda revisar, filtrar y buscar registros de forma eficiente.

#### Criterios de Aceptación

1. THE Sistema SHALL registrar el modelo `Cliente` en `pedido/admin.py` con `list_display` que muestre: `nombre`, `apellido`, `email`, `telefono`, `fecha_registro`.
2. THE Sistema SHALL configurar `search_fields` para `Cliente` en admin con los campos: `nombre`, `apellido`, `email`.
3. THE Sistema SHALL configurar `list_filter` para `Cliente` en admin con el campo: `fecha_registro`.
4. THE Sistema SHALL registrar el modelo `Pedido` en `pedido/admin.py` con `list_display` que muestre: `numero_tracking`, `cliente`, `tipo_servicio`, `estado`, `fecha_creacion`.
5. THE Sistema SHALL configurar `search_fields` para `Pedido` en admin con los campos: `numero_tracking`, `cliente__nombre`, `cliente__apellido`.
6. THE Sistema SHALL configurar `list_filter` para `Pedido` en admin con los campos: `estado`, `tipo_servicio`, `fecha_creacion`.

---

### Requisito 8: Configuración del Proyecto

**Historia de Usuario:** Como desarrollador, quiero que la configuración de Django esté correctamente ajustada para el proyecto RutaExpres, para que la zona horaria, archivos estáticos y dependencias funcionen correctamente en producción y desarrollo.

#### Criterios de Aceptación

1. THE Sistema SHALL establecer `TIME_ZONE = 'America/Guayaquil'` en `RutaExpres/settings.py`.
2. THE Sistema SHALL establecer `DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'` en `RutaExpres/settings.py`.
3. THE Sistema SHALL definir `STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')` en `RutaExpres/settings.py`.
4. THE Sistema SHALL crear un archivo `requirements.txt` en la raíz del proyecto con las dependencias necesarias, incluyendo la versión de Django instalada.

---

### Requisito 9: Pruebas Automatizadas

**Historia de Usuario:** Como desarrollador, quiero pruebas automatizadas para modelos, formularios y vistas, para que pueda detectar regresiones y verificar que el comportamiento del sistema es correcto.

#### Criterios de Aceptación

1. THE Sistema SHALL implementar pruebas de modelo en `pedido/tests.py` que verifiquen la creación correcta de instancias de `Cliente` y `Pedido`.
2. THE Sistema SHALL implementar pruebas de modelo que verifiquen que el método `__str__` de `Cliente` retorna `"{nombre} {apellido}"`.
3. THE Sistema SHALL implementar pruebas de modelo que verifiquen que el `numero_tracking` es auto-generado y único al guardar un `Pedido` sin tracking explícito.
4. THE Sistema SHALL implementar pruebas de formulario que verifiquen que `ClienteForm` rechaza emails duplicados.
5. THE Sistema SHALL implementar pruebas de formulario que verifiquen que `PedidoForm` rechaza `peso_kg` con valor cero o negativo.
6. THE Sistema SHALL implementar pruebas de vista que verifiquen que GET a `registrar_cliente` retorna HTTP 200 y usa la plantilla `registro_cliente.html`.
7. THE Sistema SHALL implementar pruebas de vista que verifiquen que GET a `rastrear_pedido` retorna HTTP 200 y usa la plantilla `rastrear_pedido.html`.
8. THE Sistema SHALL implementar pruebas de vista que verifiquen que `lista_pedidos` redirige a login cuando el usuario no es staff.
