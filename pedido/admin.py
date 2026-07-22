from django.contrib import admin
from .models import Cliente, Pedido


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido', 'email', 'telefono', 'fecha_registro')
    search_fields = ('nombre', 'apellido', 'email')
    list_filter = ('fecha_registro',)
    ordering = ('-fecha_registro',)


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('numero_tracking', 'cliente', 'tipo_servicio', 'origen', 'destino', 'estado', 'fecha_creacion')
    search_fields = ('numero_tracking', 'cliente__nombre', 'cliente__apellido', 'cliente__email')
    list_filter = ('estado', 'tipo_servicio', 'fecha_creacion')
    readonly_fields = ('numero_tracking', 'fecha_creacion', 'fecha_actualizacion')
    ordering = ('-fecha_creacion',)
