from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.http import HttpResponse
from django.db.models import Sum, Count
import json
import io
import base64

from .models import Cliente, Pedido
from .forms import ClienteForm, PedidoForm, BuscarPedidoForm

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT


def _get_or_create_group(name):
    group, _ = Group.objects.get_or_create(name=name)
    return group


def _generar_qr_base64(texto):
    try:
        import qrcode
        qr = qrcode.QRCode(version=1, box_size=6, border=2)
        qr.add_data(texto)
        qr.make(fit=True)
        img = qr.make_image(fill_color='#1F1F1F', back_color='white')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    except ImportError:
        return None


def _enviar_bienvenida(cliente):
    """Correo #1 — Bienvenida HTML al registrarse."""
    try:
        asunto = '¡Bienvenido a RutaExpres - Centro de Soluciones!'
        texto = (
            f'Hola {cliente.nombre} {cliente.apellido},\n\n'
            f'Tu cuenta fue creada con el correo: {cliente.email}\n\n'
            f'Ya puedes iniciar sesión.\n\nRutaExpres'
        )
        html = f"""<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;border:1px solid #eee;border-radius:8px;overflow:hidden;">
<div style="background:#CE1212;padding:28px 32px;text-align:center;">
<h1 style="color:#fff;margin:0;font-size:26px;">&#128666; RutaExpres</h1>
<p style="color:rgba(255,255,255,.85);margin:6px 0 0;">Centro de Soluciones Logísticas</p>
</div>
<div style="padding:32px;">
<h2 style="color:#1F1F1F;">¡Bienvenido, {cliente.nombre}! &#127881;</h2>
<p style="color:#555;line-height:1.7;">Tu cuenta ha sido creada exitosamente en <strong>RutaExpres</strong>.</p>
<div style="background:#f9f9f9;border-left:4px solid #CE1212;padding:16px 20px;margin:20px 0;border-radius:4px;">
<p style="margin:0;color:#333;"><strong>Correo de acceso:</strong> {cliente.email}</p>
</div>
<div style="text-align:center;margin:28px 0;">
<a href="http://127.0.0.1:8000/login/" style="background:#CE1212;color:#fff;padding:14px 36px;border-radius:6px;text-decoration:none;font-weight:bold;font-size:15px;">Iniciar Sesión &#8594;</a>
</div>
<p style="color:#777;font-size:13px;text-align:center;border-top:1px solid #eee;padding-top:20px;">RutaExpres &middot; Tel: +593 2 345 6789 &middot; info@rutaexpres.com.ec</p>
</div>
</div>"""
        email = EmailMultiAlternatives(subject=asunto, body=texto,
                                       from_email=settings.DEFAULT_FROM_EMAIL, to=[cliente.email])
        email.attach_alternative(html, 'text/html')
        email.send(fail_silently=True)
    except Exception:
        pass

