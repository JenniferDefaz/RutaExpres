from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings

from .models import Cliente, Pedido
from .forms import ClienteForm, PedidoForm, BuscarPedidoForm


def _get_or_create_group(name):
    """Obtiene o crea un grupo de usuarios por nombre."""
    group, _ = Group.objects.get_or_create(name=name)
    return group


def _enviar_bienvenida(cliente):
    """Envía correo de bienvenida al cliente recién registrado."""
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
    """Envía correo de confirmación cuando se registra un pedido."""
    try:
        send_mail(
            subject=f'Pedido registrado — Tracking: {pedido.numero_tracking}',
            message=(
                f'Hola {pedido.cliente.nombre} {pedido.cliente.apellido},\n\n'
                f'Tu pedido ha sido registrado exitosamente en RutaExpres.\n\n'
                f'--- DETALLES DEL PEDIDO ---\n'
                f'Número de tracking : {pedido.numero_tracking}\n'
                f'Destinatario       : {pedido.destinatario}\n'
                f'Tipo de servicio   : {pedido.get_tipo_servicio_display()}\n'
                f'Origen             : {pedido.origen}\n'
                f'Destino            : {pedido.destino}\n'
                f'Peso               : {pedido.peso_kg} kg\n'
                f'Estado actual      : {pedido.get_estado_display()}\n\n'
                f'Puedes rastrear tu envío en cualquier momento ingresando tu\n'
                f'número de tracking en nuestra página web.\n\n'
                f'Saludos,\n'
                f'El equipo de RutaExpres\n'
                f'Tel: +593 2 345 6789 | info@rutaexpres.com.ec'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[pedido.cliente.email],
            fail_silently=True,
        )
    except Exception:
        pass


def _enviar_notificacion_entrega(pedido):
    """Envía correo cuando el pedido cambia a estado 'entregado'."""
    try:
        send_mail(
            subject=f'¡Tu pedido {pedido.numero_tracking} fue entregado!',
            message=(
                f'Hola {pedido.cliente.nombre} {pedido.cliente.apellido},\n\n'
                f'Tu pedido con número de tracking {pedido.numero_tracking} '
                f'ha sido entregado exitosamente a {pedido.destinatario}.\n\n'
                f'Destino: {pedido.destino}\n\n'
                f'Gracias por confiar en RutaExpres para tus envíos.\n\n'
                f'Saludos,\n'
                f'El equipo de RutaExpres\n'
                f'Tel: +593 2 345 6789 | info@rutaexpres.com.ec'
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
    """
    Vista para registrar un nuevo pedido.
    GET  → muestra el formulario vacío.
    POST → valida, guarda y envía correo de confirmación.
    """
    if request.method == 'POST':
        form = PedidoForm(request.POST, user=request.user)
        if form.is_valid():
            pedido = form.save(commit=False)

            # Si es cliente normal (no staff ni roles internos), asignar su propio perfil
            es_rol_interno = (
                request.user.groups.filter(name__in=['Secretario', 'Despachador']).exists()
                or request.user.is_staff
            )
            if not es_rol_interno and hasattr(request.user, 'cliente'):
                pedido.cliente = request.user.cliente
                pedido.estado = 'pendiente'

            pedido.save()

            # Correo de confirmación del pedido
            _enviar_confirmacion_pedido(pedido)

            messages.success(
                request,
                f'Pedido registrado exitosamente. '
                f'Número de tracking: {pedido.numero_tracking}. '
                f'Se envió una confirmación a {pedido.cliente.email}.'
            )
            return redirect('detalle_pedido', tracking=pedido.numero_tracking)
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        form = PedidoForm(user=request.user)

    return render(request, 'registro_pedido.html', {'form': form})


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
    """
    Vista para ver el detalle de un pedido por tracking.
    Devuelve 404 si no existe.
    """
    pedido = get_object_or_404(
        Pedido.objects.select_related('cliente'),
        numero_tracking=tracking
    )
    return render(request, 'detalle_pedido.html', {'pedido': pedido})


@login_required(login_url='iniciar_sesion')
def lista_pedidos(request):
    """
    Vista para listar todos los pedidos (Secretario, Despachador o staff).
    Permite filtrar por estado y actualizar el estado de un pedido.
    """
    es_rol_interno = (
        request.user.groups.filter(name__in=['Secretario', 'Despachador']).exists()
        or request.user.is_staff
    )
    if not es_rol_interno:
        messages.error(request, 'No tienes permisos para acceder al Panel de Administración.')
        return redirect('panel_cliente')

    # Actualización de estado desde el panel
    if request.method == 'POST':
        pedido_id = request.POST.get('pedido_id')
        nuevo_estado = request.POST.get('nuevo_estado')
        estados_validos = [e[0] for e in Pedido.ESTADO_CHOICES]

        if pedido_id and nuevo_estado in estados_validos:
            try:
                pedido = Pedido.objects.select_related('cliente').get(pk=pedido_id)
                estado_anterior = pedido.estado
                pedido.estado = nuevo_estado
                pedido.save()

                # Si pasó a "entregado", notificar al cliente
                if nuevo_estado == 'entregado' and estado_anterior != 'entregado':
                    _enviar_notificacion_entrega(pedido)

                messages.success(
                    request,
                    f'Estado del pedido {pedido.numero_tracking} actualizado a '
                    f'"{pedido.get_estado_display()}".'
                )
            except Pedido.DoesNotExist:
                messages.error(request, 'Pedido no encontrado.')
        else:
            messages.error(request, 'Datos de actualización inválidos.')

        return redirect('lista_pedidos')

    estado_filtro = request.GET.get('estado', '')
    pedidos = Pedido.objects.select_related('cliente').all()

    if estado_filtro:
        pedidos = pedidos.filter(estado=estado_filtro)

    return render(request, 'lista_pedidos.html', {
        'pedidos': pedidos,
        'estado_filtro': estado_filtro,
        'estado_choices': Pedido.ESTADO_CHOICES,
    })


def iniciar_sesion(request):
    """
    Vista de inicio de sesión.
    Soporta login con email o nombre de usuario.
    """
    if request.user.is_authenticated:
        if (request.user.groups.filter(name__in=['Secretario', 'Despachador']).exists()
                or request.user.is_staff):
            return redirect('lista_pedidos')
        return redirect('panel_cliente')

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
            if (user.groups.filter(name__in=['Secretario', 'Despachador']).exists()
                    or user.is_staff):
                return redirect('lista_pedidos')
            else:
                return redirect('panel_cliente')
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
