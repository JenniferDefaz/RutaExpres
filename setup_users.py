import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'RutaExpres.settings')
django.setup()

from django.contrib.auth.models import User, Group
from pedido.models import Cliente

groups = ['Secretario', 'Despachador', 'Cliente']
for g in groups:
    Group.objects.get_or_create(name=g)

users_data = [
    ('secretario1', 'Ruta2026!', 'Secretario', True),
    ('despachador1', 'Ruta2026!', 'Despachador', True),
    ('cliente1', 'Ruta2026!', 'Cliente', False)
]

for username, password, group_name, is_staff in users_data:
    user, created = User.objects.get_or_create(username=username)
    if created:
        user.set_password(password)
        user.is_staff = is_staff
        user.save()
        
    group = Group.objects.get(name=group_name)
    user.groups.add(group)
    
    if group_name == 'Cliente':
        # Create a Cliente record for this user if it doesn't exist
        cliente, c_created = Cliente.objects.get_or_create(user=user, defaults={
            'nombre': 'Cliente',
            'apellido': 'Uno',
            'email': f'{username}@example.com',
            'telefono': '0999999999',
            'direccion': 'Direccion Cliente 1'
        })
        
print("Usuarios y roles configurados con éxito.")