def _generar_factura_pdf(pedido):
    """Genera la factura del pedido en PDF y devuelve los bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        topMargin=20 * mm, bottomMargin=20 * mm,
        leftMargin=20 * mm, rightMargin=20 * mm,
    )
    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle(
        'TituloFactura', parent=styles['Title'], textColor=colors.HexColor('#CE1212'),
        fontSize=22, alignment=TA_CENTER, spaceAfter=2,
    )
    subtitulo_style = ParagraphStyle(
        'Subtitulo', parent=styles['Normal'], textColor=colors.HexColor('#555555'),
        fontSize=10, alignment=TA_CENTER, spaceAfter=14,
    )
    tracking_style = ParagraphStyle(
        'Tracking', parent=styles['Normal'], textColor=colors.HexColor('#CE1212'),
        fontSize=13, alignment=TA_RIGHT, spaceAfter=4, fontName='Helvetica-Bold',
    )
    seccion_style = ParagraphStyle(
        'Seccion', parent=styles['Heading2'], textColor=colors.HexColor('#1F1F1F'),
        fontSize=12, spaceBefore=14, spaceAfter=6,
    )

    story = []
    story.append(Paragraph('RutaExpres', titulo_style))
    story.append(Paragraph('Centro de Soluciones Logísticas &middot; FACTURA / COMPROBANTE DE ENVÍO', subtitulo_style))
    story.append(Paragraph(f'Guía N°: {pedido.numero_tracking}', tracking_style))
    story.append(Paragraph(
        f'Fecha: {pedido.fecha_creacion.strftime("%d/%m/%Y %H:%M")}',
        ParagraphStyle('Fecha', parent=styles['Normal'], alignment=TA_RIGHT, fontSize=9, textColor=colors.grey)
    ))

    story.append(Paragraph('Datos del cliente', seccion_style))
    datos_cliente = [
        ['Nombre:', f'{pedido.cliente.nombre} {pedido.cliente.apellido}'],
        ['Correo:', pedido.cliente.email],
        ['Teléfono:', pedido.cliente.telefono],
        ['Dirección:', pedido.cliente.direccion],
    ]
    tabla_cliente = Table(datos_cliente, colWidths=[35 * mm, 130 * mm])
    tabla_cliente.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9.5),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#888888')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(tabla_cliente)

    story.append(Paragraph('Detalle del envío', seccion_style))
    precio_texto = f'${pedido.precio_envio}' if pedido.precio_envio else 'Por calcular'
    datos_envio = [
        ['Destinatario:', pedido.destinatario],
        ['Tipo de servicio:', pedido.get_tipo_servicio_display()],
        ['Origen:', pedido.origen],
        ['Destino:', pedido.destino],
        ['Peso:', f'{pedido.peso_kg} kg'],
        ['Descripción de carga:', pedido.descripcion_carga],
        ['Estado:', pedido.get_estado_display()],
    ]
    tabla_envio = Table(datos_envio, colWidths=[45 * mm, 120 * mm])
    tabla_envio.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9.5),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#888888')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(tabla_envio)

    story.append(Spacer(1, 14))
    tabla_total = Table([['TOTAL A PAGAR', precio_texto]], colWidths=[135 * mm, 30 * mm])
    tabla_total.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1F1F1F')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(tabla_total)

    story.append(Spacer(1, 30))
    story.append(Paragraph(
        'RutaExpres &middot; Tel: +593 2 345 6789 &middot; info@rutaexpres.com.ec',
        ParagraphStyle('Footer', parent=styles['Normal'], alignment=TA_CENTER, fontSize=8, textColor=colors.grey)
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
    

def _enviar_confirmacion_pedido(pedido):
    """Correo #2 — Confirmación de pedido con QR de tracking (HTML)."""
    try:
        url_rastreo = f'http://127.0.0.1:8000/pedidos/{pedido.numero_tracking}/'
        precio_texto = f'${pedido.precio_envio}' if pedido.precio_envio else 'Por calcular'
        
        asunto = f'[RutaExpres] Pedido registrado — Tracking: {pedido.numero_tracking}'
        texto = (
            f'Hola {pedido.cliente.nombre},\n\nTracking: {pedido.numero_tracking}\n'
            f'Destino: {pedido.destino}\nPeso: {pedido.peso_kg} kg\n'
            f'Precio: {precio_texto}\nRastrea: {url_rastreo}\n\nRutaExpres'
        )
        html = f"""<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;border:1px solid #eee;border-radius:8px;overflow:hidden;">
<div style="background:#CE1212;padding:28px 32px;text-align:center;">
<h1 style="color:#fff;margin:0;font-size:26px;">&#128666; RutaExpres</h1>
<p style="color:rgba(255,255,255,.85);margin:6px 0 0;">Confirmación de Pedido</p>
</div>
<div style="padding:32px;">
<h2 style="color:#1F1F1F;">¡Pedido registrado exitosamente!</h2>
<p style="color:#555;">Hola <strong>{pedido.cliente.nombre} {pedido.cliente.apellido}</strong>.</p>
<div style="background:#f9f9f9;border-radius:8px;padding:20px;margin:20px 0;">
<table style="width:100%;border-collapse:collapse;">
<tr><td style="padding:6px 0;color:#888;width:40%;">Tracking</td><td style="font-weight:bold;color:#CE1212;font-size:16px;">{pedido.numero_tracking}</td></tr>
<tr><td style="padding:6px 0;color:#888;">Destinatario</td><td style="color:#333;">{pedido.destinatario}</td></tr>
<tr><td style="padding:6px 0;color:#888;">Servicio</td><td style="color:#333;">{pedido.get_tipo_servicio_display()}</td></tr>
<tr><td style="padding:6px 0;color:#888;">Origen</td><td style="color:#333;">{pedido.origen}</td></tr>
<tr><td style="padding:6px 0;color:#888;">Destino</td><td style="color:#333;">{pedido.destino}</td></tr>
<tr><td style="padding:6px 0;color:#888;">Peso</td><td style="color:#333;">{pedido.peso_kg} kg</td></tr>
<tr><td style="padding:6px 0;color:#888;">Precio estimado</td><td style="font-weight:bold;color:#CE1212;">{precio_texto}</td></tr>
<tr><td style="padding:6px 0;color:#888;">Fecha</td><td style="color:#333;">{pedido.fecha_creacion.strftime('%d/%m/%Y %H:%M')}</td></tr>
</table>
</div>
<div style="text-align:center;margin:24px 0;">
<a href="{url_rastreo}" style="background:#CE1212;color:#fff;padding:14px 36px;border-radius:6px;text-decoration:none;font-weight:bold;">Rastrear mi pedido &#8594;</a>
</div>
<p style="color:#777;font-size:13px;text-align:center;border-top:1px solid #eee;padding-top:20px;">RutaExpres &middot; Tel: +593 2 345 6789</p>
</div>
</div>"""
        email = EmailMultiAlternatives(subject=asunto, body=texto,
                                       from_email=settings.DEFAULT_FROM_EMAIL, to=[pedido.cliente.email])
        email.attach_alternative(html, 'text/html')

        pdf_bytes = _generar_factura_pdf(pedido)
        email.attach(f'Factura_{pedido.numero_tracking}.pdf', pdf_bytes, 'application/pdf')

        email.send(fail_silently=True)
    except Exception as e:
        print(f'Error enviando confirmación de pedido: {e}')


