from django import forms
from .models import Cliente, Pedido


class ClienteForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mínimo 8 caracteres',
        }),
        label='Contraseña',
        min_length=8,
        error_messages={'min_length': 'La contraseña debe tener al menos 8 caracteres.'},
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Repite tu contraseña',
        }),
        label='Confirmar contraseña',
    )

    class Meta:
        model = Cliente
        fields = ['nombre', 'apellido', 'email', 'telefono', 'direccion']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese el nombre',
            }),
            'apellido': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese el apellido',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'ejemplo@correo.com',
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+593 99 999 9999',
            }),
            'direccion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ingrese la dirección completa',
            }),
        }

    def clean_nombre(self):
        valor = self.cleaned_data.get('nombre', '').strip()
        if not valor:
            raise forms.ValidationError('El nombre no puede estar vacío.')
        if len(valor) < 2:
            raise forms.ValidationError('El nombre debe tener al menos 2 caracteres.')
        return valor

    def clean_apellido(self):
        valor = self.cleaned_data.get('apellido', '').strip()
        if not valor:
            raise forms.ValidationError('El apellido no puede estar vacío.')
        if len(valor) < 2:
            raise forms.ValidationError('El apellido debe tener al menos 2 caracteres.')
        return valor

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        # Al editar, excluir el propio registro
        qs = Cliente.objects.filter(email=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Ya existe un cliente registrado con este correo electrónico.')
        return email

    def clean_direccion(self):
        valor = self.cleaned_data.get('direccion', '').strip()
        if not valor:
            raise forms.ValidationError('La dirección no puede estar vacía.')
        return valor

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        password_confirm = cleaned.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', 'Las contraseñas no coinciden.')
        return cleaned


class PedidoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user and hasattr(self.user, 'cliente') and not self.user.groups.filter(name__in=['Secretario', 'Despachador']).exists() and not self.user.is_staff:
            if 'cliente' in self.fields:
                del self.fields['cliente']
            if 'estado' in self.fields:
                del self.fields['estado']

    class Meta:
        model = Pedido
        fields = ['cliente', 'destinatario', 'tipo_servicio', 'origen', 'destino',
                  'descripcion_carga', 'peso_kg', 'foto_producto',
                  'metodo_pago', 'comprobante_pago', 'estado']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'destinatario': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de quien recibe',
            }),
            'tipo_servicio': forms.Select(attrs={'class': 'form-select'}),
            'origen': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ciudad / País de origen',
            }),
            'destino': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ciudad / País de destino',
            }),
            'descripcion_carga': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describa el contenido del envío',
            }),
            'peso_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'min': '0.01',
                'step': '0.01',
                'id': 'id_peso_kg',
            }),
            'foto_producto': forms.FileInput(attrs={'class': 'form-control'}),
            'metodo_pago': forms.Select(attrs={'class': 'form-select'}),
            'comprobante_pago': forms.FileInput(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_peso_kg(self):
        peso = self.cleaned_data.get('peso_kg')
        if peso is not None and peso <= 0:
            raise forms.ValidationError('El peso debe ser mayor que cero.')
        return peso

    def clean_origen(self):
        valor = self.cleaned_data.get('origen', '').strip()
        if not valor:
            raise forms.ValidationError('El origen no puede estar vacío.')
        return valor

    def clean_destino(self):
        valor = self.cleaned_data.get('destino', '').strip()
        if not valor:
            raise forms.ValidationError('El destino no puede estar vacío.')
        return valor

    def clean(self):
        cleaned = super().clean()
        origen = cleaned.get('origen', '').strip().lower()
        destino = cleaned.get('destino', '').strip().lower()
        if origen and destino and origen == destino:
            raise forms.ValidationError('El origen y el destino no pueden ser iguales.')
        return cleaned


class BuscarPedidoForm(forms.Form):
    numero_tracking = forms.CharField(
        max_length=20,
        label='Número de tracking',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: RE-A1B2C3D4',
        })
    )

    def clean_numero_tracking(self):
        valor = self.cleaned_data.get('numero_tracking', '').strip().upper()
        if not valor:
            raise forms.ValidationError('Ingrese un número de tracking.')
        return valor
