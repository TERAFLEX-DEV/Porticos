import os
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.middleware.csrf import get_token
import json
from aplicacion_porticos import monitor_ftp
from aplicacion_porticos.models import Alerta, CarpetaUsuario, Ciudad, CiudadVecina, Registro, ListaNegra
from base64 import b64decode
from io import BytesIO
import threading
from PIL import Image
from django.utils import timezone



# Create your views here.
@csrf_exempt
def get_csrf_token(request):
    csrf_token = get_token(request)
    # Puedes enviar el token CSRF como parte de la respuesta JSON
    return JsonResponse({'csrf_token': csrf_token})

@csrf_exempt
def login_user(request):
    # Asegurarse de que la solicitud provenga de un origen permitido
    response = HttpResponse()
    response["Access-Control-Allow-Origin"] = "*"  # Permitir solicitudes de cualquier origen
    response["Access-Control-Allow-Methods"] = "POST"  # Permitir solo solicitudes POST
    response["Access-Control-Allow-Headers"] = "Content-Type"  # Permitir solo el encabezado Content-Type

    r = False
    
    if request.method == 'POST':
        # Obtener el cuerpo de la solicitud como un diccionario
        body_unicode = request.body.decode('utf-8')
        body_data = json.loads(body_unicode)

        # Obtener el nombre de usuario y la contraseña del diccionario
        username = body_data.get('username')
        password = body_data.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            r=True

            return JsonResponse(data={'r':r, 'user':user.username})
        else:
            return JsonResponse(data={'r':r, 'user':username})

@csrf_exempt
def logout_user(request):

    usuario = request.user

    print(f'Solicitud detener monitoreo---')
    
    # Detener el monitoreo si está en curso para este usuario
    monitor_ftp.detener_monitoreo_usuario(usuario)

    print(f'Monitoreo detenido---')

    logout(request)
    return JsonResponse({'message':'Success'})


threads_activos = []

@csrf_exempt
def monitoreo_principal(request):
    usuario = request.user  # Obtener el ID del usuario autenticado
    r = True

    carpetas_usuario = CarpetaUsuario.objects.filter(usuario=usuario)
    paths = [cu.carpeta.nombre for cu in carpetas_usuario]

    print(f'Carpetas: {paths}')
    print(f'Usuario autenticado: {usuario.id}')

    # Iniciar el monitoreo en segundo plano
    iniciar_monitoreo_en_segundo_plano(usuario, paths)

    return JsonResponse({'data': r})

def iniciar_monitoreo_en_segundo_plano(usuario, carpetas):
    monitor_thread = threading.Thread(target=monitor_ftp.iniciar_monitoreo_usuario, args=(usuario, carpetas))
    monitor_thread.start()

@csrf_exempt
def porticos_monitoreo(request):
    usuario = request.user
    carpetas_usuario = CarpetaUsuario.objects.filter(usuario=usuario)

    datos_camara = []
    for carpeta_usuario in carpetas_usuario:
        nombre_camara = carpeta_usuario.carpeta.nombre

        nombre_camara = nombre_camara.split('/')[-2]  # Obtener el último texto después de "/"

        ubicacion_camara = carpeta_usuario.carpeta.ubicacion
        datos_camara.append({'camara': nombre_camara, 'ubicacion': ubicacion_camara})

    return JsonResponse({'camaras': datos_camara})