def _enviar_notificacion_entrega(pedido):
    """Correo #3 — Notificación de entrega con QR (HTML)."""
    try:
        url_detalle = f'http://127.0.0.1:8000/pedidos/{pedido.numero_tracking}/'
        qr_b64 = _generar_qr_base64(url_detalle)
        qr_html = (
            f'<div style="text-align:center;margin:20px 0;">'
            f'<img src="data:image/png;base64,{qr_b64}" width="160" height="160" '
            f'alt="QR" style="border:2px solid #198754;border-radius:8px;padding:6px;"/>'
            f'<p style="color:#888;font-size:12px;margin-top:8px;">Comprobante de entrega</p>'
            f'</div>'
        ) if qr_b64 else ''
        asunto = f'[RutaExpres] Tu pedido {pedido.numero_tracking} fue entregado'
        texto = (
            f'Hola {pedido.cliente.nombre},\n\n'
            f'Tu pedido {pedido.numero_tracking} fue entregado exitosamente.\n'
            f'Destino: {pedido.destino}\n'
            f'Entregado: {pedido.fecha_actualizacion.strftime("%d/%m/%Y %H:%M")}\n\n'
            f'Verifica: {url_detalle}\n\nRutaExpres'
        )
        html = f"""<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;border:1px solid #eee;border-radius:8px;overflow:hidden;">
<div style="background:#198754;padding:28px 32px;text-align:center;">
<h1 style="color:#fff;margin:0;font-size:26px;">&#9989; ¡Pedido Entregado!</h1>
<p style="color:rgba(255,255,255,.85);margin:6px 0 0;">RutaExpres &mdash; Confirmación de Entrega</p>
</div>
<div style="padding:32px;">
<h2 style="color:#1F1F1F;">¡Tu envío llegó a su destino!</h2>
<p style="color:#555;">Hola <strong>{pedido.cliente.nombre} {pedido.cliente.apellido}</strong>.</p>
<div style="background:#d1e7dd;border-radius:8px;padding:20px;margin:20px 0;">
<table style="width:100%;border-collapse:collapse;">
<tr><td style="padding:6px 0;color:#0f5132;width:40%;">Tracking</td><td style="font-weight:bold;color:#0f5132;font-size:16px;">{pedido.numero_tracking}</td></tr>
<tr><td style="padding:6px 0;color:#0f5132;">Destinatario</td><td style="color:#0f5132;">{pedido.destinatario}</td></tr>
<tr><td style="padding:6px 0;color:#0f5132;">Destino</td><td style="color:#0f5132;">{pedido.destino}</td></tr>
<tr><td style="padding:6px 0;color:#0f5132;">Entregado el</td><td style="font-weight:bold;color:#0f5132;">{pedido.fecha_actualizacion.strftime('%d/%m/%Y %H:%M')}</td></tr>
</table>
</div>
{qr_html}
<div style="text-align:center;margin:24px 0;">
<a href="{url_detalle}" style="background:#198754;color:#fff;padding:14px 36px;border-radius:6px;text-decoration:none;font-weight:bold;">Ver detalle del pedido &#8594;</a>
</div>
<p style="color:#777;font-size:13px;text-align:center;border-top:1px solid #eee;padding-top:20px;">Gracias por confiar en RutaExpres &middot; Tel: +593 2 345 6789</p>
</div>
</div>"""
        email = EmailMultiAlternatives(subject=asunto, body=texto,
                                       from_email=settings.DEFAULT_FROM_EMAIL, to=[pedido.cliente.email])
        email.attach_alternative(html, 'text/html')
        email.send(fail_silently=True)
    except Exception:
        pass


