from django.apps import AppConfig

class PedidoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pedido'
    verbose_name = 'Gestión de Encomiendas'

    def ready(self):
        import pedido.signals  # noqa: F401
