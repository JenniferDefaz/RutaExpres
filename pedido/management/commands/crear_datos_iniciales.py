from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from pedido.models import Ciudad, PerfilUsuario

class Command(BaseCommand):
    help = 'Creates initial data for the system'

    def handle(self, *args, **kwargs):
        # 1. Cities
        ciudades_data = [
            {'nombre': 'Quito', 'provincia': 'Pichincha', 'tarifa_base': 5.00},
            {'nombre': 'Guayaquil', 'provincia': 'Guayas', 'tarifa_base': 5.00},
            {'nombre': 'Cuenca', 'provincia': 'Azuay', 'tarifa_base': 6.50},
            {'nombre': 'Ambato', 'provincia': 'Tungurahua', 'tarifa_base': 5.50},
            {'nombre': 'Loja', 'provincia': 'Loja', 'tarifa_base': 8.00},
            {'nombre': 'Manta', 'provincia': 'Manabí', 'tarifa_base': 7.00},
            {'nombre': 'Riobamba', 'provincia': 'Chimborazo', 'tarifa_base': 6.00},
            {'nombre': 'Esmeraldas', 'provincia': 'Esmeraldas', 'tarifa_base': 9.00},
            {'nombre': 'Ibarra', 'provincia': 'Imbabura', 'tarifa_base': 6.00},
            {'nombre': 'Santo Domingo', 'provincia': 'Santo Domingo', 'tarifa_base': 5.50},
            {'nombre': 'Machala', 'provincia': 'El Oro', 'tarifa_base': 7.50},
            {'nombre': 'Portoviejo', 'provincia': 'Manabí', 'tarifa_base': 7.00},
            {'nombre': 'Babahoyo', 'provincia': 'Los Ríos', 'tarifa_base': 6.00},
            {'nombre': 'Tulcán', 'provincia': 'Carchi', 'tarifa_base': 8.50},
            {'nombre': 'Latacunga', 'provincia': 'Cotopaxi', 'tarifa_base': 5.50},
        ]
        
        for data in ciudades_data:
            Ciudad.objects.get_or_create(
                nombre=data['nombre'],
                defaults={'provincia': data['provincia'], 'tarifa_base': data['tarifa_base']}
            )
        self.stdout.write(self.style.SUCCESS('Cities created or updated successfully'))

        # 2. Secretary user
        user_sec, created_sec = User.objects.get_or_create(
            username='secretario1',
            defaults={'first_name': 'Admin', 'last_name': 'Secretario'}
        )
        if created_sec:
            user_sec.set_password('Ruta2026!')
            user_sec.save()
            PerfilUsuario.objects.get_or_create(usuario=user_sec, defaults={'rol': 'SECRETARIO'})
        self.stdout.write(self.style.SUCCESS('Secretary user ensured'))

        # 3. Dispatcher user
        user_desp, created_desp = User.objects.get_or_create(
            username='despachador1',
            defaults={'first_name': 'Carlos', 'last_name': 'Despachador'}
        )
        if created_desp:
            user_desp.set_password('Ruta2026!')
            user_desp.save()
            PerfilUsuario.objects.get_or_create(usuario=user_desp, defaults={'rol': 'DESPACHADOR'})
        self.stdout.write(self.style.SUCCESS('Dispatcher user ensured'))

        # 4. Client user
        user_cli, created_cli = User.objects.get_or_create(
            username='cliente1',
            defaults={'first_name': 'María', 'last_name': 'García'}
        )
        if created_cli:
            user_cli.set_password('Ruta2026!')
            user_cli.save()
            PerfilUsuario.objects.get_or_create(
                usuario=user_cli,
                defaults={'rol': 'CLIENTE', 'telefono': '0991234567', 'cedula': '1234567890'}
            )
        self.stdout.write(self.style.SUCCESS('Client user ensured'))

        self.stdout.write(self.style.SUCCESS('Initial data creation complete'))