def inicio(request):
    return render(request, 'inicio.html')


@login_required(login_url='iniciar_sesion')
def dashboard(request):
    es_secretario = request.user.is_staff or request.user.groups.filter(name='Secretario').exists()
    es_despachador = request.user.groups.filter(name='Despachador').exists()

    if es_secretario:
        pedidos = Pedido.objects.select_related('cliente').all()
        total = pedidos.count()
        pendientes = pedidos.filter(estado='pendiente').count()
        en_transito = pedidos.filter(estado='en_transito').count()
        entregados = pedidos.filter(estado='entregado').count()
        cancelados = pedidos.filter(estado='cancelado').count()
        ingresos = pedidos.exclude(precio_envio__isnull=True).aggregate(total=Sum('precio_envio'))['total'] or 0
        total_clientes = Cliente.objects.count()

        # Gráfico 1: Pedidos por estado (barras)
        etiquetas_estado = ['Pendiente', 'En Tránsito', 'Entregado', 'Cancelado']
        datos_estado = [pendientes, en_transito, entregados, cancelados]

        # Gráfico 2: Clientes frecuentes — top 5 por número de pedidos
        from django.db.models import Count as DCount
        top_clientes = (
            Cliente.objects.annotate(num_pedidos=DCount('pedidos'))
            .order_by('-num_pedidos')[:5]
        )
        etiquetas_clientes = [f'{c.nombre} {c.apellido}' for c in top_clientes]
        datos_clientes = [c.num_pedidos for c in top_clientes]

        pedidos_recientes = pedidos.order_by('-fecha_creacion')[:5]
        grupo_d = Group.objects.filter(name='Despachador').first()
        despachadores = grupo_d.user_set.all() if grupo_d else []

        return render(request, 'dashboard_secretario.html', {
            'total': total, 'pendientes': pendientes, 'en_transito': en_transito,
            'entregados': entregados, 'cancelados': cancelados, 'ingresos': ingresos,
            'total_clientes': total_clientes, 'pedidos_recientes': pedidos_recientes,
            'etiquetas_estado_json': json.dumps(etiquetas_estado),
            'datos_estado_json': json.dumps(datos_estado),
            'etiquetas_clientes_json': json.dumps(etiquetas_clientes),
            'datos_clientes_json': json.dumps(datos_clientes),
            'despachadores': despachadores,
        })

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
            'total': total, 'pendientes': pendientes, 'en_transito': en_transito,
            'entregados': entregados, 'cancelados': cancelados,
            'pedidos_recientes': pedidos_recientes,
            'etiquetas_estado_json': json.dumps(etiquetas_estado),
            'datos_estado_json': json.dumps(datos_estado),
        })

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
            'total': total, 'pendientes': pendientes, 'en_transito': en_transito,
            'entregados': entregados, 'cancelados': cancelados,
            'pedidos': pedidos, 'pedidos_recientes': pedidos_recientes,
        })