@csrf_exempt
def historial_patentes(request):
    usuario = request.user
    patente = request.GET.get('patente')
    filtro = request.GET.get('filtro')
    print(f'Vacio')

    registros = Registro.objects.filter(usuario=usuario).values('id', 'patente', 'fecha_hora', 'infraccion_id', 'infraccion__descripcion').order_by('-fecha_hora')
    print(f'Respondido...')

    if patente:
        print(f'Patente: {patente} responde')
        # Aplicar filtro por patente si se proporciona
        registros = registros.filter(patente__icontains=patente).values('id', 'patente', 'fecha_hora', 'infraccion_id', 'infraccion__descripcion').order_by('-fecha_hora')
        
    elif filtro == '1':
        print(f'Patente: {patente} - Filtro: {filtro} responde filtro 1')
        # Aplicar filtro adicional si se proporciona
        registros = registros.filter(usuario=usuario).values('id', 'patente', 'fecha_hora', 'infraccion_id', 'infraccion__descripcion').order_by('-fecha_hora')

    elif filtro:
        print(f'Patente: {patente} - Filtro: {filtro} responde')
        # Aplicar filtro adicional si se proporciona
        registros = registros.filter(infraccion=filtro).values('id', 'patente', 'fecha_hora', 'infraccion_id', 'infraccion__descripcion').order_by('-fecha_hora')

    # Iterar sobre los registros y ajustar la descripción de la infracción según el tipo
    for registro in registros:
        if registro['infraccion_id'] not in [2, 3, 4]:
            registro['infraccion__descripcion'] = ''  # Si no es tipo 2, 3 o 4, establecer descripción vacía
        del registro['infraccion_id']  # Eliminar el campo de descripción de la infracción

    # Devolver los registros encontrados en la respuesta JSON
    return JsonResponse({'registros': list(registros)})

@csrf_exempt
def ver_imagen(request):
    id_registro = request.GET.get('id')
    print(f'Id registro: {id_registro}')

    # Recuperar el registro específico desde la base de datos
    registro = Registro.objects.get(id=id_registro)

    # Obtener el contenido binario de la imagen almacenado como base64
    imagen_base64 = registro.imagen_binaria

    if imagen_base64:
        imagen_binaria = b64decode(imagen_base64)

        # Crear una instancia de Image desde los datos binarios
        image = Image.open(BytesIO(imagen_binaria))

        # Crear una respuesta HTTP con el contenido binario
        response = HttpResponse(content_type="image/jpeg")

        # Guardar la imagen en la respuesta
        image.save(response, format="JPEG")

        return response
    else:
        return JsonResponse({'data':False})
    
@csrf_exempt
def comentario_infraccion(request):

    id_registro = request.GET.get('id')
    print(f'Id registro: {id_registro}')

    registro = Registro.objects.filter(id=id_registro).values('observacion').first()

    if registro:
        return JsonResponse({'comentario': registro})
    else:
        return JsonResponse({'comentario': False})

@csrf_exempt
def lista_negra(request):
    patente = request.GET.get('patente')
    print(f'Patente: {patente}')

    # Obtener los objetos ListaNegra que coinciden con la patente
    lista = ListaNegra.objects.all().values('id', 'patente', 'motivo', 'usuario__username', 'ciudad')

    if patente:
        lista = ListaNegra.objects.filter(patente__icontains=patente).values('id', 'patente', 'motivo', 'usuario__username', 'ciudad')

    # Convertir el resultado en una lista para poder serializarlo a JSON
    lista_serializable = list(lista)

    return JsonResponse({'lista': lista_serializable})

@csrf_exempt
def registro_infraccion(request):
    patente = request.GET.get('patente')
    print(f'Patente a buscar: {patente}')

    # Obtener la lista de registros filtrados por patente
    registros = Registro.objects.filter(patente=patente).values('carpeta__nombre', 'carpeta__ubicacion', 'fecha_hora', 'observacion')

    # Obtener el nombre de la cámara
    nombre_camara = registros.first().get('carpeta__nombre', '').split('/')[-2] if registros else None

    # Reemplazar el valor de 'carpeta__nombre' con 'nombre_camara' en la lista serializable
    lista_serializable = [
        {
            'nombre_camara': nombre_camara,
            'ubicacion_carpeta': registro.get('carpeta__ubicacion', ''),
            'fecha_hora': registro.get('fecha_hora', ''),
            'observacion': registro.get('observacion', '')
        }
        for registro in registros
    ]

    return JsonResponse({'lista': lista_serializable})

