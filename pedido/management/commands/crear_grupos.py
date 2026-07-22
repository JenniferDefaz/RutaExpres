"""
Management command: crear_grupos
Uso: python manage.py crear_grupos

Crea los grupos de usuario necesarios para RutaExpres:
  - Cliente    → clientes registrados por el formulario web
  - Secretario → personal interno que gestiona pedidos
  - Despachador→ personal de despacho que actualiza estados

También puede crear un usuario despachador de ejemplo si se pasa --demo.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, User


GRUPOS = ['Cliente', 'Secretario', 'Despachador']


class Command(BaseCommand):
    help = 'Crea los grupos de usuario requeridos por RutaExpres.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--demo',
            action='store_true',
            help='Crea además un usuario despachador de prueba (usuario: despachador@rutaexpres.com, clave: Despacho2024!)',
        )

    def handle(self, *args, **options):
        for nombre in GRUPOS:
            grupo, creado = Group.objects.get_or_create(name=nombre)
            if creado:
                self.stdout.write(self.style.SUCCESS(f'  ✔ Grupo "{nombre}" creado.'))
            else:
                self.stdout.write(f'  · Grupo "{nombre}" ya existía.')

        if options['demo']:
            email_demo = 'despachador@rutaexpres.com'
            if not User.objects.filter(username=email_demo).exists():
                user = User.objects.create_user(
                    username=email_demo,
                    email=email_demo,
                    password='Despacho2024!',
                    first_name='Despachador',
                    last_name='Demo',
                )
                grupo_desp = Group.objects.get(name='Despachador')
                user.groups.add(grupo_desp)
                self.stdout.write(self.style.SUCCESS(
                    f'\n  ✔ Usuario despachador demo creado:\n'
                    f'     Email   : {email_demo}\n'
                    f'     Contraseña: Despacho2024!\n'
                ))
            else:
                self.stdout.write(f'\n  · Usuario despachador demo ya existía.')

        self.stdout.write(self.style.SUCCESS('\n¡Grupos listos!'))
