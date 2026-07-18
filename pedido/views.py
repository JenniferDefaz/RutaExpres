from django.shortcuts import render

# Create your views here.
def inicio(request):
    #Presentando en pantalla el contenido de inicio s
    return render(request, 'inicio.html')