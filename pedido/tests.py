"""
Tests para la aplicación pedido — RutaExpres.
Cubre modelos, formularios, vistas y correos electrónicos.

Ejecutar: python manage.py test pedido
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.core import mail

from .models import Cliente, Pedido
from .forms import ClienteForm, PedidoForm, BuscarPedidoForm


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def crear_grupo(nombre):
    grupo, _ = Group.objects.get_or_create(name=nombre)
    return grupo


def crear_usuario_cliente(email='test@ejemplo.com', password='Clave1234!'):
    """Crea un User + Cliente y los vincula."""
    user = User.objects.create_user(
        username=email, email=email, password=password,
        first_name='Ana', last_name='García',
    )
    grupo = crear_grupo('Cliente')
    user.groups.add(grupo)
    cliente = Cliente.objects.create(
        user=user,
        nombre='Ana',
        apellido='García',
        email=email,
        telefono='0991234567',
        direccion='Calle Falsa 123, Quito',
    )
    return user, cliente


def crear_usuario_despachador(email='despacho@ejemplo.com', password='Despacho1!'):
    user = User.objects.create_user(
        username=email, email=email, password=password,
        first_name='Carlos', last_name='Pérez',
    )
    grupo = crear_grupo('Despachador')
    user.groups.add(grupo)
    return user


def crear_pedido(cliente, estado='pendiente'):
    return Pedido.objects.create(
        cliente=cliente,
        destinatario='Juan Receptor',
        tipo_servicio='terrestre',
        origen='Quito',
        destino='Guayaquil',
        descripcion_carga='Caja de libros',
        peso_kg='2.50',
        estado=estado,
    )


# ─────────────────────────────────────────────────────────────
# Tests de Modelos
# ─────────────────────────────────────────────────────────────

class ClienteModelTest(TestCase):

    def setUp(self):
        _, self.cliente = crear_usuario_cliente()

    def test_str_retorna_nombre_completo_y_email(self):
        resultado = str(self.cliente)
        self.assertIn('Ana', resultado)
        self.assertIn('García', resultado)
        self.assertIn(self.cliente.email, resultado)

    def test_campos_obligatorios_guardados(self):
        self.assertEqual(self.cliente.nombre, 'Ana')
        self.assertEqual(self.cliente.apellido, 'García')
        self.assertIsNotNone(self.cliente.fecha_registro)

    def test_email_es_unico(self):
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Cliente.objects.create(
                nombre='Otro',
                apellido='Usuario',
                email='test@ejemplo.com',   # duplicado
                telefono='0991111111',
                direccion='Otra dirección',
            )


class PedidoModelTest(TestCase):

    def setUp(self):
        _, self.cliente = crear_usuario_cliente()
        self.pedido = crear_pedido(self.cliente)

    def test_tracking_autogenerado_con_prefijo_RE(self):
        self.assertTrue(self.pedido.numero_tracking.startswith('RE-'))

    def test_tracking_longitud_correcta(self):
        # RE- + 8 hex chars = 11 caracteres
        self.assertEqual(len(self.pedido.numero_tracking), 11)

    def test_tracking_es_unico(self):
        pedido2 = crear_pedido(self.cliente)
        self.assertNotEqual(self.pedido.numero_tracking, pedido2.numero_tracking)

    def test_estado_por_defecto_es_pendiente(self):
        self.assertEqual(self.pedido.estado, 'pendiente')

    def test_str_contiene_tracking(self):
        self.assertIn(self.pedido.numero_tracking, str(self.pedido))

    def test_fecha_creacion_autogenerada(self):
        self.assertIsNotNone(self.pedido.fecha_creacion)


# ─────────────────────────────────────────────────────────────
# Tests de Formularios
# ─────────────────────────────────────────────────────────────

class ClienteFormTest(TestCase):

    def _datos_validos(self, **kwargs):
        datos = {
            'nombre': 'María',
            'apellido': 'López',
            'email': 'maria@ejemplo.com',
            'password': 'Segura1234!',
            'password_confirm': 'Segura1234!',
            'telefono': '0998765432',
            'direccion': 'Av. Amazonas 456, Quito',
        }
        datos.update(kwargs)
        return datos

    def test_formulario_valido_con_datos_correctos(self):
        form = ClienteForm(data=self._datos_validos())
        self.assertTrue(form.is_valid(), form.errors)

    def test_rechaza_email_duplicado(self):
        _, _ = crear_usuario_cliente(email='duplicado@ejemplo.com')
        form = ClienteForm(data=self._datos_validos(email='duplicado@ejemplo.com'))
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_rechaza_passwords_que_no_coinciden(self):
        form = ClienteForm(data=self._datos_validos(
            password='Segura1234!',
            password_confirm='OtraClave99!'
        ))
        self.assertFalse(form.is_valid())
        self.assertIn('password_confirm', form.errors)

    def test_rechaza_password_muy_corta(self):
        form = ClienteForm(data=self._datos_validos(
            password='abc',
            password_confirm='abc',
        ))
        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)

    def test_rechaza_nombre_muy_corto(self):
        form = ClienteForm(data=self._datos_validos(nombre='A'))
        self.assertFalse(form.is_valid())
        self.assertIn('nombre', form.errors)

    def test_rechaza_email_invalido(self):
        form = ClienteForm(data=self._datos_validos(email='no-es-email'))
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)


class PedidoFormTest(TestCase):

    def setUp(self):
        self.user, self.cliente = crear_usuario_cliente()

    def _datos_validos(self, **kwargs):
        datos = {
            'destinatario': 'Juan Receptor',
            'tipo_servicio': 'terrestre',
            'origen': 'Quito',
            'destino': 'Guayaquil',
            'descripcion_carga': 'Paquete de ropa',
            'peso_kg': '3.00',
        }
        datos.update(kwargs)
        return datos

    def test_formulario_valido_para_cliente(self):
        form = PedidoForm(data=self._datos_validos(), user=self.user)
        self.assertTrue(form.is_valid(), form.errors)

    def test_rechaza_peso_cero(self):
        form = PedidoForm(data=self._datos_validos(peso_kg='0'), user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('peso_kg', form.errors)

    def test_rechaza_peso_negativo(self):
        form = PedidoForm(data=self._datos_validos(peso_kg='-5'), user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('peso_kg', form.errors)

    def test_rechaza_origen_igual_a_destino(self):
        form = PedidoForm(data=self._datos_validos(origen='Quito', destino='Quito'), user=self.user)
        self.assertFalse(form.is_valid())

    def test_cliente_normal_no_ve_campo_cliente_ni_estado(self):
        form = PedidoForm(user=self.user)
        self.assertNotIn('cliente', form.fields)
        self.assertNotIn('estado', form.fields)

    def test_despachador_ve_campo_cliente_y_estado(self):
        despacho = crear_usuario_despachador()
        form = PedidoForm(user=despacho)
        self.assertIn('cliente', form.fields)
        self.assertIn('estado', form.fields)


class BuscarPedidoFormTest(TestCase):

    def test_valido_con_tracking_correcto(self):
        form = BuscarPedidoForm(data={'numero_tracking': 'RE-ABCD1234'})
        self.assertTrue(form.is_valid())

    def test_normaliza_a_mayusculas(self):
        form = BuscarPedidoForm(data={'numero_tracking': 're-abcd1234'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['numero_tracking'], 'RE-ABCD1234')

    def test_rechaza_vacio(self):
        form = BuscarPedidoForm(data={'numero_tracking': ''})
        self.assertFalse(form.is_valid())


# ─────────────────────────────────────────────────────────────
# Tests de Vistas
# ─────────────────────────────────────────────────────────────

class VistaInicioTest(TestCase):

    def test_inicio_retorna_200(self):
        response = self.client.get(reverse('inicio'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'inicio.html')


class VistaRegistrarClienteTest(TestCase):

    def test_get_retorna_200_y_usa_plantilla(self):
        response = self.client.get(reverse('registrar_cliente'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registro_cliente.html')

    def test_post_valido_crea_usuario_y_redirige(self):
        response = self.client.post(reverse('registrar_cliente'), {
            'nombre': 'Laura',
            'apellido': 'Torres',
            'email': 'laura@ejemplo.com',
            'password': 'LauraPass1!',
            'password_confirm': 'LauraPass1!',
            'telefono': '0991234567',
            'direccion': 'Calle 10, Cuenca',
        })
        self.assertRedirects(response, reverse('iniciar_sesion'))
        self.assertTrue(User.objects.filter(username='laura@ejemplo.com').exists())
        self.assertTrue(Cliente.objects.filter(email='laura@ejemplo.com').exists())

    def test_post_invalido_no_crea_usuario(self):
        response = self.client.post(reverse('registrar_cliente'), {
            'nombre': 'L',  # muy corto
            'apellido': 'Torres',
            'email': 'laura2@ejemplo.com',
            'password': 'LauraPass1!',
            'password_confirm': 'LauraPass1!',
            'telefono': '0991234567',
            'direccion': 'Calle 10',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='laura2@ejemplo.com').exists())


class VistaLoginTest(TestCase):

    def setUp(self):
        self.user, self.cliente = crear_usuario_cliente(
            email='login@ejemplo.com', password='Login1234!'
        )

    def test_get_retorna_200(self):
        response = self.client.get(reverse('iniciar_sesion'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')

    def test_login_correcto_con_email_redirige(self):
        response = self.client.post(reverse('iniciar_sesion'), {
            'username': 'login@ejemplo.com',
            'password': 'Login1234!',
        })
        self.assertRedirects(response, reverse('panel_cliente'))

    def test_login_incorrecto_muestra_error(self):
        response = self.client.post(reverse('iniciar_sesion'), {
            'username': 'login@ejemplo.com',
            'password': 'ClaveIncorrecta',
        })
        self.assertEqual(response.status_code, 200)

    def test_despachador_redirige_a_lista(self):
        despacho = crear_usuario_despachador(
            email='despacho2@ejemplo.com', password='Desp1234!'
        )
        response = self.client.post(reverse('iniciar_sesion'), {
            'username': 'despacho2@ejemplo.com',
            'password': 'Desp1234!',
        })
        self.assertRedirects(response, reverse('lista_pedidos'))


class VistaRastrearPedidoTest(TestCase):

    def test_get_retorna_200(self):
        response = self.client.get(reverse('rastrear_pedido'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rastrear_pedido.html')

    def test_post_tracking_valido_muestra_pedido(self):
        _, cliente = crear_usuario_cliente()
        pedido = crear_pedido(cliente)
        response = self.client.post(reverse('rastrear_pedido'), {
            'numero_tracking': pedido.numero_tracking,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, pedido.numero_tracking)

    def test_post_tracking_inexistente_muestra_error(self):
        response = self.client.post(reverse('rastrear_pedido'), {
            'numero_tracking': 'RE-XXXXXXXX',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['pedido'])


class VistaDetallePedidoTest(TestCase):

    def setUp(self):
        _, self.cliente = crear_usuario_cliente()
        self.pedido = crear_pedido(self.cliente)

    def test_retorna_200_con_tracking_valido(self):
        response = self.client.get(
            reverse('detalle_pedido', args=[self.pedido.numero_tracking])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'detalle_pedido.html')
        self.assertContains(response, self.pedido.numero_tracking)

    def test_retorna_404_con_tracking_inexistente(self):
        response = self.client.get(
            reverse('detalle_pedido', args=['RE-00000000'])
        )
        self.assertEqual(response.status_code, 404)


class VistaListaPedidosTest(TestCase):

    def setUp(self):
        self.user_cliente, self.cliente = crear_usuario_cliente()
        self.despacho = crear_usuario_despachador()

    def test_redirige_a_login_si_no_autenticado(self):
        response = self.client.get(reverse('lista_pedidos'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])

    def test_redirige_a_panel_si_es_cliente_normal(self):
        self.client.force_login(self.user_cliente)
        response = self.client.get(reverse('lista_pedidos'))
        self.assertRedirects(response, reverse('panel_cliente'))

    def test_despachador_accede_correctamente(self):
        self.client.force_login(self.despacho)
        response = self.client.get(reverse('lista_pedidos'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'lista_pedidos.html')

    def test_despachador_puede_cambiar_estado(self):
        pedido = crear_pedido(self.cliente)
        self.client.force_login(self.despacho)
        response = self.client.post(reverse('lista_pedidos'), {
            'pedido_id': pedido.pk,
            'nuevo_estado': 'en_transito',
        })
        self.assertRedirects(response, reverse('lista_pedidos'))
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, 'en_transito')


class VistaRegistrarPedidoTest(TestCase):

    def setUp(self):
        self.user, self.cliente = crear_usuario_cliente()

    def test_redirige_a_login_si_no_autenticado(self):
        response = self.client.get(reverse('registrar_pedido'))
        self.assertRedirects(response, '/login/?next=/pedidos/registrar/')

    def test_get_retorna_200_para_cliente(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('registrar_pedido'))
        self.assertEqual(response.status_code, 200)

    def test_post_valido_crea_pedido_y_redirige(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('registrar_pedido'), {
            'destinatario': 'Juan Receptor',
            'tipo_servicio': 'aereo',
            'origen': 'Quito',
            'destino': 'Guayaquil',
            'descripcion_carga': 'Electrónica',
            'peso_kg': '1.50',
        })
        self.assertEqual(Pedido.objects.filter(cliente=self.cliente).count(), 1)
        pedido = Pedido.objects.get(cliente=self.cliente)
        self.assertRedirects(
            response,
            reverse('detalle_pedido', args=[pedido.numero_tracking])
        )


# ─────────────────────────────────────────────────────────────
# Tests de Correos Electrónicos
# ─────────────────────────────────────────────────────────────

class CorreoBienvenidaTest(TestCase):

    def test_correo_bienvenida_enviado_al_registrarse(self):
        self.client.post(reverse('registrar_cliente'), {
            'nombre': 'Pedro',
            'apellido': 'Ramírez',
            'email': 'pedro@ejemplo.com',
            'password': 'Pedro1234!',
            'password_confirm': 'Pedro1234!',
            'telefono': '0991234567',
            'direccion': 'Av. Principal, Loja',
        })
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('pedro@ejemplo.com', mail.outbox[0].to)
        self.assertIn('Bienvenido', mail.outbox[0].subject)

    def test_correo_bienvenida_contiene_datos_cliente(self):
        self.client.post(reverse('registrar_cliente'), {
            'nombre': 'Sofía',
            'apellido': 'Vega',
            'email': 'sofia@ejemplo.com',
            'password': 'Sofia1234!',
            'password_confirm': 'Sofia1234!',
            'telefono': '0991234567',
            'direccion': 'Calle 5, Ambato',
        })
        cuerpo = mail.outbox[0].body
        self.assertIn('Sofía', cuerpo)
        self.assertIn('sofia@ejemplo.com', cuerpo)


class CorreoConfirmacionPedidoTest(TestCase):

    def setUp(self):
        self.user, self.cliente = crear_usuario_cliente()
        self.client.force_login(self.user)

    def test_correo_confirmacion_enviado_al_crear_pedido(self):
        self.client.post(reverse('registrar_pedido'), {
            'destinatario': 'Receptor Uno',
            'tipo_servicio': 'maritimo',
            'origen': 'Quito',
            'destino': 'Manta',
            'descripcion_carga': 'Maquinaria',
            'peso_kg': '50.00',
        })
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.cliente.email, mail.outbox[0].to)

    def test_correo_confirmacion_contiene_tracking(self):
        self.client.post(reverse('registrar_pedido'), {
            'destinatario': 'Receptor Dos',
            'tipo_servicio': 'terrestre',
            'origen': 'Cuenca',
            'destino': 'Loja',
            'descripcion_carga': 'Alimentos',
            'peso_kg': '10.00',
        })
        pedido = Pedido.objects.get(cliente=self.cliente)
        cuerpo = mail.outbox[0].body
        self.assertIn(pedido.numero_tracking, cuerpo)
        self.assertIn('Receptor Dos', cuerpo)


class CorreoEntregaTest(TestCase):

    def setUp(self):
        _, self.cliente = crear_usuario_cliente()
        self.pedido = crear_pedido(self.cliente, estado='en_transito')
        self.despacho = crear_usuario_despachador()
        self.client.force_login(self.despacho)

    def test_correo_entrega_enviado_al_marcar_entregado(self):
        self.client.post(reverse('lista_pedidos'), {
            'pedido_id': self.pedido.pk,
            'nuevo_estado': 'entregado',
        })
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.cliente.email, mail.outbox[0].to)
        self.assertIn('entregado', mail.outbox[0].subject.lower())

    def test_correo_entrega_no_se_envia_si_ya_era_entregado(self):
        pedido_ya_entregado = crear_pedido(self.cliente, estado='entregado')
        self.client.post(reverse('lista_pedidos'), {
            'pedido_id': pedido_ya_entregado.pk,
            'nuevo_estado': 'entregado',
        })
        # No debe enviarse correo porque el estado no cambió
        self.assertEqual(len(mail.outbox), 0)