def registrar_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save(commit=False)
            password = form.cleaned_data['password']
            username = cliente.email
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Ya existe una cuenta registrada con ese correo electrónico.')
                return render(request, 'registro_cliente.html', {'form': form})
            user = User.objects.create_user(
                username=username, email=cliente.email, password=password,
                first_name=cliente.nombre, last_name=cliente.apellido,
            )
            grupo_cliente = _get_or_create_group('Cliente')
            user.groups.add(grupo_cliente)
            cliente.user = user
            cliente.save()
            _enviar_bienvenida(cliente)
            messages.success(
                request,
                f'¡Registro exitoso! Bienvenido {cliente.nombre}. '
                f'Te enviamos un correo de bienvenida a {cliente.email}. '
                f'Ya puedes iniciar sesión.'
            )
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
    form = BuscarPedidoForm(request.POST or None)
    pedido = None
    if request.method == 'POST' and form.is_valid():
        tracking = form.cleaned_data['numero_tracking']
        try:
            pedido = Pedido.objects.select_related('cliente').get(numero_tracking=tracking)
        except Pedido.DoesNotExist:
            messages.error(request, f'No se encontró ningún pedido con el número de tracking: {tracking}')
    return render(request, 'rastrear_pedido.html', {'form': form, 'pedido': pedido})


def detalle_pedido(request, tracking):
    pedido = get_object_or_404(Pedido.objects.select_related('cliente'), numero_tracking=tracking)
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
                if es_secretario and not es_despachador:
                    messages.error(request, 'El secretario solo puede asignar despachadores.')
                elif es_despachador and pedido.despachador != request.user:
                    messages.error(request, 'No tienes permiso para modificar este pedido.')
                elif confirmar_pago and es_despachador:
                    pedido.pago_confirmado = True
                    pedido.save()
                    messages.success(request, f'Pago confirmado para el pedido {pedido.numero_tracking}.')
                elif nuevo_estado in estados_validos and es_despachador:
                    if nuevo_estado not in estados_despachador:
                        messages.error(request, 'Solo puedes cambiar a "En Tránsito" o "Entregado".')
                    elif nuevo_estado in ['en_transito', 'entregado'] and not pedido.pago_confirmado:
                        messages.error(
                            request,
                            f'No puedes mover el pedido {pedido.numero_tracking} a '
                            f'"{dict(Pedido.ESTADO_CHOICES)[nuevo_estado]}" porque el pago aún no ha sido confirmado. '
                            f'Confirma el pago primero.'
                        )
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
    if es_despachador:
        pedidos = Pedido.objects.select_related('cliente').filter(despachador=request.user)
    else:
        pedidos = Pedido.objects.select_related('cliente').all()
    if estado_filtro:
        pedidos = pedidos.filter(estado=estado_filtro)

    despachadores = []
    if es_secretario:
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
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username_input = request.POST.get('username', '').strip()
        clave = request.POST.get('password', '')
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
            messages.error(request, 'Usuario o contraseña incorrectos. Recuerda ingresar con tu correo electrónico.')
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
def qr_pedido(request, tracking):
    """Genera el QR del pedido como imagen PNG."""
    try:
        import qrcode
        get_object_or_404(Pedido, numero_tracking=tracking)
        url = request.build_absolute_uri(f'/pedidos/{tracking}/')
        qr = qrcode.QRCode(version=1, box_size=8, border=3)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color='#1F1F1F', back_color='white')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return HttpResponse(buffer.getvalue(), content_type='image/png')
    except ImportError:
        return HttpResponse('QR no disponible. Instala: pip install qrcode[pil]', status=503)


@login_required(login_url='iniciar_sesion')
def descargar_orden_pdf(request, tracking):
    """Descarga la factura del pedido como PDF real."""
    pedido = get_object_or_404(Pedido.objects.select_related('cliente'), numero_tracking=tracking)
    if not (request.user.groups.filter(name__in=['Secretario', 'Despachador']).exists()
            or request.user.is_staff):
        if hasattr(request.user, 'cliente') and pedido.cliente != request.user.cliente:
            messages.error(request, 'No tienes permiso para descargar esta orden.')
            return redirect('panel_cliente')

    pdf_bytes = _generar_factura_pdf(pedido)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Factura_{tracking}.pdf"'
    return response

@login_required(login_url='iniciar_sesion')
def asignar_despachador(request, tracking):
    """Solo el Secretario puede asignar un despachador a un pedido."""
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
    """Reporte financiero — solo Secretario o staff."""
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
    ingresos = pedidos.exclude(precio_envio__isnull=True).aggregate(
        total=Sum('precio_envio')
    )['total'] or 0
    return render(request, 'reporte.html', {
        'total': total, 'pendientes': pendientes, 'en_transito': en_transito,
        'entregados': entregados, 'cancelados': cancelados,
        'ingresos': ingresos, 'pedidos': pedidos,
    })
