import os

templates = {
    r"d:\Programacion\RutaExpres\pedido\templates\registration\login.html": """{% extends 'plantillaPrin.html' %}
{% load static %}
{% block page_title %}Iniciar Sesión - RutaExpres{% endblock %}

{% block contenido %}
<div class="container-xxl py-5">
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-lg-5">
                <div class="card shadow-lg border-0 rounded-lg mt-5">
                    <div class="card-header bg-primary text-white text-center py-4">
                        <h3 class="font-weight-light my-2"><i class="fas fa-truck-moving me-2"></i>RutaExpres</h3>
                        <p class="mb-0">Iniciar Sesión</p>
                    </div>
                    <div class="card-body p-5">
                        <form id="loginForm" method="POST" action="{% url 'login' %}">
                            {% csrf_token %}
                            {% if form.errors %}
                                <div class="alert alert-danger">Usuario o contraseña incorrectos.</div>
                            {% endif %}
                            <div class="form-floating mb-3">
                                {{ form.username }}
                                <label for="{{ form.username.id_for_label }}"><i class="fas fa-user text-muted me-2"></i>Usuario</label>
                            </div>
                            <div class="form-floating mb-3">
                                {{ form.password }}
                                <label for="{{ form.password.id_for_label }}"><i class="fas fa-lock text-muted me-2"></i>Contraseña</label>
                            </div>
                            <div class="d-grid gap-2 mt-4">
                                <button type="submit" class="btn btn-primary btn-lg">Entrar</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
$(document).ready(function() {
    $('input[name="username"]').addClass('form-control').attr('placeholder', 'Usuario');
    $('input[name="password"]').addClass('form-control').attr('placeholder', 'Contraseña');
    
    $('#loginForm').validate({
        rules: {
            username: { required: true },
            password: { required: true }
        },
        messages: {
            username: { required: "Por favor, ingrese su usuario." },
            password: { required: "Por favor, ingrese su contraseña." }
        },
        errorElement: 'span',
        errorPlacement: function (error, element) {
            error.addClass('invalid-feedback');
            element.closest('.form-floating').append(error);
        },
        highlight: function (element, errorClass, validClass) {
            $(element).addClass('is-invalid');
        },
        unhighlight: function (element, errorClass, validClass) {
            $(element).removeClass('is-invalid');
        }
    });
});
</script>
{% endblock %}
""",

    r"d:\Programacion\RutaExpres\pedido\templates\secretario\base_panel.html": """{% extends 'plantillaPrin.html' %}
{% load static %}
{% block contenido %}
<div class="container-fluid pt-4">
    <div class="row">
        <!-- Sidebar -->
        <div class="col-md-3 col-lg-2 mb-4">
            <div class="card bg-primary text-white shadow" style="position: sticky; top: 100px;">
                <div class="card-body p-0">
                    <div class="nav flex-column nav-pills" role="tablist" aria-orientation="vertical">
                        <a class="nav-link text-white py-3 px-4 border-bottom {% if request.resolver_match.url_name == 'dashboard_secretario' %}bg-dark{% endif %}" href="{% url 'dashboard_secretario' %}">
                            <i class="fas fa-tachometer-alt me-2"></i> Dashboard
                        </a>
                        <a class="nav-link text-white py-3 px-4 border-bottom {% if 'encomienda' in request.resolver_match.url_name and request.resolver_match.url_name != 'registrar_encomienda' %}bg-dark{% endif %}" href="{% url 'listar_encomiendas' %}">
                            <i class="fas fa-box me-2"></i> Encomiendas
                        </a>
                        <a class="nav-link text-white py-3 px-4 border-bottom {% if request.resolver_match.url_name == 'registrar_encomienda' %}bg-dark{% endif %}" href="{% url 'registrar_encomienda' %}">
                            <i class="fas fa-plus-circle me-2"></i> Nueva Encomienda
                        </a>
                        <a class="nav-link text-white py-3 px-4 border-bottom {% if 'cliente' in request.resolver_match.url_name %}bg-dark{% endif %}" href="{% url 'listar_clientes' %}">
                            <i class="fas fa-users me-2"></i> Clientes
                        </a>
                        <a class="nav-link text-white py-3 px-4 {% if 'ciudad' in request.resolver_match.url_name %}bg-dark{% endif %}" href="{% url 'listar_ciudades' %}">
                            <i class="fas fa-city me-2"></i> Ciudades
                        </a>
                    </div>
                </div>
            </div>
        </div>
        <!-- Contenido principal -->
        <div class="col-md-9 col-lg-10">
            {% block panel_contenido %}{% endblock %}
        </div>
    </div>
</div>
{% endblock %}
""",

    r"d:\Programacion\RutaExpres\pedido\templates\secretario\dashboard.html": """{% extends 'secretario/base_panel.html' %}
{% load rutaexpres_tags %}
{% block page_title %}Dashboard - RutaExpres{% endblock %}

{% block panel_contenido %}
<h2 class="mb-4">Bienvenido(a), {{ user.first_name|default:user.username }}</h2>

<div class="row mb-4">
    <div class="col-xl-3 col-md-6 mb-4">
        <div class="card border-left-primary shadow h-100 py-2" style="border-left: 4px solid #0d6efd;">
            <div class="card-body">
                <div class="row align-items-center">
                    <div class="col mr-2">
                        <div class="text-xs font-weight-bold text-primary text-uppercase mb-1">Total Encomiendas</div>
                        <div class="h5 mb-0 font-weight-bold text-dark">{{ total_encomiendas }}</div>
                    </div>
                    <div class="col-auto"><i class="fas fa-box fa-2x text-muted"></i></div>
                </div>
            </div>
        </div>
    </div>
    <div class="col-xl-3 col-md-6 mb-4">
        <div class="card border-left-success shadow h-100 py-2" style="border-left: 4px solid #198754;">
            <div class="card-body">
                <div class="row align-items-center">
                    <div class="col mr-2">
                        <div class="text-xs font-weight-bold text-success text-uppercase mb-1">Registradas Hoy</div>
                        <div class="h5 mb-0 font-weight-bold text-dark">{{ encomiendas_hoy }}</div>
                    </div>
                    <div class="col-auto"><i class="fas fa-calendar-day fa-2x text-muted"></i></div>
                </div>
            </div>
        </div>
    </div>
    <div class="col-xl-3 col-md-6 mb-4">
        <div class="card border-left-warning shadow h-100 py-2" style="border-left: 4px solid #ffc107;">
            <div class="card-body">
                <div class="row align-items-center">
                    <div class="col mr-2">
                        <div class="text-xs font-weight-bold text-warning text-uppercase mb-1">En Tránsito</div>
                        <div class="h5 mb-0 font-weight-bold text-dark">{{ en_transito }}</div>
                    </div>
                    <div class="col-auto"><i class="fas fa-truck fa-2x text-muted"></i></div>
                </div>
            </div>
        </div>
    </div>
    <div class="col-xl-3 col-md-6 mb-4">
        <div class="card border-left-info shadow h-100 py-2" style="border-left: 4px solid #0dcaf0;">
            <div class="card-body">
                <div class="row align-items-center">
                    <div class="col mr-2">
                        <div class="text-xs font-weight-bold text-info text-uppercase mb-1">Entregadas</div>
                        <div class="h5 mb-0 font-weight-bold text-dark">{{ entregadas }}</div>
                    </div>
                    <div class="col-auto"><i class="fas fa-check-circle fa-2x text-muted"></i></div>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="card shadow mb-4">
    <div class="card-header py-3 d-flex flex-row align-items-center justify-content-between bg-light">
        <h6 class="m-0 font-weight-bold text-primary">Últimas Encomiendas Registradas</h6>
        <div class="dropdown no-arrow">
            <a href="{% url 'registrar_encomienda' %}" class="btn btn-sm btn-primary shadow-sm"><i class="fas fa-plus fa-sm text-white-50"></i> Registrar</a>
            <a href="{% url 'listar_encomiendas' %}" class="btn btn-sm btn-secondary shadow-sm"><i class="fas fa-list fa-sm text-white-50"></i> Ver Todas</a>
        </div>
    </div>
    <div class="card-body">
        <div class="table-responsive">
            <table class="table table-bordered table-hover" width="100%" cellspacing="0">
                <thead class="table-light">
                    <tr>
                        <th>Guía</th>
                        <th>Cliente</th>
                        <th>Destino</th>
                        <th>Estado</th>
                        <th>Fecha</th>
                    </tr>
                </thead>
                <tbody>
                    {% for enc in ultimas_encomiendas %}
                    <tr style="cursor: pointer;" onclick="window.location='{% url 'detalle_encomienda' enc.pk %}'">
                        <td><strong>{{ enc.numero_guia }}</strong></td>
                        <td>{{ enc.cliente.usuario.get_full_name }}</td>
                        <td>{{ enc.ciudad_destino.nombre }}</td>
                        <td>{{ enc.estado|badge_estado|safe }}</td>
                        <td>{{ enc.fecha_registro|date:'d/m/Y H:i' }}</td>
                    </tr>
                    {% empty %}
                    <tr><td colspan="5" class="text-center">No hay encomiendas recientes</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
{% endblock %}
""",

    r"d:\Programacion\RutaExpres\pedido\templates\secretario\clientes_lista.html": """{% extends 'secretario/base_panel.html' %}
{% block page_title %}Listado de Clientes{% endblock %}

{% block panel_contenido %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h2 class="m-0 text-primary">Listado de Clientes</h2>
    <a href="{% url 'crear_cliente' %}" class="btn btn-primary shadow-sm"><i class="fas fa-plus"></i> Registrar Nuevo Cliente</a>
</div>

<div class="card shadow mb-4">
    <div class="card-body">
        <div class="table-responsive">
            <table class="table table-striped table-bordered" id="tablaClientes" width="100%" cellspacing="0">
                <thead class="table-dark">
                    <tr>
                        <th>#</th>
                        <th>Nombres</th>
                        <th>Apellidos</th>
                        <th>Cédula</th>
                        <th>Teléfono</th>
                        <th>Email</th>
                        <th>Acciones</th>
                    </tr>
                </thead>
                <tbody>
                    {% for cliente in clientes %}
                    <tr>
                        <td>{{ forloop.counter }}</td>
                        <td>{{ cliente.usuario.first_name }}</td>
                        <td>{{ cliente.usuario.last_name }}</td>
                        <td>{{ cliente.cedula }}</td>
                        <td>{{ cliente.telefono }}</td>
                        <td>{{ cliente.usuario.email }}</td>
                        <td>
                            <a href="{% url 'editar_cliente' cliente.pk %}" class="btn btn-sm btn-warning"><i class="fas fa-edit"></i> Editar</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
$(document).ready(function() {
    $('#tablaClientes').DataTable({
        language: { url: 'https://cdn.datatables.net/plug-ins/1.13.7/i18n/es-ES.json' }
    });
});
</script>
{% endblock %}
""",

    r"d:\Programacion\RutaExpres\pedido\templates\secretario\cliente_form.html": """{% extends 'secretario/base_panel.html' %}
{% block page_title %}{{ titulo }}{% endblock %}

{% block panel_contenido %}
<div class="card shadow mb-4">
    <div class="card-header py-3 bg-primary text-white">
        <h6 class="m-0 font-weight-bold">{{ titulo }}</h6>
    </div>
    <div class="card-body">
        <form method="POST" id="clienteForm">
            {% csrf_token %}
            <div class="row">
                {% for field in form %}
                <div class="col-md-6 mb-3">
                    <label for="{{ field.id_for_label }}" class="form-label fw-bold">{{ field.label }}</label>
                    {{ field }}
                    {% if field.errors %}
                        <div class="text-danger mt-1 small">{{ field.errors }}</div>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
            <div class="mt-4 text-center">
                <button type="submit" class="btn btn-primary btn-lg"><i class="fas fa-save"></i> Guardar</button>
                <a href="{% url 'listar_clientes' %}" class="btn btn-secondary btn-lg"><i class="fas fa-times"></i> Cancelar</a>
            </div>
        </form>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
$(document).ready(function() {
    $('input, select').addClass('form-control');
    
    $('#clienteForm').validate({
        rules: {
            username: { required: true },
            first_name: { required: true },
            last_name: { required: true },
            {% if not form.instance.pk %}password: { required: true },{% endif %}
            cedula: { required: true },
            telefono: { required: true }
        },
        errorElement: 'div',
        errorClass: 'invalid-feedback',
        highlight: function(element) { $(element).addClass('is-invalid'); },
        unhighlight: function(element) { $(element).removeClass('is-invalid'); },
        submitHandler: function(form) {
            Swal.fire({
                title: 'Guardando...',
                allowOutsideClick: false,
                didOpen: () => { Swal.showLoading(); }
            });
            form.submit();
        }
    });
    
    {% if messages %}
        {% for message in messages %}
            {% if message.tags == 'success' %}
                Swal.fire('¡Éxito!', '{{ message }}', 'success');
            {% endif %}
        {% endfor %}
    {% endif %}
});
</script>
{% endblock %}
""",

    r"d:\Programacion\RutaExpres\pedido\templates\secretario\ciudades_lista.html": """{% extends 'secretario/base_panel.html' %}
{% block page_title %}Catálogo de Ciudades{% endblock %}

{% block panel_contenido %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h2 class="m-0 text-primary">Catálogo de Ciudades</h2>
    <a href="{% url 'crear_ciudad' %}" class="btn btn-primary shadow-sm"><i class="fas fa-plus"></i> Registrar Ciudad</a>
</div>

<div class="card shadow mb-4">
    <div class="card-body">
        <div class="table-responsive">
            <table class="table table-striped table-bordered" id="tablaCiudades" width="100%">
                <thead class="table-dark">
                    <tr>
                        <th>#</th>
                        <th>Nombre</th>
                        <th>Provincia</th>
                        <th>Tarifa Base</th>
                        <th>Estado</th>
                        <th>Acciones</th>
                    </tr>
                </thead>
                <tbody>
                    {% for ciudad in ciudades %}
                    <tr>
                        <td>{{ forloop.counter }}</td>
                        <td>{{ ciudad.nombre }}</td>
                        <td>{{ ciudad.provincia }}</td>
                        <td>${{ ciudad.tarifa_base }}</td>
                        <td>
                            {% if ciudad.activa %}
                                <span class="badge bg-success">Activa</span>
                            {% else %}
                                <span class="badge bg-danger">Inactiva</span>
                            {% endif %}
                        </td>
                        <td>
                            <a href="{% url 'editar_ciudad' ciudad.pk %}" class="btn btn-sm btn-warning mb-1" title="Editar"><i class="fas fa-edit"></i></a>
                            <button onclick="toggleCiudad({{ ciudad.pk }}, '{{ ciudad.nombre }}', {{ ciudad.activa|yesno:'true,false' }})" class="btn btn-sm {% if ciudad.activa %}btn-danger{% else %}btn-success{% endif %} mb-1" title="{% if ciudad.activa %}Desactivar{% else %}Activar{% endif %}">
                                <i class="fas {% if ciudad.activa %}fa-times-circle{% else %}fa-check-circle{% endif %}"></i> 
                            </button>
                            <form id="form-toggle-{{ ciudad.pk }}" action="{% url 'toggle_ciudad' ciudad.pk %}" method="POST" style="display: none;">
                                {% csrf_token %}
                            </form>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
$(document).ready(function() {
    $('#tablaCiudades').DataTable({
        language: { url: 'https://cdn.datatables.net/plug-ins/1.13.7/i18n/es-ES.json' }
    });
});

function toggleCiudad(pk, nombre, isActiva) {
    let accion = isActiva ? 'desactivar' : 'activar';
    let btnColor = isActiva ? '#dc3545' : '#198754';
    Swal.fire({
        title: `¿Desea ${accion} la ciudad de ${nombre}?`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: btnColor,
        cancelButtonColor: '#6c757d',
        confirmButtonText: `Sí, ${accion}`,
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            document.getElementById(`form-toggle-${pk}`).submit();
        }
    });
}
</script>
{% endblock %}
""",

    r"d:\Programacion\RutaExpres\pedido\templates\secretario\ciudad_form.html": """{% extends 'secretario/base_panel.html' %}
{% block page_title %}Formulario de Ciudad{% endblock %}

{% block panel_contenido %}
<div class="card shadow mb-4" style="max-width: 600px; margin: 0 auto;">
    <div class="card-header py-3 bg-primary text-white">
        <h6 class="m-0 font-weight-bold">Datos de la Ciudad</h6>
    </div>
    <div class="card-body">
        <form method="POST" id="ciudadForm">
            {% csrf_token %}
            {% for field in form %}
            <div class="mb-3">
                <label for="{{ field.id_for_label }}" class="form-label fw-bold">{{ field.label }}</label>
                {{ field }}
                {% if field.errors %}
                    <div class="text-danger mt-1 small">{{ field.errors }}</div>
                {% endif %}
            </div>
            {% endfor %}
            <div class="mt-4 text-center">
                <button type="submit" class="btn btn-primary"><i class="fas fa-save"></i> Guardar</button>
                <a href="{% url 'listar_ciudades' %}" class="btn btn-secondary"><i class="fas fa-times"></i> Cancelar</a>
            </div>
        </form>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
$(document).ready(function() {
    $('input:not([type="checkbox"]), select').addClass('form-control');
    $('input[type="checkbox"]').addClass('form-check-input');
    
    $('#ciudadForm').validate({
        rules: {
            nombre: { required: true },
            provincia: { required: true },
            tarifa_base: { required: true, number: true, min: 0 }
        },
        errorElement: 'div',
        errorClass: 'invalid-feedback',
        highlight: function(element) { $(element).addClass('is-invalid'); },
        unhighlight: function(element) { $(element).removeClass('is-invalid'); }
    });
});
</script>
{% endblock %}
""",

    r"d:\Programacion\RutaExpres\pedido\templates\secretario\encomiendas_lista.html": """{% extends 'secretario/base_panel.html' %}
{% load rutaexpres_tags %}
{% block page_title %}Listado de Encomiendas{% endblock %}

{% block panel_contenido %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h2 class="m-0 text-primary">Listado de Encomiendas</h2>
    <a href="{% url 'registrar_encomienda' %}" class="btn btn-primary shadow-sm"><i class="fas fa-plus"></i> Registrar Encomienda</a>
</div>

<div class="card shadow mb-4">
    <div class="card-body">
        <div class="table-responsive">
            <table class="table table-striped table-bordered" id="tablaEncomiendas" width="100%">
                <thead class="table-dark">
                    <tr>
                        <th>Guía</th>
                        <th>Remitente</th>
                        <th>Destinatario</th>
                        <th>Ciudad Destino</th>
                        <th>Estado</th>
                        <th>Fecha</th>
                        <th>Acciones</th>
                    </tr>
                </thead>
                <tbody>
                    {% for encomienda in encomiendas %}
                    <tr>
                        <td><strong>{{ encomienda.numero_guia }}</strong></td>
                        <td>{{ encomienda.cliente.usuario.get_full_name }}</td>
                        <td>{{ encomienda.nombre_destinatario }}</td>
                        <td>{{ encomienda.ciudad_destino.nombre }}</td>
                        <td>{{ encomienda.estado|badge_estado|safe }}</td>
                        <td>{{ encomienda.fecha_registro|date:'d/m/Y H:i' }}</td>
                        <td>
                            <div class="btn-group" role="group">
                                <a href="{% url 'detalle_encomienda' encomienda.pk %}" class="btn btn-sm btn-info text-white" title="Ver Detalle"><i class="fas fa-eye"></i></a>
                                <a href="{% url 'cambiar_estado' encomienda.pk %}" class="btn btn-sm btn-warning" title="Cambiar Estado"><i class="fas fa-sync-alt"></i></a>
                                <a href="{% url 'comprobante_encomienda' encomienda.pk %}" class="btn btn-sm btn-secondary" title="Comprobante"><i class="fas fa-receipt"></i></a>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
$(document).ready(function() {
    $('#tablaEncomiendas').DataTable({
        language: { url: 'https://cdn.datatables.net/plug-ins/1.13.7/i18n/es-ES.json' },
        order: [[5, 'desc']]
    });
});
</script>
{% endblock %}
""",

    r"d:\Programacion\RutaExpres\pedido\templates\secretario\encomienda_form.html": """{% extends 'secretario/base_panel.html' %}
{% block page_title %}Registrar Nueva Encomienda{% endblock %}

{% block panel_contenido %}
<h2 class="mb-4 text-primary">Registrar Nueva Encomienda</h2>

<form method="POST" id="encomiendaForm">
    {% csrf_token %}
    <div class="row">
        <!-- Remitente -->
        <div class="col-md-6 mb-4">
            <div class="card shadow h-100">
                <div class="card-header bg-primary text-white"><i class="fas fa-user me-2"></i>Datos del Remitente</div>
                <div class="card-body">
                    <div class="mb-3">
                        <label class="form-label fw-bold">{{ form.cliente.label }}</label>
                        {{ form.cliente }}
                        {% if form.cliente.errors %}<div class="text-danger small">{{ form.cliente.errors }}</div>{% endif %}
                    </div>
                </div>
            </div>
        </div>
        <!-- Destinatario -->
        <div class="col-md-6 mb-4">
            <div class="card shadow h-100">
                <div class="card-header bg-secondary text-white"><i class="fas fa-user-tag me-2"></i>Datos del Destinatario</div>
                <div class="card-body">
                    <div class="mb-3">
                        <label class="form-label fw-bold">{{ form.nombre_destinatario.label }}</label>
                        {{ form.nombre_destinatario }}
                        {% if form.nombre_destinatario.errors %}<div class="text-danger small">{{ form.nombre_destinatario.errors }}</div>{% endif %}
                    </div>
                    <div class="mb-3">
                        <label class="form-label fw-bold">{{ form.telefono_destinatario.label }}</label>
                        {{ form.telefono_destinatario }}
                        {% if form.telefono_destinatario.errors %}<div class="text-danger small">{{ form.telefono_destinatario.errors }}</div>{% endif %}
                    </div>
                    <div class="mb-3">
                        <label class="form-label fw-bold">{{ form.direccion_entrega.label }}</label>
                        {{ form.direccion_entrega }}
                        {% if form.direccion_entrega.errors %}<div class="text-danger small">{{ form.direccion_entrega.errors }}</div>{% endif %}
                    </div>
                </div>
            </div>
        </div>
        <!-- Paquete -->
        <div class="col-md-6 mb-4">
            <div class="card shadow h-100">
                <div class="card-header bg-dark text-white"><i class="fas fa-box me-2"></i>Datos del Paquete</div>
                <div class="card-body">
                    <div class="mb-3">
                        <label class="form-label fw-bold">{{ form.descripcion_paquete.label }}</label>
                        {{ form.descripcion_paquete }}
                        {% if form.descripcion_paquete.errors %}<div class="text-danger small">{{ form.descripcion_paquete.errors }}</div>{% endif %}
                    </div>
                    <div class="row">
                        <div class="col-6 mb-3">
                            <label class="form-label fw-bold">{{ form.peso.label }} (kg)</label>
                            {{ form.peso }}
                        </div>
                        <div class="col-6 mb-3">
                            <label class="form-label fw-bold">{{ form.valor_declarado.label }} ($)</label>
                            {{ form.valor_declarado }}
                        </div>
                    </div>
                    <div class="mb-3">
                        <label class="form-label fw-bold">{{ form.ciudad_destino.label }}</label>
                        {{ form.ciudad_destino }}
                        {% if form.ciudad_destino.errors %}<div class="text-danger small">{{ form.ciudad_destino.errors }}</div>{% endif %}
                    </div>
                    <div class="alert alert-info py-2" id="tarifaInfo" style="display:none;">
                        Tarifa Base Estimada: $<span id="tarifaMonto">0.00</span>
                    </div>
                </div>
            </div>
        </div>
        <!-- Info Adicional -->
        <div class="col-md-6 mb-4">
            <div class="card shadow h-100">
                <div class="card-header bg-info text-white"><i class="fas fa-info-circle me-2"></i>Información Adicional</div>
                <div class="card-body">
                    <div class="mb-3">
                        <label class="form-label fw-bold">{{ form.observaciones.label }}</label>
                        {{ form.observaciones }}
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="text-center mb-5">
        <button type="submit" class="btn btn-primary btn-lg px-5 shadow"><i class="fas fa-check-circle"></i> Registrar Encomienda</button>
        <a href="{% url 'listar_encomiendas' %}" class="btn btn-secondary btn-lg shadow">Cancelar</a>
    </div>
</form>
{% endblock %}

{% block extra_js %}
<script>
$(document).ready(function() {
    $('input, select, textarea').addClass('form-control');
    
    // Add data-tarifa to options
    {% for ciudad in ciudades %}
    $('#id_ciudad_destino option[value="{{ ciudad.pk }}"]').attr('data-tarifa', '{{ ciudad.tarifa_base }}');
    {% endfor %}
    
    $('#id_ciudad_destino').change(function() {
        let tarifa = $(this).find(':selected').data('tarifa');
        if (tarifa) {
            $('#tarifaMonto').text(tarifa);
            $('#tarifaInfo').slideDown();
        } else {
            $('#tarifaInfo').slideUp();
        }
    }).trigger('change');

    $('#encomiendaForm').validate({
        rules: {
            cliente: { required: true },
            ciudad_destino: { required: true },
            nombre_destinatario: { required: true },
            telefono_destinatario: { required: true },
            direccion_entrega: { required: true },
            descripcion_paquete: { required: true }
        },
        errorElement: 'div',
        errorClass: 'invalid-feedback',
        highlight: function(element) { $(element).addClass('is-invalid'); },
        unhighlight: function(element) { $(element).removeClass('is-invalid'); },
        submitHandler: function(form) {
            Swal.fire({
                title: '¿Confirmar Registro?',
                text: "Revise que los datos sean correctos",
                icon: 'question',
                showCancelButton: true,
                confirmButtonColor: '#3085d6',
                cancelButtonColor: '#d33',
                confirmButtonText: 'Sí, registrar',
                cancelButtonText: 'Cancelar'
            }).then((result) => {
                if (result.isConfirmed) {
                    Swal.fire({
                        title: 'Guardando...',
                        allowOutsideClick: false,
                        didOpen: () => { Swal.showLoading(); }
                    });
                    form.submit();
                }
            });
        }
    });
});
</script>
{% endblock %}
""",

    r"d:\Programacion\RutaExpres\pedido\templates\secretario\encomienda_detalle.html": """{% extends 'secretario/base_panel.html' %}
{% load rutaexpres_tags %}
{% block page_title %}Detalle - Guía {{ encomienda.numero_guia }}{% endblock %}

{% block panel_contenido %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <div>
        <h2 class="text-primary m-0">Guía: {{ encomienda.numero_guia }}</h2>
        <div class="mt-2">{{ encomienda.estado|badge_estado|safe }}</div>
    </div>
    <div>
        <a href="{% url 'cambiar_estado' encomienda.pk %}" class="btn btn-warning shadow-sm"><i class="fas fa-sync-alt"></i> Cambiar Estado</a>
        <a href="{% url 'comprobante_encomienda' encomienda.pk %}" class="btn btn-secondary shadow-sm"><i class="fas fa-receipt"></i> Comprobante</a>
        <a href="{% url 'descargar_comprobante_pdf' encomienda.pk %}" class="btn btn-danger shadow-sm"><i class="fas fa-file-pdf"></i> PDF</a>
    </div>
</div>

<div class="row">
    <!-- Detalles de Envío -->
    <div class="col-md-7 mb-4">
        <div class="card shadow">
            <div class="card-header bg-primary text-white"><i class="fas fa-info-circle"></i> Datos del Envío</div>
            <div class="card-body">
                <h5 class="border-bottom pb-2 text-primary">Remitente</h5>
                <p class="mb-1"><strong>Nombre:</strong> {{ encomienda.cliente.usuario.get_full_name }}</p>
                <p class="mb-1"><strong>Teléfono:</strong> {{ encomienda.cliente.telefono }}</p>
                <p class="mb-1"><strong>Cédula:</strong> {{ encomienda.cliente.cedula }}</p>
                
                <h5 class="border-bottom pb-2 mt-4 text-secondary">Destinatario</h5>
                <p class="mb-1"><strong>Nombre:</strong> {{ encomienda.nombre_destinatario }}</p>
                <p class="mb-1"><strong>Teléfono:</strong> {{ encomienda.telefono_destinatario }}</p>
                <p class="mb-1"><strong>Dirección:</strong> {{ encomienda.direccion_entrega }}</p>
                <p class="mb-1"><strong>Ciudad:</strong> {{ encomienda.ciudad_destino.nombre }}</p>

                <h5 class="border-bottom pb-2 mt-4 text-dark">Paquete y Costos</h5>
                <p class="mb-1"><strong>Descripción:</strong> {{ encomienda.descripcion_paquete }}</p>
                <p class="mb-1"><strong>Peso:</strong> {{ encomienda.peso|default:'-' }} kg</p>
                <p class="mb-1"><strong>Valor Declarado:</strong> ${{ encomienda.valor_declarado|default:'0.00' }}</p>
                <div class="alert alert-success mt-3 py-2 text-end">
                    <h5 class="mb-0">Costo Envío: <strong>${{ encomienda.costo_envio }}</strong></h5>
                </div>
            </div>
        </div>
    </div>

    <!-- Línea de Tiempo -->
    <div class="col-md-5 mb-4">
        <div class="card shadow">
            <div class="card-header bg-dark text-white"><i class="fas fa-history"></i> Historial de Estados</div>
            <div class="card-body p-0" style="max-height: 600px; overflow-y: auto;">
                <ul class="list-group list-group-flush">
                    {% for h in historial %}
                    <li class="list-group-item p-3">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <strong>{{ h.estado|badge_estado|safe }}</strong>
                            <small class="text-muted"><i class="far fa-clock"></i> {{ h.fecha|date:'d/m/Y H:i' }}</small>
                        </div>
                        {% if h.comentario %}<p class="mb-1 small">{{ h.comentario }}</p>{% endif %}
                        <div class="small text-muted mt-2"><i class="fas fa-user-edit"></i> Por: {{ h.usuario.get_full_name }}</div>
                    </li>
                    {% empty %}
                    <li class="list-group-item">No hay historial de estados.</li>
                    {% endfor %}
                </ul>
            </div>
        </div>
    </div>
</div>
{% endblock %}
""",

    r"d:\Programacion\RutaExpres\pedido\templates\secretario\comprobante.html": """{% if is_pdf %}
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Comprobante {{ encomienda.numero_guia }}</title>
<style>
  body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 13px; color: #333; margin: 0; padding: 0; }
  .comprobante { max-width: 800px; margin: 0 auto; padding: 20px; }
  .header { border-bottom: 3px solid #06A3DA; padding-bottom: 15px; margin-bottom: 20px; }
  .guia-code { font-size: 26px; font-weight: bold; color: #06A3DA; text-align: center; padding: 15px; border: 2px dashed #06A3DA; margin: 20px 0; border-radius: 10px; background-color: #f8f9fa; }
  table { width: 100%; border-collapse: collapse; margin-bottom: 25px; }
  td, th { padding: 10px; border: 1px solid #dee2e6; text-align: left; }
  th { background-color: #f8f9fa; }
  .row { display: table; width: 100%; margin-bottom: 20px; }
  .col-6 { display: table-cell; width: 50%; vertical-align: top; }
  .card { border: 1px solid #dee2e6; border-radius: 5px; margin-bottom: 20px; }
  .card-header { padding: 10px; font-weight: bold; color: white; background-color: #06A3DA; }
  .card-header.bg-secondary { background-color: #6c757d; }
  .card-body { padding: 15px; }
  .text-center { text-align: center; }
  .text-end { text-align: right; }
  .mb-0 { margin-bottom: 0; }
</style>
</head><body>
{% else %}
{% extends 'plantillaPrin.html' %}
{% load static %}
{% load rutaexpres_tags %}
{% block page_title %}Comprobante {{ encomienda.numero_guia }}{% endblock %}
{% block contenido %}
{% endif %}

<div class="container{% if not is_pdf %} py-5{% endif %}">
  <div class="comprobante bg-white shadow-lg p-4 p-md-5" style="max-width: 800px; margin: 0 auto; border-radius: 10px;">
    
    <!-- Header -->
    <div class="header row align-items-center">
      <div class="col-6">
        <h2 style="color: #06A3DA; margin:0; font-size: 28px;">RutaExpres</h2>
        <p style="color: #6c757d; margin:0; font-size: 16px;">Servicio de Encomiendas</p>
        <small style="display:block; margin-top:10px;">Dirección: Av. Principal s/n<br>Tel: (02) 123-4567<br>Email: info@rutaexpres.com</small>
      </div>
      <div class="col-6 text-end">
        <h4 style="margin:0; font-size: 20px;">COMPROBANTE DE ENVÍO</h4>
        <p style="margin-top:5px;"><strong>Fecha:</strong> {{ encomienda.fecha_registro|date:'d/m/Y H:i' }}</p>
      </div>
    </div>

    <!-- TRACKING CODE -->
    <div class="guia-code">
      <small style="color:#6c757d; display:block; font-size: 14px; font-weight: normal;">NÚMERO DE GUÍA / CÓDIGO DE RASTREO</small>
      <div style="font-size: 34px; margin-top: 5px;">{{ encomienda.numero_guia }}</div>
    </div>

    <!-- Sender & Recipient -->
    <div class="row">
      <div class="col-6" style="padding-right: 15px;">
        <div class="card">
          <div class="card-header bg-primary"><i class="fas fa-user"></i> REMITENTE</div>
          <div class="card-body">
            <p class="mb-1"><strong>Nombre:</strong> {{ encomienda.cliente.usuario.get_full_name }}</p>
            <p class="mb-1"><strong>Teléfono:</strong> {{ encomienda.cliente.telefono }}</p>
            <p class="mb-0"><strong>Cédula:</strong> {{ encomienda.cliente.cedula }}</p>
          </div>
        </div>
      </div>
      <div class="col-6" style="padding-left: 15px;">
        <div class="card">
          <div class="card-header bg-secondary"><i class="fas fa-map-marker-alt"></i> DESTINATARIO</div>
          <div class="card-body">
            <p class="mb-1"><strong>Nombre:</strong> {{ encomienda.nombre_destinatario }}</p>
            <p class="mb-1"><strong>Teléfono:</strong> {{ encomienda.telefono_destinatario }}</p>
            <p class="mb-1"><strong>Dirección:</strong> {{ encomienda.direccion_entrega }}</p>
            <p class="mb-0"><strong>Ciudad:</strong> {{ encomienda.ciudad_destino.nombre }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Package Details -->
    <table class="table">
      <tr style="background:#343a40; color:white;"><th colspan="2"><i class="fas fa-box"></i> DETALLE DEL PAQUETE</th></tr>
      <tr><th style="width: 30%;">Descripción</th><td>{{ encomienda.descripcion_paquete }}</td></tr>
      <tr><th>Peso</th><td>{{ encomienda.peso|default:'No especificado' }} kg</td></tr>
      <tr><th>Valor Declarado</th><td>${{ encomienda.valor_declarado|default:'0.00' }}</td></tr>
    </table>

    <!-- Costs -->
    <table class="table">
      <tr style="background:#198754; color:white;"><th colspan="2"><i class="fas fa-dollar-sign"></i> DETALLE DE COSTOS</th></tr>
      <tr><td>Tarifa Base ({{ encomienda.ciudad_destino.nombre }})</td><td class="text-end" style="width: 30%;"><strong>${{ encomienda.costo_envio }}</strong></td></tr>
      <tr style="background:#d1e7dd; font-size: 18px;"><td><strong>TOTAL A PAGAR</strong></td><td class="text-end"><strong>${{ encomienda.costo_envio }}</strong></td></tr>
    </table>

    <div style="background:#cff4fc; color: #055160; padding: 15px; border-radius: 5px; margin-bottom: 40px; border: 1px solid #b6effb;">
      <strong><i class="fas fa-info-circle"></i> Consulte el estado de su envío en cualquier momento:</strong><br>
      Ingrese a <strong>www.rutaexpres.com/rastreo/</strong> y escriba su código de rastreo: <strong>{{ encomienda.numero_guia }}</strong>
    </div>

    <!-- Signatures -->
    <div class="row text-center" style="margin-top: 70px;">
      <div class="col-6">
        <div style="border-top: 1px solid #000; width: 80%; margin: 0 auto; padding-top: 10px;">
          Firma del Remitente
        </div>
      </div>
      <div class="col-6">
        <div style="border-top: 1px solid #000; width: 80%; margin: 0 auto; padding-top: 10px;">
          Firma del Secretario<br>
          <small style="color:#6c757d;">{{ encomienda.secretario_registro.get_full_name }}</small>
        </div>
      </div>
    </div>

    {% if not is_pdf %}
    <!-- Action Buttons -->
    <div class="text-center mt-5 no-print border-top pt-4">
      <a href="{% url 'descargar_comprobante_pdf' encomienda.pk %}" class="btn btn-danger btn-lg me-2 shadow">
        <i class="fas fa-file-pdf"></i> Descargar PDF
      </a>
      <button onclick="enviarEmail({{ encomienda.pk }})" class="btn btn-primary btn-lg me-2 shadow">
        <i class="fas fa-envelope"></i> Enviar por Email
      </button>
      <button onclick="window.print()" class="btn btn-secondary btn-lg shadow">
        <i class="fas fa-print"></i> Imprimir
      </button>
      <a href="{% url 'detalle_encomienda' encomienda.pk %}" class="btn btn-outline-dark btn-lg ms-2">Volver</a>
    </div>
    {% endif %}

  </div>
</div>

{% if is_pdf %}
</body></html>
{% else %}
{% endblock %}
{% block extra_css %}
<style>
@media print {
    .no-print, .navbar, .footer, .back-to-top, #spinner { display: none !important; }
    .comprobante { box-shadow: none !important; margin-top: 0 !important; }
    body { background-color: white !important; }
}
</style>
{% endblock %}
{% block extra_js %}
<script>
function enviarEmail(pk) {
    Swal.fire({
        title: '¿Enviar comprobante por email?',
        text: 'Se enviará el comprobante en PDF al correo del cliente',
        icon: 'question',
        showCancelButton: true,
        confirmButtonText: 'Sí, enviar',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            Swal.fire({
                title: 'Enviando correo...',
                allowOutsideClick: false,
                didOpen: () => { Swal.showLoading(); }
            });
            fetch(`/secretario/encomiendas/${pk}/comprobante/email/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': '{{ csrf_token }}',
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if(data.success) {
                    Swal.fire('¡Enviado!', data.message, 'success');
                } else {
                    Swal.fire('Error', data.message || 'Error al enviar correo', 'error');
                }
            }).catch(e => {
                Swal.fire('Error', 'No se pudo conectar con el servidor', 'error');
            });
        }
    });
}
</script>
{% endblock %}
{% endif %}
""",

    r"d:\Programacion\RutaExpres\pedido\templates\secretario\cambio_estado.html": """{% extends 'secretario/base_panel.html' %}
{% load rutaexpres_tags %}
{% block page_title %}Cambiar Estado{% endblock %}

{% block panel_contenido %}
<div class="card shadow mb-4" style="max-width: 600px; margin: 0 auto;">
    <div class="card-header py-3 bg-warning text-dark">
        <h6 class="m-0 font-weight-bold"><i class="fas fa-sync-alt"></i> Cambiar Estado - Guía {{ encomienda.numero_guia }}</h6>
    </div>
    <div class="card-body">
        <div class="text-center mb-4">
            <h5 class="text-muted">Estado Actual</h5>
            <div class="h3">{{ encomienda.estado|badge_estado|safe }}</div>
            <i class="fas fa-arrow-down fa-2x text-muted my-3"></i>
            <h5 class="text-muted">Nuevo Estado</h5>
        </div>
        
        <form method="POST" id="estadoForm">
            {% csrf_token %}
            <div class="mb-3">
                <label class="form-label fw-bold">{{ form.nuevo_estado.label }}</label>
                {{ form.nuevo_estado }}
                {% if form.nuevo_estado.errors %}<div class="text-danger small">{{ form.nuevo_estado.errors }}</div>{% endif %}
            </div>
            
            {% if form.despachador %}
            <div class="mb-3" id="despachadorDiv" style="display:none;">
                <label class="form-label fw-bold">{{ form.despachador.label }}</label>
                {{ form.despachador }}
                {% if form.despachador.errors %}<div class="text-danger small">{{ form.despachador.errors }}</div>{% endif %}
            </div>
            {% endif %}
            
            <div class="mb-4">
                <label class="form-label fw-bold">{{ form.comentario.label }}</label>
                {{ form.comentario }}
                {% if form.comentario.errors %}<div class="text-danger small">{{ form.comentario.errors }}</div>{% endif %}
            </div>
            
            <div class="text-center">
                <button type="submit" class="btn btn-warning btn-lg shadow"><i class="fas fa-save"></i> Actualizar Estado</button>
                <a href="{% url 'detalle_encomienda' encomienda.pk %}" class="btn btn-secondary btn-lg shadow"><i class="fas fa-times"></i> Cancelar</a>
            </div>
        </form>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
$(document).ready(function() {
    $('select, textarea').addClass('form-control');
    
    // Si hay campo despachador, mostrarlo si el estado es 'EN_TRANSITO'
    $('#id_nuevo_estado').change(function() {
        if($(this).val() === 'EN_TRANSITO') {
            $('#despachadorDiv').slideDown();
        } else {
            $('#despachadorDiv').slideUp();
        }
    }).trigger('change');

    $('#estadoForm').on('submit', function(e) {
        e.preventDefault();
        Swal.fire({
            title: '¿Actualizar estado?',
            text: "Se registrará este cambio en el historial.",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#ffc107',
            cancelButtonColor: '#6c757d',
            confirmButtonText: 'Sí, actualizar',
            cancelButtonText: 'Cancelar'
        }).then((result) => {
            if (result.isConfirmed) {
                Swal.fire({
                    title: 'Guardando...',
                    allowOutsideClick: false,
                    didOpen: () => { Swal.showLoading(); }
                });
                this.submit();
            }
        });
    });
});
</script>
{% endblock %}
"""
}

for k, v in templates.items():
    os.makedirs(os.path.dirname(k), exist_ok=True)
    with open(k, "w", encoding="utf-8") as f:
        f.write(v)

print("Plantillas creadas con éxito.")
