from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Encomienda, HistorialEstado

@receiver(post_save, sender=Encomienda)
def crear_historial_inicial(sender, instance, created, **kwargs):
    """When a new Encomienda is created, add initial REGISTRADA history entry."""
    if created:
        HistorialEstado.objects.create(
            encomienda=instance,
            estado='REGISTRADA',
            comentario='Encomienda registrada en el sistema',
            usuario=instance.secretario_registro
        )
