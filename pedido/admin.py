from django.contrib import admin
from .models import PerfilUsuario, Ciudad, Encomienda, HistorialEstado

class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'rol', 'telefono', 'cedula')
    list_filter = ('rol',)
    search_fields = ('usuario__username', 'cedula')

class CiudadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'provincia', 'tarifa_base', 'activa')
    list_filter = ('activa', 'provincia')

class HistorialEstadoInline(admin.TabularInline):
    model = HistorialEstado
    extra = 0
    readonly_fields = ('estado', 'fecha', 'comentario', 'usuario')

    def has_add_permission(self, request, obj=None):
        return False

class EncomiendaAdmin(admin.ModelAdmin):
    list_display = ('numero_guia', 'cliente', 'ciudad_destino', 'estado', 'fecha_registro')
    list_filter = ('estado', 'fecha_registro')
    search_fields = ('numero_guia',)
    inlines = [HistorialEstadoInline]

admin.site.register(PerfilUsuario, PerfilUsuarioAdmin)
admin.site.register(Ciudad, CiudadAdmin)
admin.site.register(Encomienda, EncomiendaAdmin)
