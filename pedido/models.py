from django.db import models
from django.contrib.auth.models import User
import secrets
import string
from datetime import date
from django.utils import timezone

class PerfilUsuario(models.Model):
    """Extends User with role and extra contact data. OneToOne."""
    ROL_CHOICES = [
        ('CLIENTE', 'Cliente'),
        ('SECRETARIO', 'Secretario'),
        ('DESPACHADOR', 'Despachador'),
    ]
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rol = models.CharField(max_length=15, choices=ROL_CHOICES, default='CLIENTE')
    telefono = models.CharField(max_length=15, blank=True, verbose_name='Teléfono')
    cedula = models.CharField(max_length=13, blank=True, verbose_name='Cédula')
    direccion = models.TextField(blank=True, verbose_name='Dirección')

    class Meta:
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuarios'

    def __str__(self):
        return f"{self.usuario.get_full_name() or self.usuario.username} ({self.get_rol_display()})"


class Ciudad(models.Model):
    """City catalog managed by secretary."""
    nombre = models.CharField(max_length=100, unique=True)
    provincia = models.CharField(max_length=100, blank=True)
    tarifa_base = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Tarifa Base ($)')
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Ciudad'
        verbose_name_plural = 'Ciudades'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.provincia})" if self.provincia else self.nombre


class Encomienda(models.Model):
    """Main entity. Package shipment with state machine."""
    ESTADOS = [
        ('REGISTRADA', 'Registrada'),
        ('RECIBIDA', 'Recibida'),
        ('EN_CLASIFICACION', 'En Clasificación'),
        ('EN_DESPACHO', 'En Despacho'),
        ('EN_TRANSITO', 'En Tránsito'),
        ('LLEGO_A_DESTINO', 'Llegó a Destino'),
        ('EN_ENTREGA', 'En Entrega'),
        ('ENTREGADA', 'Entregada'),
        ('NO_ENTREGADA', 'No Entregada'),
    ]

    # Valid state transitions (state machine)
    TRANSICIONES_VALIDAS = {
        'REGISTRADA': ['RECIBIDA'],
        'RECIBIDA': ['EN_CLASIFICACION'],
        'EN_CLASIFICACION': ['EN_DESPACHO'],
        'EN_DESPACHO': ['EN_TRANSITO'],
        'EN_TRANSITO': ['LLEGO_A_DESTINO'],
        'LLEGO_A_DESTINO': ['EN_ENTREGA'],
        'EN_ENTREGA': ['ENTREGADA', 'NO_ENTREGADA'],
        'ENTREGADA': [],
        'NO_ENTREGADA': ['EN_TRANSITO'],
    }

    # States the secretary can set
    ESTADOS_SECRETARIO = ['REGISTRADA', 'RECIBIDA', 'EN_CLASIFICACION', 'EN_DESPACHO']
    # States the dispatcher can set
    ESTADOS_DESPACHADOR = ['EN_TRANSITO', 'LLEGO_A_DESTINO', 'EN_ENTREGA', 'ENTREGADA', 'NO_ENTREGADA']

    numero_guia = models.CharField(max_length=25, unique=True, editable=False, db_index=True, verbose_name='Número de Guía')
    cliente = models.ForeignKey(PerfilUsuario, on_delete=models.PROTECT, related_name='encomiendas', verbose_name='Cliente (Remitente)')
    ciudad_destino = models.ForeignKey(Ciudad, on_delete=models.PROTECT, related_name='encomiendas', verbose_name='Ciudad Destino')
    nombre_destinatario = models.CharField(max_length=150, verbose_name='Nombre Destinatario')
    telefono_destinatario = models.CharField(max_length=15, verbose_name='Teléfono Destinatario')
    direccion_entrega = models.TextField(verbose_name='Dirección de Entrega')
    descripcion_paquete = models.TextField(verbose_name='Descripción del Paquete')
    peso = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name='Peso (kg)')
    valor_declarado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Valor Declarado ($)')
    costo_envio = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name='Costo de Envío ($)')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='REGISTRADA')
    despachador_asignado = models.ForeignKey(PerfilUsuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='encomiendas_asignadas', verbose_name='Despachador Asignado')
    secretario_registro = models.ForeignKey(User, on_delete=models.PROTECT, related_name='encomiendas_registradas', verbose_name='Registrado por')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_ultima_actualizacion = models.DateTimeField(auto_now=True)
    fecha_entrega = models.DateTimeField(null=True, blank=True)
    observaciones = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Encomienda'
        verbose_name_plural = 'Encomiendas'
        ordering = ['-fecha_registro']

    def __str__(self):
        return f"Guía: {self.numero_guia} - {self.get_estado_display()}"

    def save(self, *args, **kwargs):
        if not self.numero_guia:
            self.numero_guia = Encomienda.generar_numero_guia()
        if not self.costo_envio and self.ciudad_destino_id:
            self.costo_envio = self.ciudad_destino.tarifa_base
        super().save(*args, **kwargs)

    @staticmethod
    def generar_numero_guia():
        """Generate non-sequential, non-guessable tracking number: RE-YYYYMMDD-XXXXXX"""
        chars = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'  # Exclude confusable: 0,O,1,I,L
        while True:
            codigo = ''.join(secrets.choice(chars) for _ in range(6))
            guia = f"RE-{date.today().strftime('%Y%m%d')}-{codigo}"
            if not Encomienda.objects.filter(numero_guia=guia).exists():
                return guia

    def puede_transicionar_a(self, nuevo_estado):
        """Check if transition from current state to new state is valid."""
        return nuevo_estado in self.TRANSICIONES_VALIDAS.get(self.estado, [])

    def cambiar_estado(self, nuevo_estado, usuario, comentario=''):
        """Change state with validation and create history entry."""
        if not self.puede_transicionar_a(nuevo_estado):
            raise ValueError(f"No se puede cambiar de '{self.get_estado_display()}' a '{dict(self.ESTADOS).get(nuevo_estado, nuevo_estado)}'")
        self.estado = nuevo_estado
        if nuevo_estado == 'ENTREGADA':
            self.fecha_entrega = timezone.now()
        self.save()
        HistorialEstado.objects.create(
            encomienda=self,
            estado=nuevo_estado,
            comentario=comentario,
            usuario=usuario
        )
        return True

    def get_estados_siguientes(self):
        """Return list of valid next states."""
        return self.TRANSICIONES_VALIDAS.get(self.estado, [])


class HistorialEstado(models.Model):
    """Audit log for state changes. Creates timeline for tracking."""
    encomienda = models.ForeignKey(Encomienda, on_delete=models.CASCADE, related_name='historial')
    estado = models.CharField(max_length=20, choices=Encomienda.ESTADOS)
    fecha = models.DateTimeField(auto_now_add=True)
    comentario = models.TextField(blank=True)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)

    class Meta:
        verbose_name = 'Historial de Estado'
        verbose_name_plural = 'Historial de Estados'
        ordering = ['fecha']

    def __str__(self):
        return f"{self.encomienda.numero_guia} → {self.get_estado_display()} ({self.fecha.strftime('%d/%m/%Y %H:%M')})"
