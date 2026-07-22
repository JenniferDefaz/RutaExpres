def rol_usuario(request):
    """
    Inyecta variables de rol en el contexto de todas las plantillas.
    """
    es_secretario = False
    es_despachador = False
    es_rol_interno = False

    if request.user.is_authenticated:
        es_secretario = (
            request.user.is_staff
            or request.user.groups.filter(name='Secretario').exists()
        )
        es_despachador = request.user.groups.filter(name='Despachador').exists()
        es_rol_interno = es_secretario or es_despachador

    return {
        'es_secretario': es_secretario,
        'es_despachador': es_despachador,
        'es_rol_interno': es_rol_interno,
    }
