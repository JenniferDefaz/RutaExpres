import uuid
from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import User


def generar_tracking():
    return 'RE-' + uuid.uuid4().hex[:8].upper()


class Cliente(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Usuario asociado')
    nombre = models.CharField(max_length=100, verbose_name='Nombre')
    apellido = models.CharField(max_length=100, verbose_name='Apellido')
    email = models.EmailField(unique=True, verbose_name='Correo electrónico')
    telefono = models.CharField(
        max_length=20,
        verbose_name='Teléfono',
        validators=[RegexValidator(
            regex=r'^\+?1?\d{7,15}$',
            message='Ingrese un número de teléfono válido (7-15 dígitos).'
        )]
    )
    direccion = models.TextField(verbose_name='Dirección')
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de registro')

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['-fecha_registro']

    def __str__(self):
        return f'{self.nombre} {self.apellido} — {self.email}'


class Pedido(models.Model):
    TIPO_SERVICIO_CHOICES = [
        ('aereo', 'Aéreo'),
        ('maritimo', 'Marítimo'),
        ('terrestre', 'Terrestre'),
        ('tren', 'Tren'),
    ]
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_transito', 'En tránsito'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='pedidos',
        verbose_name='Cliente'
    )
    numero_tracking = models.CharField(
        max_length=20,
        unique=True,
        default=generar_tracking,
        editable=False,
        verbose_name='Número de tracking'
    )
    destinatario = models.CharField(
        max_length=100, 
        verbose_name='Nombre del destinatario',
        default='Desconocido'
    )
    tipo_servicio = models.CharField(
        max_length=20,
        choices=TIPO_SERVICIO_CHOICES,
        verbose_name='Tipo de servicio'
    )
    origen = models.CharField(max_length=200, verbose_name='Origen')
    destino = models.CharField(max_length=200, verbose_name='Destino')
    descripcion_carga = models.TextField(verbose_name='Descripción de la carga')
    peso_kg = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name='Peso (kg)'
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente',
        verbose_name='Estado'
    )
    foto_producto = models.FileField(
        upload_to='productos/',
        null=True, blank=True,
        verbose_name='Foto del producto'
    )
    # ─── Cotización y Pago ────────────────────────────────────
    precio_envio = models.DecimalField(
        max_digits=8, decimal_places=2,
        null=True, blank=True,
        verbose_name='Precio de envío ($)'
    )
    METODO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo en oficina'),
        ('transferencia', 'Transferencia bancaria'),
        ('tarjeta', 'Tarjeta de crédito/débito'),
    ]
    metodo_pago = models.CharField(
        max_length=20,
        choices=METODO_PAGO_CHOICES,
        null=True, blank=True,
        verbose_name='Método de pago'
    )
    comprobante_pago = models.FileField(
        upload_to='comprobantes/',
        null=True, blank=True,
        verbose_name='Comprobante de pago'
    )
    pago_confirmado = models.BooleanField(default=False, verbose_name='Pago confirmado')
    despachador = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='pedidos_asignados',
        verbose_name='Despachador asignado',
        limit_choices_to={'groups__name': 'Despachador'}
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name='Última actualización')

    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f'{self.numero_tracking} — {self.cliente} [{self.get_estado_display()}]'
