from django.urls import path
from . import views

urlpatterns = [
    # Inicio
    path('', views.inicio, name='inicio'),
    path('inicio/', views.inicio, name='inicio_home'),

    # Autenticación
    path('login/', views.iniciar_sesion, name='iniciar_sesion'),
    path('logout/', views.cerrar_sesion, name='cerrar_sesion'),

    # Clientes
    path('clientes/registrar/', views.registrar_cliente, name='registrar_cliente'),

    # Pedidos — rutas específicas PRIMERO, luego las dinámicas
    path('pedidos/', views.lista_pedidos, name='lista_pedidos'),
    path('pedidos/registrar/', views.registrar_pedido, name='registrar_pedido'),
    path('pedidos/rastrear/', views.rastrear_pedido, name='rastrear_pedido'),
    path('pedidos/<str:tracking>/pdf/', views.descargar_orden_pdf, name='descargar_orden_pdf'),
    path('pedidos/<str:tracking>/', views.detalle_pedido, name='detalle_pedido'),

    # Panel cliente
    path('panel/', views.panel_cliente, name='panel_cliente'),

    # Reporte
    path('reporte/', views.reporte_global, name='reporte_global'),
]
