from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def badge_estado(estado):
    """Return Bootstrap badge HTML for a shipment state."""
    colores = {
        'REGISTRADA': 'secondary',
        'RECIBIDA': 'info',
        'EN_CLASIFICACION': 'primary',
        'EN_DESPACHO': 'warning',
        'EN_TRANSITO': 'dark',
        'LLEGO_A_DESTINO': 'primary',
        'EN_ENTREGA': 'warning',
        'ENTREGADA': 'success',
        'NO_ENTREGADA': 'danger',
    }
    labels = {
        'REGISTRADA': 'Registrada',
        'RECIBIDA': 'Recibida',
        'EN_CLASIFICACION': 'En Clasificación',
        'EN_DESPACHO': 'En Despacho',
        'EN_TRANSITO': 'En Tránsito',
        'LLEGO_A_DESTINO': 'Llegó a Destino',
        'EN_ENTREGA': 'En Entrega',
        'ENTREGADA': 'Entregada',
        'NO_ENTREGADA': 'No Entregada',
    }
    color = colores.get(estado, 'secondary')
    label = labels.get(estado, estado)
    return mark_safe(f'<span class="badge bg-{color}">{label}</span>')

@register.filter
def has_role(user, role):
    """Check if user has a specific role. Usage: {% if user|has_role:'SECRETARIO' %}"""
    if hasattr(user, 'perfil'):
        return user.perfil.rol == role
    return False
