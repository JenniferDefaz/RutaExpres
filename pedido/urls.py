#1111111111111111111  Archivo para gertionar las rutas internas de la app Nomina 

#IMprotar una libreria que eta dentro de Django para gestionar las rutas path es una
# funcion que se encarga de gestionar las rutas internas de la app   
from django.urls import path  
#Importamos la logica de negocios de la app Nomina
#El views es un archivo que se encarga de gestionar la logica de negocios de la app Nomina 
#LO estamos llamando 
from . import views
#Definimos las rutas internas de la app Nomina
#Listado de rutas de la aplicacion Nomina
urlpatterns = [
    path('', views.inicio),
    
]
