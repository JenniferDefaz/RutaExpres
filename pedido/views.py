from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse
from django.db.models import Sum, Count
import json

from .models import Cliente, Pedido
from .forms import ClienteForm, PedidoForm, BuscarPedidoForm


def _get_or_create_group(name):
    """Obtiene o crea un grupo de usuarios por nombre."""
    group, _ = Group.objects.get_or_create(name=name)
    return group


def _enviar_bienvenida(cliente):
    """Correo #1 — Bienvenida al cliente registrado."""
    try:
        send_mail(
            subject='¡Bienvenido a RutaExpres - Centro de Soluciones!',
            message=(
                f'Hola {cliente.nombre} {cliente.apellido},\n\n'
                f'¡Gracias por registrarte en RutaExpres - Centro de Soluciones!\n\n'
                f'Tu cuenta ha sido creada exitosamente con el correo: {cliente.email}\n\n'
                f'Ya puedes iniciar sesión y registrar tus envíos desde nuestra plataforma.\n\n'
                f'Si tienes alguna consulta, no dudes en contactarnos.\n\n'
                f'Saludos,\n'
                f'El equipo de RutaExpres\n'
                f'Tel: +593 2 345 6789 | info@rutaexpres.com.ec'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[cliente.email],
            fail_silently=True,
        )
    except Exception:
        pass


def _enviar_confirmacion_pedido(pedido):
    """Correo #2 — Confirmación al crear un pedido con todos sus datos."""
    try:
        precio_texto = f'${pedido.precio_envio}' if pedido.precio_envio else 'Por calcular'
        send_mail(
            subject=f'[RutaExpres] Pedido registrado — Tracking: {pedido.numero_tracking}',
            message=(
                f'Hola {pedido.cliente.nombre} {pedido.cliente.apellido},\n\n'
                f'Tu pedido ha sido registrado exitosamente en RutaExpres.\n\n'
                f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
                f'  DETALLES DEL PEDIDO\n'
                f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
                f'  Tracking        : {pedido.numero_tracking}\n'
                f'  Destinatario    : {pedido.destinatario}\n'
                f'  Tipo de servicio: {pedido.get_tipo_servicio_display()}\n'
                f'  Origen          : {pedido.origen}\n'
                f'  Destino         : {pedido.destino}\n'
                f'  Peso            : {pedido.peso_kg} kg\n'
                f'  Precio estimado : {precio_texto}\n'
                f'  Estado          : {pedido.get_estado_display()}\n'
                f'  Fecha           : {pedido.fecha_creacion.strftime("%d/%m/%Y %H:%M")}\n'
                f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n'
                f'Puedes rastrear tu envío en cualquier momento con el\n'
                f'número de tracking en nuestra página web.\n\n'
                f'Contáctanos:\n'
                f'  Tel  : +593 2 345 6789\n'
                f'  Email: info@rutaexpres.com.ec\n\n'
                f'Saludos,\n'
                f'El equipo de RutaExpres'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[pedido.cliente.email],
            fail_silently=True,
        )
    except Exception:
        pass


def _enviar_notificacion_entrega(pedido):
    """Correo #3 — Notificación cuando el pedido es entregado."""
    try:
        send_mail(
            subject=f'[RutaExpres] ¡Tu pedido {pedido.numero_tracking} fue entregado!',
            message=(
                f'Hola {pedido.cliente.nombre} {pedido.cliente.apellido},\n\n'
                f'Nos complace informarte que tu pedido fue entregado exitosamente.\n\n'
                f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
                f'  CONFIRMACIÓN DE ENTREGA\n'
                f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
                f'  Tracking     : {pedido.numero_tracking}\n'
                f'  Destinatario : {pedido.destinatario}\n'
                f'  Destino      : {pedido.destino}\n'
                f'  Entregado el : {pedido.fecha_actualizacion.strftime("%d/%m/%Y %H:%M")}\n'
                f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n'
                f'Gracias por confiar en RutaExpres para tus envíos.\n\n'
                f'Contáctanos:\n'
                f'  Tel  : +593 2 345 6789\n'
                f'  Email: info@rutaexpres.com.ec\n\n'
                f'Saludos,\n'
                f'El equipo de RutaExpres'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[pedido.cliente.email],
            fail_silently=True,
        )
    except Exception:
        pass


def inicio(request):
    """Vista de la página principal."""
    return render(request, 'inicio.html')


@login_required(login_url='iniciar_sesion')
def dashboard(request):
    """
    Dashboard personalizado por rol:
    - Secretario/staff: estadísticas globales + gráficos
    - Despachador: resumen de sus pedidos asignados
    - Cliente: resumen de sus propios pedidos
    """
    es_secretario = (
        request.user.is_staff
        or request.user.groups.filter(name='Secretario').exists()
    )
    es_despachador = request.user.groups.filter(name='Despachador').exists()

    # ── Secretario ──────────────────────────────────────────
    if es_secretario:
        pedidos = Pedido.objects.select_related('cliente').all()
        total = pedidos.count()
        pendientes = pedidos.filter(estado='pendiente').count()
        en_transito = pedidos.filter(estado='en_transito').count()
        entregados = pedidos.filter(estado='entregado').count()
        cancelados = pedidos.filter(estado='cancelado').count()
        ingresos = pedidos.exclude(precio_envio__isnull=True).aggregate(
            total=Sum('precio_envio')
        )['total'] or 0
        total_clientes = Cliente.objects.count()

        # Datos para gráfico: distribución por estado
        etiquetas_estado = ['Pendiente', 'En Tránsito', 'Entregado', 'Cancelado']
        datos_estado = [pendientes, en_transito, entregados, cancelados]

        # Datos para gráfico: distribución por tipo de servicio
        servicios = pedidos.values('tipo_servicio').annotate(total=Count('id'))
        etiquetas_servicio = [s['tipo_servicio'].capitalize() for s in servicios]
        datos_servicio = [s['total'] for s in servicios]

        # Últimos 5 pedidos recientes
        pedidos_recientes = pedidos.order_by('-fecha_creacion')[:5]

        # Despachadores disponibles
        grupo_d = Group.objects.filter(name='Despachador').first()
        despachadores = grupo_d.user_set.all() if grupo_d else []

        return render(request, 'dashboard_secretario.html', {
            'total': total,
            'pendientes': pendientes,
            'en_transito': en_transito,
            'entregados': entregados,
            'cancelados': cancelados,
            'ingresos': ingresos,
            'total_clientes': total_clientes,
            'pedidos_recientes': pedidos_recientes,
            'etiquetas_estado_json': json.dumps(etiquetas_estado),
            'datos_estado_json': json.dumps(datos_estado),
            'etiquetas_servicio_json': json.dumps(etiquetas_servicio),
            'datos_servicio_json': json.dumps(datos_servicio),
            'despachadores': despachadores,
        })

    # ── Despachador ─────────────────────────────────────────
    elif es_despachador:
        pedidos = Pedido.objects.select_related('cliente').filter(despachador=request.user)
        total = pedidos.count()
        pendientes = pedidos.filter(estado='pendiente').count()
        en_transito = pedidos.filter(estado='en_transito').count()
        entregados = pedidos.filter(estado='entregado').count()
        cancelados = pedidos.filter(estado='cancelado').count()

        etiquetas_estado = ['Pendiente', 'En Tránsito', 'Entregado', 'Cancelado']
        datos_estado = [pendientes, en_transito, entregados, cancelados]
        pedidos_recientes = pedidos.order_by('-fecha_creacion')[:5]

        return render(request, 'dashboard_despachador.html', {
            'total': total,
            'pendientes': pendientes,
            'en_transito': en_transito,
            'entregados': entregados,
            'cancelados': cancelados,
            'pedidos_recientes': pedidos_recientes,
            'etiquetas_estado_json': json.dumps(etiquetas_estado),
            'datos_estado_json': json.dumps(datos_estado),
        })

    # ── Cliente ──────────────────────────────────────────────
    else:
        if not hasattr(request.user, 'cliente'):
            messages.error(request, 'No tienes un perfil de cliente asociado.')
            return redirect('inicio')

        pedidos = request.user.cliente.pedidos.all()
        total = pedidos.count()
        pendientes = pedidos.filter(estado='pendiente').count()
        en_transito = pedidos.filter(estado='en_transito').count()
        entregados = pedidos.filter(estado='entregado').count()
        cancelados = pedidos.filter(estado='cancelado').count()
        pedidos_recientes = pedidos.order_by('-fecha_creacion')[:5]

        return render(request, 'dashboard_cliente.html', {
            'total': total,
            'pendientes': pendientes,
            'en_transito': en_transito,
            'entregados': entregados,
            'cancelados': cancelados,
            'pedidos': pedidos,
            'pedidos_recientes': pedidos_recientes,
        })


def registrar_cliente(request):
    """
    Vista para registrar un nuevo cliente.
    GET  → muestra el formulario vacío.
    POST → valida, crea el usuario y cliente, envía bienvenida, redirige al login.
    """
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save(commit=False)
            password = form.cleaned_data['password']
            username = cliente.email

            if User.objects.filter(username=username).exists():
                messages.error(request, 'Ya existe una cuenta registrada con ese correo electrónico.')
                return render(request, 'registro_cliente.html', {'form': form})

            # Crear el usuario con la contraseña ya hasheada por create_user
            user = User.objects.create_user(
                username=username,
                email=cliente.email,
                password=password,
                first_name=cliente.nombre,
                last_name=cliente.apellido,
            )
            # Asignar al grupo Cliente (lo crea si no existe)
            grupo_cliente = _get_or_create_group('Cliente')
            user.groups.add(grupo_cliente)

            cliente.user = user
            cliente.save()

            # Correo de bienvenida
            _enviar_bienvenida(cliente)

            messages.success(
                request,
                f'¡Registro exitoso! Bienvenido {cliente.nombre}. '
                f'Te enviamos un correo de bienvenida a {cliente.email}. '
                f'Ya puedes iniciar sesión.'
            )
            # Redirigir al login para que el cliente inicie sesión
            return redirect('iniciar_sesion')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        form = ClienteForm()

    return render(request, 'registro_cliente.html', {'form': form})


@login_required(login_url='iniciar_sesion')
def registrar_pedido(request):
    if request.method == 'POST':
        form = PedidoForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            pedido = form.save(commit=False)
            es_rol_interno = (
                request.user.groups.filter(name__in=['Secretario', 'Despachador']).exists()
                or request.user.is_staff
            )
            if not es_rol_interno and hasattr(request.user, 'cliente'):
                pedido.cliente = request.user.cliente
                pedido.estado = 'pendiente'

            # Cotización automática: peso × tarifa
            tarifa = getattr(settings, 'TARIFA_POR_KG', 2.50)
            pedido.precio_envio = round(float(pedido.peso_kg) * float(tarifa), 2)

            pedido.save()
            _enviar_confirmacion_pedido(pedido)
            messages.success(
                request,
                f'Pedido registrado. Tracking: {pedido.numero_tracking}. '
                f'Precio estimado: ${pedido.precio_envio}. '
                f'Confirmación enviada a {pedido.cliente.email}.'
            )
            return redirect('detalle_pedido', tracking=pedido.numero_tracking)
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        form = PedidoForm(user=request.user)
    return render(request, 'registro_pedido.html', {
        'form': form,
        'tarifa_por_kg': getattr(settings, 'TARIFA_POR_KG', 2.50),
    })


def rastrear_pedido(request):
    """
    Vista para rastrear un pedido por número de tracking.
    GET  → muestra el formulario de búsqueda.
    POST → busca y muestra el resultado, o error si no se encuentra.
    """
    form = BuscarPedidoForm(request.POST or None)
    pedido = None

    if request.method == 'POST' and form.is_valid():
        tracking = form.cleaned_data['numero_tracking']
        try:
            pedido = Pedido.objects.select_related('cliente').get(
                numero_tracking=tracking
            )
        except Pedido.DoesNotExist:
            messages.error(
                request,
                f'No se encontró ningún pedido con el número de tracking: {tracking}'
            )

    return render(request, 'rastrear_pedido.html', {
        'form': form,
        'pedido': pedido,
    })


def detalle_pedido(request, tracking):
    pedido = get_object_or_404(
        Pedido.objects.select_related('cliente'),
        numero_tracking=tracking
    )
    # Confidencialidad: cliente solo ve sus propios pedidos
    if request.user.is_authenticated:
        es_rol_interno = (
            request.user.groups.filter(name__in=['Secretario', 'Despachador']).exists()
            or request.user.is_staff
        )
        if not es_rol_interno and hasattr(request.user, 'cliente'):
            if pedido.cliente != request.user.cliente:
                messages.error(request, 'No tienes permiso para ver este pedido.')
                return redirect('panel_cliente')
    return render(request, 'detalle_pedido.html', {'pedido': pedido})


@login_required(login_url='iniciar_sesion')
def lista_pedidos(request):
    es_secretario = request.user.groups.filter(name='Secretario').exists() or request.user.is_staff
    es_despachador = request.user.groups.filter(name='Despachador').exists()
    es_rol_interno = es_secretario or es_despachador

    if not es_rol_interno:
        messages.error(request, 'No tienes permisos para acceder al Panel.')
        return redirect('panel_cliente')

    if request.method == 'POST':
        pedido_id = request.POST.get('pedido_id')
        nuevo_estado = request.POST.get('nuevo_estado')
        confirmar_pago = request.POST.get('confirmar_pago')
        estados_validos = [e[0] for e in Pedido.ESTADO_CHOICES]
        estados_despachador = ['en_transito', 'entregado']

        if pedido_id:
            try:
                pedido = Pedido.objects.select_related('cliente').get(pk=pedido_id)

                # Secretario SOLO puede asignar despachador (manejado en asignar_despachador)
                # Despachador puede cambiar estado y confirmar pago de SUS pedidos asignados
                if es_despachador and pedido.despachador != request.user:
                    messages.error(request, 'No tienes permiso para modificar este pedido.')
                elif es_secretario and not es_despachador:
                    # Secretario puro: no puede cambiar estado ni confirmar pago
                    messages.error(request, 'El secretario solo puede asignar despachadores. El cambio de estado y pago lo gestiona el despachador.')
                elif confirmar_pago and es_despachador:
                    if pedido.despachador != request.user:
                        messages.error(request, 'No tienes permiso para confirmar el pago de este pedido.')
                    else:
                        pedido.pago_confirmado = True
                        pedido.save()
                        messages.success(request, f'Pago confirmado para el pedido {pedido.numero_tracking}.')
                elif nuevo_estado in estados_validos and es_despachador:
                    if nuevo_estado not in estados_despachador:
                        messages.error(request, 'Solo puedes cambiar a "En Tránsito" o "Entregado".')
                    else:
                        estado_anterior = pedido.estado
                        pedido.estado = nuevo_estado
                        pedido.save()
                        if nuevo_estado == 'entregado' and estado_anterior != 'entregado':
                            _enviar_notificacion_entrega(pedido)
                        messages.success(request, f'Estado de {pedido.numero_tracking} actualizado a "{pedido.get_estado_display()}".')
                else:
                    messages.error(request, 'Acción no permitida.')
            except Pedido.DoesNotExist:
                messages.error(request, 'Pedido no encontrado.')
        return redirect('lista_pedidos')

    estado_filtro = request.GET.get('estado', '')

    # Despachador solo ve SUS pedidos asignados
    if es_despachador:
        pedidos = Pedido.objects.select_related('cliente').filter(despachador=request.user)
    else:
        pedidos = Pedido.objects.select_related('cliente').all()

    if estado_filtro:
        pedidos = pedidos.filter(estado=estado_filtro)

    # Lista de despachadores disponibles para el secretario
    despachadores = []
    if es_secretario:
        from django.contrib.auth.models import Group
        grupo = Group.objects.filter(name='Despachador').first()
        if grupo:
            despachadores = grupo.user_set.all()

    return render(request, 'lista_pedidos.html', {
        'pedidos': pedidos,
        'estado_filtro': estado_filtro,
        'estado_choices': Pedido.ESTADO_CHOICES,
        'es_secretario': es_secretario,
        'es_despachador': es_despachador,
        'despachadores': despachadores,
    })


def iniciar_sesion(request):
    """
    Vista de inicio de sesión.
    Soporta login con email o nombre de usuario.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username_input = request.POST.get('username', '').strip()
        clave = request.POST.get('password', '')

        # Permitir login con email: buscar el username real
        if '@' in username_input:
            try:
                user_obj = User.objects.get(email__iexact=username_input)
                username_input = user_obj.username
            except User.DoesNotExist:
                pass

        user = authenticate(request, username=username_input, password=clave)
        if user is not None:
            login(request, user)
            nombre_display = user.first_name or user.username
            messages.success(request, f'¡Bienvenido de nuevo, {nombre_display}!')
            return redirect('dashboard')
        else:
            messages.error(
                request,
                'Usuario o contraseña incorrectos. '
                'Recuerda que debes ingresar con tu correo electrónico.'
            )

    return render(request, 'login.html')


def cerrar_sesion(request):
    logout(request)
    messages.info(request, 'Has cerrado sesión exitosamente.')
    return redirect('inicio')


@login_required(login_url='iniciar_sesion')
def panel_cliente(request):
    if not hasattr(request.user, 'cliente'):
        messages.error(request, 'No tienes un perfil de cliente asociado.')
        return redirect('inicio')

    pedidos = request.user.cliente.pedidos.all()
    return render(request, 'panel_cliente.html', {'pedidos': pedidos})


@login_required(login_url='iniciar_sesion')
def descargar_orden_pdf(request, tracking):
    """
    Genera y descarga la orden de envío como archivo de texto.
    No requiere librerías externas (sin reportlab, sin qrcode).
    """
    pedido = get_object_or_404(Pedido.objects.select_related('cliente'), numero_tracking=tracking)

    # Clientes solo pueden descargar sus propios pedidos
    if not (request.user.groups.filter(name__in=['Secretario', 'Despachador']).exists()
            or request.user.is_staff):
        if hasattr(request.user, 'cliente') and pedido.cliente != request.user.cliente:
            messages.error(request, 'No tienes permiso para descargar esta orden.')
            return redirect('panel_cliente')

    precio = f'${pedido.precio_envio}' if pedido.precio_envio else 'Por calcular'
    metodo = pedido.get_metodo_pago_display() if pedido.metodo_pago else 'No especificado'
    despachador_nombre = (
        pedido.despachador.get_full_name() or pedido.despachador.username
        if pedido.despachador else 'Sin asignar'
    )

    contenido = (
        '╔══════════════════════════════════════════════╗\n'
        '║      RUTAEXPRES - ORDEN DE ENVÍO             ║\n'
        '║      Centro de Soluciones Logísticas         ║\n'
        '╚══════════════════════════════════════════════╝\n\n'
        f'Número de Tracking : {pedido.numero_tracking}\n'
        f'Estado             : {pedido.get_estado_display()}\n'
        f'Fecha de creación  : {pedido.fecha_creacion.strftime("%d/%m/%Y %H:%M")}\n\n'
        '── CLIENTE ──────────────────────────────────────\n'
        f'Nombre    : {pedido.cliente.nombre} {pedido.cliente.apellido}\n'
        f'Email     : {pedido.cliente.email}\n'
        f'Teléfono  : {pedido.cliente.telefono}\n'
        f'Dirección : {pedido.cliente.direccion}\n\n'
        '── ENVÍO ────────────────────────────────────────\n'
        f'Destinatario    : {pedido.destinatario}\n'
        f'Tipo de servicio: {pedido.get_tipo_servicio_display()}\n'
        f'Origen          : {pedido.origen}\n'
        f'Destino         : {pedido.destino}\n'
        f'Peso            : {pedido.peso_kg} kg\n'
        f'Precio estimado : {precio}\n'
        f'Descripción     : {pedido.descripcion_carga}\n\n'
        '── PAGO ─────────────────────────────────────────\n'
        f'Método de pago  : {metodo}\n'
        f'Pago confirmado : {"SÍ" if pedido.pago_confirmado else "NO"}\n\n'
        '── ASIGNACIÓN ───────────────────────────────────\n'
        f'Despachador     : {despachador_nombre}\n\n'
        '────────────────────────────────────────────────\n'
        'Tel: +593 2 345 6789 | info@rutaexpres.com.ec\n'
        '────────────────────────────────────────────────\n'
    )

    response = HttpResponse(contenido, content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="Orden_{tracking}.txt"'
    return response


@login_required(login_url='iniciar_sesion')
def asignar_despachador(request, tracking):
    """
    Solo el Secretario puede asignar un despachador a un pedido.
    El despachador asignado verá el pedido en su panel.
    """
    es_secretario = request.user.groups.filter(name='Secretario').exists() or request.user.is_staff
    if not es_secretario:
        messages.error(request, 'Solo el Secretario puede asignar despachadores.')
        return redirect('lista_pedidos')

    pedido = get_object_or_404(Pedido, numero_tracking=tracking)

    if request.method == 'POST':
        despachador_id = request.POST.get('despachador_id')
        if despachador_id:
            try:
                despachador = User.objects.get(pk=despachador_id, groups__name='Despachador')
                pedido.despachador = despachador
                pedido.save()
                messages.success(
                    request,
                    f'Pedido {tracking} asignado a {despachador.get_full_name() or despachador.username}.'
                )
            except User.DoesNotExist:
                messages.error(request, 'Despachador no válido.')
        else:
            pedido.despachador = None
            pedido.save()
            messages.info(request, f'Pedido {tracking} quedó sin despachador asignado.')

    return redirect('lista_pedidos')


@login_required(login_url='iniciar_sesion')
def reporte_global(request):
    """
    Reporte financiero y operacional.
    Solo Secretario o staff — el Despachador NO puede ver datos financieros.
    """
    es_secretario = request.user.groups.filter(name='Secretario').exists() or request.user.is_staff
    if not es_secretario:
        messages.error(request, 'Solo el Secretario puede acceder al reporte financiero.')
        return redirect('lista_pedidos')

    pedidos     = Pedido.objects.select_related('cliente').all()
    total       = pedidos.count()
    pendientes  = pedidos.filter(estado='pendiente').count()
    en_transito = pedidos.filter(estado='en_transito').count()
    entregados  = pedidos.filter(estado='entregado').count()
    cancelados  = pedidos.filter(estado='cancelado').count()
    ingresos    = pedidos.exclude(precio_envio__isnull=True).aggregate(
        total=Sum('precio_envio')
    )['total'] or 0

    return render(request, 'reporte.html', {
        'total':       total,
        'pendientes':  pendientes,
        'en_transito': en_transito,
        'entregados':  entregados,
        'cancelados':  cancelados,
        'ingresos':    ingresos,
        'pedidos':     pedidos,
    })
