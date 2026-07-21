import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.core.mail import EmailMessage
from django.db.models import Count
from io import BytesIO
from django.template.loader import get_template

from .models import Encomienda, Ciudad, PerfilUsuario, HistorialEstado
from .forms import (LoginForm, ClienteForm, ClienteEditForm, CiudadForm, 
                    EncomiendaForm, CambioEstadoForm)
from .decorators import secretario_requerido, despachador_requerido, cliente_requerido

try:
    from xhtml2pdf import pisa
    XHTML2PDF_AVAILABLE = True
except ImportError:
    XHTML2PDF_AVAILABLE = False

def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode('UTF-8')), result)
    if not pdf.err:
        return result.getvalue()
    return None

# --- Public Views ---
def inicio(request):
    return render(request, 'inicio.html')

def rastreo_publico(request):
    if request.method == 'POST':
        numero_guia = request.POST.get('numero_guia')
        if numero_guia:
            return redirect('resultado_rastreo', numero_guia=numero_guia)
    return render(request, 'rastreo/buscar.html')

def resultado_rastreo(request, numero_guia):
    encomienda = Encomienda.objects.filter(numero_guia=numero_guia).first()
    if not encomienda:
        messages.error(request, 'No se encontró ninguna encomienda con ese número de guía.')
        return redirect('rastreo_publico')
    
    historial = encomienda.historial.all().order_by('fecha')
    nombre_destinatario = encomienda.nombre_destinatario.split()[0] if encomienda.nombre_destinatario else ''
    
    context = {
        'numero_guia': encomienda.numero_guia,
        'estado': encomienda.estado,
        'ciudad_destino': encomienda.ciudad_destino,
        'nombre_destinatario': nombre_destinatario,
        'historial': historial
    }
    return render(request, 'rastreo/resultado.html', context)

# --- Auth Views ---
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if hasattr(user, 'perfil'):
                if user.perfil.rol == 'SECRETARIO':
                    return redirect('dashboard_secretario')
                elif user.perfil.rol == 'DESPACHADOR':
                    return redirect('mis_asignaciones')
                elif user.perfil.rol == 'CLIENTE':
                    return redirect('mis_envios')
            return redirect('inicio')
    else:
        form = LoginForm()
    return render(request, 'registration/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('inicio')

# --- Secretario Views ---
@secretario_requerido
def dashboard_secretario(request):
    encomiendas = Encomienda.objects.all()
    hoy = datetime.date.today()
    
    context = {
        'total_encomiendas': encomiendas.count(),
        'encomiendas_hoy': encomiendas.filter(fecha_registro__date=hoy).count(),
        'en_transito': encomiendas.filter(estado='EN_TRANSITO').count(),
        'entregadas': encomiendas.filter(estado='ENTREGADA').count(),
        'pendientes': encomiendas.exclude(estado__in=['ENTREGADA', 'NO_ENTREGADA']).count(),
        'ultimas_encomiendas': encomiendas.order_by('-fecha_registro')[:10]
    }
    return render(request, 'secretario/dashboard.html', context)

@secretario_requerido
def listar_clientes(request):
    clientes = PerfilUsuario.objects.filter(rol='CLIENTE').select_related('usuario')
    return render(request, 'secretario/clientes_lista.html', {'clientes': clientes})

@secretario_requerido
def crear_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente registrado exitosamente.')
            return redirect('listar_clientes')
    else:
        form = ClienteForm()
    return render(request, 'secretario/cliente_form.html', {'form': form, 'titulo': 'Registrar Nuevo Cliente'})

@secretario_requerido
def editar_cliente(request, pk):
    perfil = get_object_or_404(PerfilUsuario, pk=pk, rol='CLIENTE')
    user = perfil.usuario
    if request.method == 'POST':
        form = ClienteEditForm(request.POST)
        if form.is_valid():
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()
            
            perfil.telefono = form.cleaned_data['telefono']
            perfil.cedula = form.cleaned_data['cedula']
            perfil.direccion = form.cleaned_data['direccion']
            perfil.save()
            messages.success(request, 'Cliente actualizado exitosamente.')
            return redirect('listar_clientes')
    else:
        initial_data = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'telefono': perfil.telefono,
            'cedula': perfil.cedula,
            'direccion': perfil.direccion,
        }
        form = ClienteEditForm(initial=initial_data)
    return render(request, 'secretario/cliente_form.html', {'form': form, 'titulo': 'Editar Cliente', 'editando': True})

