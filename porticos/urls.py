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
    
    ##########################################################
    ##################### PANEL DE USUARIO ###################
    ##########################################################
    
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
    path('visto_alerta', views.visto_alerta),
    path('alerta_ciudades_noti/', views.alerta_ciudad_noti),
    path('ver_imagen_alerta', views.ver_imagen_alerta),
    path('detalles_patentes/', views.detalles_patentes),
    path('ver_imagen_infraccion', views.ver_imagen_infraccion),

##########################################################
############### PANEL DE ADMINISTRACIÓN ##################
##########################################################

    path('admin_ver_usuarios', views.admin_ver_usuarios),
    path('admin_logout_usuarios', views.logout_usuarios),
    path('eliminar_usuario', views.eliminar_usuario),
    path('admin_crear_usuario/', views.admin_crear_usuario),
    path('admin_ver_camaras', views.admin_ver_camaras),
    path('eliminar_camaras', views.eliminar_camara),
    path('admin_crear_camaras/', views.admin_crear_camara),
    path('admin_ver_ciudades/', views.admin_ver_ciudades),
    path('admin_enviar_datos', views.admin_enviar_datos),
    path('admin_editar_camaras/', views.admin_editar_camara),
    path('admin_crear_ciudades/', views.admin_crear_ciudades),
    path('admin_ver_ciudades_buscador', views.admin_ver_ciudades_buscador),
    path('admin_enviar_datos_ciudad', views.admin_enviar_datos_ciudad),
    path('admin_editar_ciudad/', views.admin_editar_ciudad),
    path('admin_enviar_vincular', views.admin_enviar_vincular),
    path('admin_recibir_datos/', views.admin_recibir_datos),
    path('admin_vincular_camaras', views.admin_vincular_camaras),
    path('admin_recibir_camaras/', views.admin_recibir_camaras),
    
    
    path('prueba_exportar', views.mi_vista),
    path('conteo1/', views.conteo1),

    path('admin_conteo_datos', views.admin_conteo_datos),
    path('admin_ciudades_camaras', views.conteo2),
    path('admin_ciudades_horas', views.conteo4),
    path('admin_datos_exportar/', views.datos_exportar),
    path('admin_exportar/', views.exportar),
    
    
    ##########################################################
    ################### PANEL DE FISCALIA ####################
    ##########################################################
    
    path('historial_fiscalia',views.historial_fiscalia),
    path('exportar_fiscalia/', views.exportar_fiscalia),
    
]
