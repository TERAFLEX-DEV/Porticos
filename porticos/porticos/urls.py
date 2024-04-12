"""
URL configuration for porticos project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from aplicacion_porticos import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('csrf_endpoint/', views.get_csrf_token),
    path('monitoreo_camaras/', views.monitoreo_principal),
    path('porticos_monitoreo/', views.porticos_monitoreo),
    path('historial_patentes',views.historial_patentes),
    path('ver_imagen', views.ver_imagen),
    path('comentario_infraccion', views.comentario_infraccion),
    path('lista_negra', views.lista_negra),
    path('detalles_lista_negra', views.registro_infraccion),
    path('agregar_patente_negra/', views.agregar_lista_negra),
    path('eliminar_lista_negra', views.eliminar_lista_negra),
    path('alerta_ciudades/', views.alerta_ciudad),
    # path('notificacion_global/', views.notificacion_global),
    path('notificacion_infraccion/', views.notificacion_infraccion),
    path('ciudades_vecinas/', views.ciudades_vecinas),
    path('ingresar_comentario/', views.insertar_comentario),
    path('grupo_usuario/', views.grupo_usuario),
]
