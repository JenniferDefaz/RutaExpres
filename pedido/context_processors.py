def rol_usuario(request):
    """
    Inyecta 'es_rol_interno' en el contexto de todas las plantillas.
    True si el usuario autenticado es staff, Secretario o Despachador.
    """
    es_rol_interno = False
    if request.user.is_authenticated:
        es_rol_interno = (
            request.user.is_staff
            or request.user.groups.filter(name__in=['Secretario', 'Despachador']).exists()
        )
    return {'es_rol_interno': es_rol_interno}