@secretario_requerido
def listar_ciudades(request):
    ciudades = Ciudad.objects.all()
    return render(request, 'secretario/ciudades_lista.html', {'ciudades': ciudades})

@secretario_requerido
def crear_ciudad(request):
    if request.method == 'POST':
        form = CiudadForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ciudad registrada exitosamente.')
            return redirect('listar_ciudades')
    else:
        form = CiudadForm()
    return render(request, 'secretario/ciudad_form.html', {'form': form, 'titulo': 'Registrar Ciudad'})

@secretario_requerido
def editar_ciudad(request, pk):
    ciudad = get_object_or_404(Ciudad, pk=pk)
    if request.method == 'POST':
        form = CiudadForm(request.POST, instance=ciudad)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ciudad actualizada exitosamente.')
            return redirect('listar_ciudades')
    else:
        form = CiudadForm(instance=ciudad)
    return render(request, 'secretario/ciudad_form.html', {'form': form, 'titulo': 'Editar Ciudad', 'editando': True})

@secretario_requerido
def toggle_ciudad(request, pk):
    ciudad = get_object_or_404(Ciudad, pk=pk)
    ciudad.activa = not ciudad.activa
    ciudad.save()
    messages.success(request, f"Ciudad {'activada' if ciudad.activa else 'desactivada'} exitosamente.")
    return redirect('listar_ciudades')

@secretario_requerido
def listar_encomiendas(request):
    encomiendas = Encomienda.objects.select_related('cliente__usuario', 'ciudad_destino').all()
    return render(request, 'secretario/encomiendas_lista.html', {'encomiendas': encomiendas})

@secretario_requerido
def registrar_encomienda(request):
    if request.method == 'POST':
        form = EncomiendaForm(request.POST)
        if form.is_valid():
            encomienda = form.save(commit=False)
            encomienda.secretario_registro = request.user
            encomienda.costo_envio = encomienda.ciudad_destino.tarifa_base
            encomienda.save()
            messages.success(request, 'Encomienda registrada exitosamente.')
            return redirect('comprobante_encomienda', pk=encomienda.pk)
    else:
        form = EncomiendaForm()
    return render(request, 'secretario/encomienda_form.html', {'form': form})

@secretario_requerido
def detalle_encomienda(request, pk):
    encomienda = get_object_or_404(Encomienda.objects.prefetch_related('historial'), pk=pk)
    return render(request, 'secretario/encomienda_detalle.html', {
        'encomienda': encomienda,
        'historial': encomienda.historial.all()
    })

@secretario_requerido
def cambiar_estado(request, pk):
    encomienda = get_object_or_404(Encomienda, pk=pk)
    if request.method == 'POST':
        form = CambioEstadoForm(encomienda, request.POST)
        if form.is_valid():
            nuevo_estado = form.cleaned_data['nuevo_estado']
            comentario = form.cleaned_data.get('comentario', '')
            despachador = form.cleaned_data.get('despachador')
            
            try:
                if despachador and nuevo_estado == 'EN_DESPACHO':
                    encomienda.despachador_asignado = despachador
                encomienda.cambiar_estado(nuevo_estado, request.user, comentario)
                encomienda.save()
                messages.success(request, 'Estado actualizado exitosamente.')
                return redirect('detalle_encomienda', pk=pk)
            except Exception as e:
                messages.error(request, f'Error al actualizar el estado: {str(e)}')
    else:
        form = CambioEstadoForm(encomienda)
    return render(request, 'secretario/cambio_estado.html', {'form': form, 'encomienda': encomienda})

