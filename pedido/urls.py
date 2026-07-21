from django.urls import path
from . import views

urlpatterns = [
    # Public
    path('', views.inicio, name='inicio'),
    path('rastreo/', views.rastreo_publico, name='rastreo_publico'),
    path('rastreo/<str:numero_guia>/', views.resultado_rastreo, name='resultado_rastreo'),
    
    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Secretario
    path('secretario/', views.dashboard_secretario, name='dashboard_secretario'),
    path('secretario/clientes/', views.listar_clientes, name='listar_clientes'),
    path('secretario/clientes/crear/', views.crear_cliente, name='crear_cliente'),
    path('secretario/clientes/<int:pk>/editar/', views.editar_cliente, name='editar_cliente'),
    path('secretario/ciudades/', views.listar_ciudades, name='listar_ciudades'),
    path('secretario/ciudades/crear/', views.crear_ciudad, name='crear_ciudad'),
    path('secretario/ciudades/<int:pk>/editar/', views.editar_ciudad, name='editar_ciudad'),
    path('secretario/ciudades/<int:pk>/toggle/', views.toggle_ciudad, name='toggle_ciudad'),
    path('secretario/encomiendas/', views.listar_encomiendas, name='listar_encomiendas'),
    path('secretario/encomiendas/registrar/', views.registrar_encomienda, name='registrar_encomienda'),
    path('secretario/encomiendas/<int:pk>/', views.detalle_encomienda, name='detalle_encomienda'),
    path('secretario/encomiendas/<int:pk>/estado/', views.cambiar_estado, name='cambiar_estado'),
    path('secretario/encomiendas/<int:pk>/comprobante/', views.comprobante_encomienda, name='comprobante_encomienda'),
    path('secretario/encomiendas/<int:pk>/comprobante/pdf/', views.descargar_comprobante_pdf, name='descargar_comprobante_pdf'),
    path('secretario/encomiendas/<int:pk>/comprobante/email/', views.enviar_comprobante_email, name='enviar_comprobante_email'),
    
    # Despachador
    path('despachador/', views.mis_asignaciones, name='mis_asignaciones'),
    path('despachador/encomienda/<int:pk>/estado/', views.actualizar_estado_despachador, name='actualizar_estado_despachador'),
    
    # Cliente
    path('mis-envios/', views.mis_envios, name='mis_envios'),
    path('mis-envios/<int:pk>/', views.detalle_envio_cliente, name='detalle_envio_cliente'),
]
