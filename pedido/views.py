from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.http import HttpResponse

import qrcode
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

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
    """Envía correo de confirmación con PDF adjunto cuando se registra un pedido."""
    try:
        pdf_bytes = _generar_pdf_pedido(pedido)
        email = EmailMessage(
            subject=f'Pedido registrado — Tracking: {pedido.numero_tracking}',
            body=(
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
                f'Adjunto encontrará su orden de envío en PDF con código QR.\n'
                f'Puede rastrear su envío en cualquier momento con el número de tracking.\n\n'
                f'Saludos,\n'
                f'El equipo de RutaExpres\n'
                f'Tel: +593 2 345 6789 | info@rutaexpres.com.ec'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[pedido.cliente.email],
        )
        email.attach(f'orden_{pedido.numero_tracking}.pdf', pdf_bytes, 'application/pdf')
        email.send()
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

    # Solo secretario puede confirmar pago
    if request.method == 'POST':
        pedido_id = request.POST.get('pedido_id')
        nuevo_estado = request.POST.get('nuevo_estado')
        confirmar_pago = request.POST.get('confirmar_pago')
        estados_validos = [e[0] for e in Pedido.ESTADO_CHOICES]

        # Despachador solo puede cambiar a en_transito o entregado
        estados_despachador = ['en_transito', 'entregado']

        if pedido_id:
            try:
                pedido = Pedido.objects.select_related('cliente').get(pk=pedido_id)

                # Confirmar pago (solo secretario)
                if confirmar_pago and es_secretario:
                    pedido.pago_confirmado = True
                    pedido.save()
                    messages.success(request, f'Pago confirmado para el pedido {pedido.numero_tracking}.')

                # Cambiar estado
                elif nuevo_estado in estados_validos:
                    if es_despachador and nuevo_estado not in estados_despachador:
                        messages.error(request, 'El despachador solo puede cambiar a En Tránsito o Entregado.')
                    else:
                        estado_anterior = pedido.estado
                        pedido.estado = nuevo_estado
                        pedido.save()
                        if nuevo_estado == 'entregado' and estado_anterior != 'entregado':
                            _enviar_notificacion_entrega(pedido)
                        messages.success(request, f'Estado del pedido {pedido.numero_tracking} actualizado a "{pedido.get_estado_display()}".')
                else:
                    messages.error(request, 'Datos de actualización inválidos.')
            except Pedido.DoesNotExist:
                messages.error(request, 'Pedido no encontrado.')
        return redirect('lista_pedidos')

    estado_filtro = request.GET.get('estado', '')
    pedidos = Pedido.objects.select_related('cliente').all()
    if estado_filtro:
        pedidos = pedidos.filter(estado=estado_filtro)

    return render(request, 'lista_pedidos.html', {
        'pedidos': pedidos,
        'estado_filtro': estado_filtro,
        'estado_choices': Pedido.ESTADO_CHOICES,
        'es_secretario': es_secretario,
        'es_despachador': es_despachador,
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


# ─── Generación de PDF con QR ────────────────────────────────

def _generar_pdf_pedido(pedido):
    """Genera el PDF de la orden de pedido con QR. Devuelve bytes."""
    # QR con el número de tracking
    qr = qrcode.QRCode(version=1, box_size=6, border=2)
    qr.add_data(
        f"RutaExpres - Orden de Envío\n"
        f"Tracking: {pedido.numero_tracking}\n"
        f"Cliente: {pedido.cliente.nombre} {pedido.cliente.apellido}\n"
        f"Destinatario: {pedido.destinatario}\n"
        f"Origen: {pedido.origen}\n"
        f"Destino: {pedido.destino}\n"
        f"Peso: {pedido.peso_kg} kg\n"
        f"Estado: {pedido.get_estado_display()}"
    )
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#003580", back_color="white")
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)

    # Estilos
    titulo = ParagraphStyle('titulo', fontSize=20, alignment=TA_CENTER,
                             fontName='Helvetica-Bold', textColor=colors.HexColor('#003580'), spaceAfter=4)
    subtitulo = ParagraphStyle('sub', fontSize=11, alignment=TA_CENTER,
                                fontName='Helvetica', textColor=colors.HexColor('#555'), spaceAfter=6)
    label = ParagraphStyle('label', fontSize=10, fontName='Helvetica-Bold',
                            textColor=colors.HexColor('#003580'))
    valor = ParagraphStyle('valor', fontSize=10, fontName='Helvetica',
                            textColor=colors.black)
    pie = ParagraphStyle('pie', fontSize=8, alignment=TA_CENTER,
                          fontName='Helvetica-Oblique', textColor=colors.grey)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    def draw_border(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor('#003580'))
        canvas.setLineWidth(3)
        canvas.rect(1*cm, 1*cm, A4[0]-2*cm, A4[1]-2*cm)
        canvas.restoreState()

    elementos = []
    elementos.append(Spacer(1, 0.5*cm))
    elementos.append(Paragraph("ORDEN DE ENVÍO", titulo))
    elementos.append(Paragraph("RutaExpres — Centro de Soluciones Logísticas", subtitulo))
    elementos.append(Spacer(1, 0.3*cm))

    # Línea separadora
    sep = Table([['']], colWidths=[A4[0]-4*cm])
    sep.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,-1), 1.5, colors.HexColor('#003580')),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    elementos.append(sep)

    # Datos del pedido + QR lado a lado
    datos = [
        [Paragraph("N° Tracking:", label), Paragraph(f"<b>{pedido.numero_tracking}</b>", ParagraphStyle('t', fontSize=12, fontName='Helvetica-Bold', textColor=colors.HexColor('#003580')))],
        [Paragraph("Estado:", label), Paragraph(pedido.get_estado_display(), valor)],
        [Paragraph("Cliente:", label), Paragraph(f"{pedido.cliente.nombre} {pedido.cliente.apellido}", valor)],
        [Paragraph("Email:", label), Paragraph(pedido.cliente.email, valor)],
        [Paragraph("Teléfono:", label), Paragraph(pedido.cliente.telefono, valor)],
        [Paragraph("Destinatario:", label), Paragraph(pedido.destinatario, valor)],
        [Paragraph("Tipo de servicio:", label), Paragraph(pedido.get_tipo_servicio_display(), valor)],
        [Paragraph("Origen:", label), Paragraph(pedido.origen, valor)],
        [Paragraph("Destino:", label), Paragraph(pedido.destino, valor)],
        [Paragraph("Peso:", label), Paragraph(f"{pedido.peso_kg} kg", valor)],
        [Paragraph("Descripción:", label), Paragraph(pedido.descripcion_carga, valor)],
        [Paragraph("Fecha:", label), Paragraph(pedido.fecha_creacion.strftime('%d/%m/%Y %H:%M'), valor)],
    ]

    tabla_datos = Table(datos, colWidths=[4*cm, 9*cm])
    tabla_datos.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [colors.HexColor('#f0f4ff'), colors.white]),
    ]))

    qr_image = Image(qr_buffer, width=4*cm, height=4*cm)

    cuerpo = Table(
        [[tabla_datos, qr_image]],
        colWidths=[13*cm, 4.5*cm]
    )
    cuerpo.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (1,0), (1,0), 'CENTER'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    elementos.append(cuerpo)
    elementos.append(Spacer(1, 0.5*cm))

    # Pie
    sep2 = Table([['']], colWidths=[A4[0]-4*cm])
    sep2.setStyle(TableStyle([
        ('LINEABOVE', (0,0), (-1,-1), 1, colors.HexColor('#003580')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
    ]))
    elementos.append(sep2)
    elementos.append(Paragraph(
        "Escanee el código QR para rastrear su envío en línea · Tel: +593 2 345 6789 · info@rutaexpres.com.ec",
        pie
    ))

    doc.build(elementos, onFirstPage=draw_border, onLaterPages=draw_border)
    buffer.seek(0)
    return buffer.read()


@login_required(login_url='iniciar_sesion')
def reporte_global(request):
    """Reporte global solo para Secretario o staff — NO para Despachador."""
    es_secretario = request.user.groups.filter(name='Secretario').exists() or request.user.is_staff
    if not es_secretario:
        messages.error(request, 'Solo el Secretario puede acceder al reporte financiero.')
        return redirect('lista_pedidos')

    pedidos = Pedido.objects.select_related('cliente').all()
    total = pedidos.count()
    pendientes = pedidos.filter(estado='pendiente').count()
    en_transito = pedidos.filter(estado='en_transito').count()
    entregados = pedidos.filter(estado='entregado').count()
    cancelados = pedidos.filter(estado='cancelado').count()

    # Ingresos totales (pedidos con precio calculado)
    from django.db.models import Sum
    ingresos = pedidos.exclude(precio_envio__isnull=True).aggregate(
        total=Sum('precio_envio')
    )['total'] or 0

    return render(request, 'reporte.html', {
        'total': total,
        'pendientes': pendientes,
        'en_transito': en_transito,
        'entregados': entregados,
        'cancelados': cancelados,
        'ingresos': ingresos,
        'pedidos': pedidos,
    })


@login_required(login_url='iniciar_sesion')
def descargar_orden_pdf(request, tracking):
    """Descarga el PDF de la orden de un pedido."""
    pedido = get_object_or_404(Pedido.objects.select_related('cliente'), numero_tracking=tracking)
    pdf_bytes = _generar_pdf_pedido(pedido)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Orden_de_Envio_{tracking}.pdf"'
    return response