@csrf_exempt
def agregar_lista_negra(request):
    usuario = request.user

    grupos_usuario = usuario.groups.all()

    grupo = grupos_usuario.first() if grupos_usuario else None

    if grupo:
        ciudad = grupo.name
        print(f'Grupo: {ciudad}')

    if request.method == 'POST':
        # Obtener el cuerpo de la solicitud como un diccionario
        body_unicode = request.body.decode('utf-8')
        body_data = json.loads(body_unicode)

        # Obtener los datos de la solicitud
        patente = body_data.get('patente')
        patente = patente.upper()
        motivo = body_data.get('motivo')

        # Crear un nuevo objeto ListaNegra
        try:
            nuevo_registro = ListaNegra.objects.create(patente=patente, motivo=motivo, usuario=usuario, ciudad=ciudad)
            return JsonResponse({'success': True, 'id': nuevo_registro.id, 'message': 'Registro de lista negra creado exitosamente'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    else:
        return JsonResponse({'success': False, 'message': 'Método no permitido'})

@csrf_exempt
def eliminar_lista_negra(request):
    id_dato = request.GET.get('id')
    print(f'Registro a buscar: {id_dato}')

    if request.method == 'DELETE':
        try:
            # Obtener el objeto ListaNegra por su ID
            registro = ListaNegra.objects.get(id=id_dato)
            # Eliminar el registro
            registro.delete()
            # print(f'Patente eliminada')
            return JsonResponse({'success': True, 'message': 'Registro eliminado correctamente'})
        except ListaNegra.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'El registro no existe'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    else:
        return JsonResponse({'success': False, 'message': 'Método no permitido'})

@csrf_exempt
def alerta_ciudad(request):
    usuario = request.user
    grupos_usuario = usuario.groups.all()
    ciudad = None

    if grupos_usuario.exists():
        # Si el usuario pertenece a algún grupo, obtén la primera ciudad del primer grupo
        ciudad = grupos_usuario.first().name
        print(f'Grupo: {ciudad}')

    if ciudad:
        # Busca el ID de la ciudad en la base de datos
        ubi = Ciudad.objects.filter(nombre=ciudad).values('id').first()
        if ubi:
            id_ciudad = ubi['id']
            print(f'Id ciudad: {id_ciudad}')
            # Obtener las alertas relacionadas con la ciudad encontrada
            alertas = Alerta.objects.filter(ciudad_recibe=id_ciudad).order_by('-fecha')
            # Convertir el resultado en una lista para poder serializarlo a JSON
            alertas_serializables = list(alertas.values('id', 'ciudad_envia__nombre', 'ciudad_recibe__nombre', 'fecha', 'patente', 'comentario'))

            return JsonResponse({'alertas': alertas_serializables})
        else:
            return JsonResponse({'error': 'La ciudad no fue encontrada'})
    else:
        return JsonResponse({'error': 'El usuario no pertenece a ningún grupo'})

from aplicacion_porticos.consumers import PorticosConsumer

@csrf_exempt
def notificacion_infraccion(request):
    usuario=request.user
    registros = Registro.objects.filter(
        infraccion_id__in=[2, 3, 4],
        observacion__in=[None, ''],
        usuario_id=usuario
    ).values('id', 'patente', 'infraccion__nombre').order_by('-id')

    # Convertir los resultados en un formato JSON
    registros_json = [
        {
            'id': registro['id'],
            'patente': registro['patente'],
            'nombre_infraccion': registro['infraccion__nombre']
        }
        for registro in registros
    ]

    return JsonResponse({'registros': registros_json})

@csrf_exempt
def ciudades_vecinas(request):

    usuario = request.user
    ciudad = None

    if usuario.groups.exists():
        # Obtener la primera ciudad asociada al primer grupo del usuario
        grupo_ciudad = usuario.groups.first()
        ciudad_nombre = grupo_ciudad.name
        ciudad = Ciudad.objects.filter(nombre=ciudad_nombre).first()

    if ciudad is not None:
        # Obtener las ciudades vecinas de la ciudad del usuario
        vecinas = CiudadVecina.objects.filter(origen=ciudad)
        data = list(vecinas.values('destino__nombre'))
    else:
        data = []

    return JsonResponse({'data': data})

@csrf_exempt
def insertar_comentario(request):
    print(f'Vista ingreso comentario')

    usuario = request.user

    if usuario.groups.exists():
        grupo_ciudad = usuario.groups.first()
        ciudad_nombre = grupo_ciudad.name
        ciudad_origen = Ciudad.objects.filter(nombre=ciudad_nombre).first()
    print(f'Ciudad origen: {ciudad_origen.nombre} - {ciudad_origen.id}')

    if request.method == 'POST':
        # Obtener el cuerpo de la solicitud como un diccionario
        body_unicode = request.body.decode('utf-8')
        body_data = json.loads(body_unicode)

        id = body_data.get('id')
        ciudades = body_data.get('ciudades')

        if 'comentario' in body_data:
            comentario = body_data.get('comentario')

            # Validar que el comentario no esté vacío
            if comentario.strip():
                Registro.objects.filter(id=id).update(observacion=comentario)
            else:
                return None

            if ciudades:
                for nombre_ciudad in ciudades:
                    # Buscar la ciudad por su nombre
                    ciudad = Ciudad.objects.filter(nombre=nombre_ciudad).first()
                    patente_query = Registro.objects.filter(id=id).values('patente', 'imagen_binaria')
                    patente = patente_query.first()['patente'] if patente_query.exists() else None
                    print(f'Patente: {patente}')

                    imagen = patente_query.first()['imagen_binaria'] if patente_query.exists() else None
                    
                    print(f'Ciudad destino: {ciudad.nombre} - {ciudad.id}')

                    # Crear una instancia de Alerta para la ciudad de destino
                    alerta = Alerta.objects.create(
                        ciudad_envia=ciudad_origen,  # Asigna la ciudad de origen a la alerta
                        ciudad_recibe=ciudad,  # Asigna la ciudad de destino a la alerta
                        fecha=timezone.now(),  # Asigna la fecha actual
                        patente=patente,  # Asigna la patente si es relevante
                        comentario=comentario,  # Asigna el comentario
                        visto = 2,
                        imagen_binaria = imagen
                    )

                    id_alerta = alerta.id

                    # await PorticosConsumer.enviar_notificacion_global(ciudad_origen, patente)
                    noti(id_alerta, ciudad_origen, ciudad, patente)

                    print(f'Alerta creada para {ciudad.nombre}')
                        
            else:
                print('No se han proporcionado ciudades.')

            return JsonResponse({'data': 'success'})
    
    return None

from django.core.serializers import serialize


def noti(id_alerta, origen, destino, patente):
    print(f'Ciudad origen: {origen}, ciudad de destino: {destino} y patente: {patente}')
    # Llamar a la función asíncrona usando un evento de bucle de eventos asyncio
    import asyncio

    # origen = {
    #     'nombre': origen.nombre,
    #     # Agrega otros campos relevantes que necesites serializar
    # }
    # destino = {
    #     'nombre': destino.nombre,
    #     # Agrega otros campos relevantes que necesites serializar
    # }

    # Llamar a la función asíncrona usando un evento de bucle de eventos asyncio
    asyncio.run(PorticosConsumer.enviar_notificacion_global(id_alerta, origen.nombre, destino.nombre, patente))

@csrf_exempt
def grupo_usuario(request):
    print(f'Vista ingreso comentario')

    usuario = request.user

    if usuario.groups.exists():
        grupo_ciudad = usuario.groups.first()
        ciudad_nombre = grupo_ciudad.name
        ciudad = Ciudad.objects.filter(nombre=ciudad_nombre).first()
    print(f'Ciudad origen: {ciudad.nombre}')

    return JsonResponse ({'ciudad':ciudad.nombre})

@csrf_exempt
def visto_alerta(request):
    print(f'Usuario vio alerta')
    id_alerta = request.GET.get('id')

    if id_alerta:
        try:
            alerta = Alerta.objects.get(id=id_alerta)
            alerta.visto = 1
            alerta.save()
            return JsonResponse({'data': 'success'})
        except Alerta.DoesNotExist:
            return JsonResponse({'error': 'La alerta no existe'}, status=404)
    else:
        return JsonResponse({'error': 'Se requiere un ID de alerta'}, status=400)
    
@csrf_exempt
def alerta_ciudad_noti(request):
    usuario = request.user
    grupos_usuario = usuario.groups.all()
    ciudad = None

    if grupos_usuario.exists():
        # Si el usuario pertenece a algún grupo, obtén la primera ciudad del primer grupo
        ciudad = grupos_usuario.first().name
        print(f'Grupo: {ciudad}')

    if ciudad:
        # Busca el ID de la ciudad en la base de datos
        ubi = Ciudad.objects.filter(nombre=ciudad).values('id').first()
        if ubi:
            id_ciudad = ubi['id']
            print(f'Id ciudad: {id_ciudad}')
            # Obtener las alertas relacionadas con la ciudad encontrada
            alertas = Alerta.objects.filter(ciudad_recibe=id_ciudad).order_by('-fecha')[:3]
            # Convertir el resultado en una lista para poder serializarlo a JSON
            alertas_serializables = list(alertas.values('id', 'ciudad_envia__nombre', 'ciudad_recibe__nombre', 'fecha', 'patente', 'comentario'))

            return JsonResponse({'alertas': alertas_serializables})
        else:
            return JsonResponse({'error': 'La ciudad no fue encontrada'})
    else:
        return JsonResponse({'error': 'El usuario no pertenece a ningún grupo'})
    
@csrf_exempt
def ver_imagen_alerta(request):
    id_alerta = request.GET.get('id')
    print(f'Id registro: {id_alerta}')

    # Recuperar el registro específico desde la base de datos
    alerta = Alerta.objects.get(id=id_alerta)

    # Obtener el contenido binario de la imagen almacenado como base64
    imagen_base64 = alerta.imagen_binaria

    if imagen_base64:
        imagen_binaria = b64decode(imagen_base64)

        # Crear una instancia de Image desde los datos binarios
        image = Image.open(BytesIO(imagen_binaria))

        # Crear una respuesta HTTP con el contenido binario
        response = HttpResponse(content_type="image/jpeg")

        # Guardar la imagen en la respuesta
        image.save(response, format="JPEG")

        return response
    else:
        return JsonResponse({'data':False})

from datetime import datetime

@csrf_exempt
def detalles_patentes(request):
    usuario = request.user
    arreglo_respuesta = []  # Arreglo para almacenar los datos de cada carpeta y la cantidad de registros
    carpetas_usuario = CarpetaUsuario.objects.filter(usuario=usuario).values('id', 'carpeta__nombre')
    
    for carpeta_usuario in carpetas_usuario:
        carpeta_nombre = carpeta_usuario["carpeta__nombre"]
        ultimo_segmento = os.path.basename(carpeta_nombre.rstrip('/'))  # Obtener el último segmento del nombre de la carpeta

        fecha_hoy = timezone.localtime(timezone.now())
        inicio_dia = datetime.combine(fecha_hoy, datetime.min.time())
        fin_dia = datetime.combine(fecha_hoy, datetime.max.time())

        # Filtrar los registros asociados a la carpeta que se hayan creado hoy
        registros = Registro.objects.filter(carpeta_id=carpeta_usuario['id'], fecha_hora__range=(inicio_dia, fin_dia))
        cantidad_registros = registros.count()

        # Agregar los datos de la carpeta y la cantidad de registros al arreglo de respuesta
        arreglo_respuesta.append({'carpeta': ultimo_segmento, 'cantidad_registros': cantidad_registros})

    return JsonResponse({'respuesta': arreglo_respuesta})