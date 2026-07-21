from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import PerfilUsuario, Ciudad, Encomienda

class LoginForm(AuthenticationForm):
    """Custom login form with Bootstrap styling."""
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Usuario', 'id': 'id_username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña', 'id': 'id_password'})
    )

class ClienteForm(forms.Form):
    """Form for secretary to register a new client. Creates User + PerfilUsuario."""
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de usuario', 'id': 'id_username'}))
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombres', 'id': 'id_first_name'}), label='Nombres')
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellidos', 'id': 'id_last_name'}), label='Apellidos')
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com', 'id': 'id_email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña', 'id': 'id_password'}), label='Contraseña')
    telefono = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0999999999', 'id': 'id_telefono'}), label='Teléfono')
    cedula = forms.CharField(max_length=13, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '1234567890', 'id': 'id_cedula'}), label='Cédula')
    direccion = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Dirección habitual', 'id': 'id_direccion'}), label='Dirección')

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Este nombre de usuario ya está en uso.')
        return username

    def save(self):
        data = self.cleaned_data
        user = User.objects.create_user(
            username=data['username'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data.get('email', '')
        )
        perfil = PerfilUsuario.objects.create(
            usuario=user,
            rol='CLIENTE',
            telefono=data.get('telefono', ''),
            cedula=data.get('cedula', ''),
            direccion=data.get('direccion', '')
        )
        return user, perfil

class ClienteEditForm(forms.Form):
    """Form for editing existing client (no password change)."""
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_first_name'}), label='Nombres')
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_last_name'}), label='Apellidos')
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control', 'id': 'id_email'}))
    telefono = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_telefono'}), label='Teléfono')
    cedula = forms.CharField(max_length=13, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_cedula'}), label='Cédula')
    direccion = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'id': 'id_direccion'}), label='Dirección')

class CiudadForm(forms.ModelForm):
    class Meta:
        model = Ciudad
        fields = ['nombre', 'provincia', 'tarifa_base', 'activa']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_nombre'}),
            'provincia': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_provincia'}),
            'tarifa_base': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'id': 'id_tarifa_base'}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_activa'}),
        }

class EncomiendaForm(forms.ModelForm):
    """Form for registering a new shipment."""
    class Meta:
        model = Encomienda
        fields = ['cliente', 'ciudad_destino', 'nombre_destinatario', 'telefono_destinatario',
                  'direccion_entrega', 'descripcion_paquete', 'peso', 'valor_declarado', 'observaciones']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select', 'id': 'id_cliente'}),
            'ciudad_destino': forms.Select(attrs={'class': 'form-select', 'id': 'id_ciudad_destino'}),
            'nombre_destinatario': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_nombre_destinatario'}),
            'telefono_destinatario': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_telefono_destinatario'}),
            'direccion_entrega': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'id': 'id_direccion_entrega'}),
            'descripcion_paquete': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'id': 'id_descripcion_paquete'}),
            'peso': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'id': 'id_peso'}),
            'valor_declarado': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'id': 'id_valor_declarado'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'id': 'id_observaciones'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show clients (rol=CLIENTE)
        self.fields['cliente'].queryset = PerfilUsuario.objects.filter(rol='CLIENTE').select_related('usuario')
        # Only show active cities
        self.fields['ciudad_destino'].queryset = Ciudad.objects.filter(activa=True)

class CambioEstadoForm(forms.Form):
    """Form for changing shipment state."""
    nuevo_estado = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_nuevo_estado'}),
        label='Nuevo Estado'
    )
    comentario = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'id': 'id_comentario', 'placeholder': 'Comentario opcional...'}),
        label='Comentario'
    )
    despachador = forms.ModelChoiceField(
        queryset=PerfilUsuario.objects.filter(rol='DESPACHADOR'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_despachador'}),
        label='Asignar Despachador'
    )

    def __init__(self, encomienda, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show valid next states
        estados_siguientes = encomienda.get_estados_siguientes()
        self.fields['nuevo_estado'].choices = [
            (e, dict(Encomienda.ESTADOS).get(e, e)) for e in estados_siguientes
        ]
        # Show despachador field only when transitioning to EN_DESPACHO
        if encomienda.estado != 'EN_CLASIFICACION':
            del self.fields['despachador']