@secretario_requerido
def comprobante_encomienda(request, pk):
    encomienda = get_object_or_404(Encomienda, pk=pk)
    return render(request, 'secretario/comprobante.html', {
        'encomienda': encomienda,
        'historial': encomienda.historial.all(),
        'is_pdf': False
    })

@secretario_requerido
def descargar_comprobante_pdf(request, pk):
    if not XHTML2PDF_AVAILABLE:
        return HttpResponse('Generación de PDF no disponible. Por favor instala xhtml2pdf.', status=500)
    encomienda = get_object_or_404(Encomienda, pk=pk)
    context = {
        'encomienda': encomienda,
        'historial': encomienda.historial.all(),
        'is_pdf': True
    }
    pdf = render_to_pdf('secretario/comprobante.html', context)
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="comprobante_{encomienda.numero_guia}.pdf"'
        return response
    return HttpResponse('Error generando PDF', status=500)

@secretario_requerido
def enviar_comprobante_email(request, pk):
    if not XHTML2PDF_AVAILABLE:
        return JsonResponse({'success': False, 'message': 'Generación de PDF no disponible.'})
    
    encomienda = get_object_or_404(Encomienda, pk=pk)
    cliente_email = encomienda.cliente.usuario.email
    if not cliente_email:
        return JsonResponse({'success': False, 'message': 'El cliente no tiene email registrado.'})
    
    pdf = render_to_pdf('secretario/comprobante.html', {
        'encomienda': encomienda,
        'historial': encomienda.historial.all(),
        'is_pdf': True
    })
    
    if not pdf:
         return JsonResponse({'success': False, 'message': 'Error al generar el PDF.'})
         
    email = EmailMessage(
        subject=f'RutaExpres - Comprobante de Envío {encomienda.numero_guia}',
        body=f'Adjunto encontrará el comprobante de su envío con número de guía: {encomienda.numero_guia}',
        to=[cliente_email]
    )
    email.attach(f'comprobante_{encomienda.numero_guia}.pdf', pdf, 'application/pdf')
    email.send()
    
    return JsonResponse({'success': True, 'message': 'Comprobante enviado por email exitosamente.'})

# --- Despachador Views ---
@despachador_requerido
def mis_asignaciones(request):
    encomiendas = Encomienda.objects.filter(despachador_asignado=request.user.perfil).exclude(estado='ENTREGADA')
    return render(request, 'despachador/asignaciones.html', {'encomiendas': encomiendas})

@despachador_requerido
def actualizar_estado_despachador(request, pk):
    encomienda = get_object_or_404(Encomienda, pk=pk)
    if encomienda.despachador_asignado != request.user.perfil:
        return HttpResponseForbidden("No tienes permiso para actualizar esta encomienda.")
        
    if request.method == 'POST':
        form = CambioEstadoForm(encomienda, request.POST)
        if form.is_valid():
            nuevo_estado = form.cleaned_data['nuevo_estado']
            comentario = form.cleaned_data.get('comentario', '')
            
            try:
                encomienda.cambiar_estado(nuevo_estado, request.user, comentario)
                encomienda.save()
                messages.success(request, 'Estado actualizado exitosamente.')
                return redirect('mis_asignaciones')
            except Exception as e:
                messages.error(request, f'Error al actualizar el estado: {str(e)}')
    else:
        form = CambioEstadoForm(encomienda)
    return render(request, 'despachador/actualizar_estado.html', {'form': form, 'encomienda': encomienda})

# --- Cliente Views ---
@cliente_requerido
def mis_envios(request):
    encomiendas = Encomienda.objects.filter(cliente=request.user.perfil)
    return render(request, 'cliente/mis_envios.html', {'encomiendas': encomiendas})

@cliente_requerido
def detalle_envio_cliente(request, pk):
    encomienda = get_object_or_404(Encomienda, pk=pk)
    if encomienda.cliente != request.user.perfil:
        return HttpResponseForbidden("No tienes permiso para ver esta encomienda.")
        
    return render(request, 'cliente/detalle_envio.html', {
        'encomienda': encomienda,
        'historial': encomienda.historial.all()
    })