from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.middleware.csrf import get_token
import json
from aplicacion_porticos import monitor_ftp
from aplicacion_porticos.models import Alerta, Carpeta, CarpetaUsuario, Ciudad, CiudadVecina, Registro, ListaNegra
from base64 import b64decode
from io import BytesIO
import threading
from PIL import Image
from django.utils import timezone
from django.contrib.auth.models import User, Group
from django.shortcuts import redirect

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
    isAdmin = False
    
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

            isAdmin = user.is_superuser

            r=True

            return JsonResponse(data={'r':r, 'user':user.username, 'admin':isAdmin})
        else:
            return JsonResponse(data={'r':r, 'user':username, 'admin':isAdmin})

@csrf_exempt
def logout_user(request):

    usuario = request.user

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

    registros = Registro.objects.filter(usuario=usuario).values('id', 'patente', 'fecha_hora', 'infraccion_id', 'infraccion__descripcion').order_by('-fecha_hora')

    if patente:
        registros = registros.filter(patente__icontains=patente)

    elif filtro == '1':
        registros = registros.filter(usuario=usuario)

    elif filtro:
        registros = registros.filter(infraccion=filtro)

    registros_serializados = []
    for registro in registros:
        registro_serializado = {
            'id': registro['id'],
            'patente': registro['patente'],
            'fecha_hora': registro['fecha_hora'].strftime('%d/%m/%Y %H:%M:%S'),  # Formatear la fecha
            'infraccion_descripcion': registro['infraccion__descripcion']
        }
        registros_serializados.append(registro_serializado)

    return JsonResponse({'registros': registros_serializados})

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
    usuario = request.user
    print(f'Registro a buscar: {id_dato}')

    if request.method == 'DELETE':
        try:
            # Obtener el objeto ListaNegra por su ID
            registro = ListaNegra.objects.get(id=id_dato)

            # Verificar si el usuario que intenta eliminar es el mismo que lo creó
            if registro.usuario == usuario:
                # Eliminar el registro
                registro.delete()
                return JsonResponse({'success': True, 'message': 'Registro eliminado correctamente'})
            else:
                return JsonResponse({'success': False, 'message': 'No tiene permiso para eliminar este registro'})

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
            # Serializar las alertas y formatear la fecha
            alertas_serializables = []
            for alerta in alertas:
                alerta_dict = {
                    'id': alerta.id,
                    'ciudad_envia': alerta.ciudad_envia.nombre,
                    'ciudad_recibe': alerta.ciudad_recibe.nombre,
                    'fecha': alerta.fecha.strftime('%d/%m/%Y %H:%M:%S'),  # Formatear la fecha
                    'patente': alerta.patente,
                    'comentario': alerta.comentario
                }
                alertas_serializables.append(alerta_dict)

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
    ).values('id', 'patente', 'fecha_hora', 'infraccion__nombre').order_by('-id')

    # Convertir los resultados en un formato JSON
    registros_json = [
        {
            'id': registro['id'],
            'patente': registro['patente'],
            'fecha': registro['fecha_hora'].strftime('%d/%m/%Y %H:%M:%S'),
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

    ciudad_nombre = None  # Inicializar ciudad_nombre como None

    if usuario.groups.exists():
        grupo_ciudad = usuario.groups.first()
        ciudad_nombre = grupo_ciudad.name

    if ciudad_nombre is not None:
        ciudad = Ciudad.objects.filter(nombre=ciudad_nombre).first()
        if ciudad is not None:
            print(f'Ciudad origen: {ciudad.nombre}')
        else:
            print('No se encontró la ciudad asociada al grupo del usuario')
    else:
        print('El usuario no tiene grupos asignados')

    return JsonResponse({'ciudad': ciudad_nombre})

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
from django.db.models import Count
from datetime import datetime
from .models import Carpeta, CarpetaUsuario, Registro
from django.db.models import Q

@csrf_exempt
def detalles_patentes(request):
    usuario_id = request.user.id
    
    fecha_hoy = timezone.localtime(timezone.now())
    inicio_dia = datetime.combine(fecha_hoy, datetime.min.time())
    fin_dia = datetime.combine(fecha_hoy, datetime.max.time())

    # Consulta para obtener la lista de carpetas y la cantidad de registros para el usuario actual
    resultado_consulta = (
        Carpeta.objects
        .filter(carpetausuario__usuario_id=usuario_id)  # Filtrar las carpetas asociadas al usuario
        .annotate(cantidad_registros=Count('registro', filter=Q(registro__fecha_hora__range=(inicio_dia, fin_dia))))  # Contar registros asociados a cada carpeta que estén dentro del rango de fechas
        .values('nombre', 'cantidad_registros')  # Seleccionar los campos deseados
    )

    # Construir la respuesta
    arreglo_respuesta = []
    for item in resultado_consulta:
        carpeta_nombre_completo = item['nombre']
        carpeta_nombre = carpeta_nombre_completo.split('/')[2]  # Obtener el último segmento del nombre de la carpeta
        arreglo_respuesta.append({'carpeta': carpeta_nombre, 'cantidad_registros': item['cantidad_registros']})

    return JsonResponse({'respuesta': arreglo_respuesta})

@csrf_exempt
def ver_imagen_infraccion(request):
    id_infraccion = request.GET.get('id')
    print(f'Id registro: {id_infraccion}')

    # Recuperar el registro específico desde la base de datos
    alerta = Registro.objects.get(id=id_infraccion)

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
    

##########################################################
##########################################################
############### PANEL DE ADMINISTRACIÓN ##################
##########################################################
##########################################################
    
@csrf_exempt
def admin_ver_usuarios(request):

    username = request.GET.get('username')

    usuario = User.objects.filter(is_superuser=0, username__icontains=username)

    usuarios= []

    for u in usuario:

        grupos_usuario = u.groups.all()
        ciudad = None

        if grupos_usuario.exists():
            ciudad = grupos_usuario.first().name

            u_serializado ={
                'id':u.id,
                'username': u.username,
                'ciudad': ciudad
            }
        else:
            u_serializado ={
                'id':u.id,
                'username': u.username,
            }

        usuarios.append(u_serializado)  


    return JsonResponse({'usuarios':usuarios})

from django.shortcuts import get_object_or_404


@csrf_exempt
def logout_usuarios(request):
    if request.method == 'POST':
        id_usuario = request.GET.get('id')

        # Obtener el objeto de usuario
        usuario = get_object_or_404(User, id=id_usuario)
        
        print(f'Solicitud de detener monitoreo para el usuario con ID: {id_usuario}')
        
        # Detener el monitoreo si está en curso para este usuario
        monitor_detenido = monitor_ftp.detener_monitoreo_usuario(usuario)

        return JsonResponse({'data': 'success'})

@csrf_exempt
def eliminar_usuario(request):
    id_dato = request.GET.get('id')
    print(f'Usuario a buscar: {id_dato}')

    if request.method == 'DELETE':
        try:
            # Obtener el objeto ListaNegra por su ID
            usuario = User.objects.get(id=id_dato)

            # Verificar si el usuario que intenta eliminar es el mismo que lo creó
            usuario.delete()
            return JsonResponse({'success': True, 'message': 'Registro eliminado correctamente'})
            
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'El usuario no existe'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    else:
        return JsonResponse({'success': False, 'message': 'Método no permitido'})
    
@csrf_exempt
def admin_crear_usuario(request):
    if request.method == 'POST':
        # Obtener el cuerpo de la solicitud como un diccionario
        body_unicode = request.body.decode('utf-8')
        body_data = json.loads(body_unicode)

        # Obtener los datos de la solicitud
        username = body_data.get('username')
        password = body_data.get('password')
        grupo = body_data.get('grupo')
        grupo = grupo.upper()

        # Verificar si el grupo ya existe o crearlo
        grupo, creado = Group.objects.get_or_create(name=grupo)

        user = User.objects.create_user(username=username, password=password)
        
        user.save()
        grupo.user_set.add(user)
        

        return JsonResponse({'data':'Usuario creado y agregado al grupo '+grupo.name})
    
@csrf_exempt
def admin_ver_camaras(request):

    camara = request.GET.get('camara')

    carpeta = Carpeta.objects.filter(nombre__icontains=camara).values('id','nombre','ubicacion','ciudad__nombre')

    carpetas= []

    for c in carpeta:
            
        nombre_camara = c['nombre'].split('/')[-2]  # Obtener el último texto después de "/"

        c_serializado ={
            'id':c['id'],
            'nombre': nombre_camara,
            'ubicacion': c['ubicacion'],
            'ciudad':c['ciudad__nombre']
            }

        carpetas.append(c_serializado)  


    return JsonResponse({'carpetas':carpetas})

@csrf_exempt
def eliminar_camara(request):
    id_dato = request.GET.get('id')
    print(f'Camara a buscar: {id_dato}')

    if request.method == 'DELETE':
        try:
            # Obtener el objeto ListaNegra por su ID
            camara = Carpeta.objects.get(id=id_dato)

            # Verificar si el usuario que intenta eliminar es el mismo que lo creó
            camara.delete()
            return JsonResponse({'success': True, 'message': 'Camara eliminado correctamente'})
            
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'La camara no existe'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    else:
        return JsonResponse({'success': False, 'message': 'Método no permitido'})
    
@csrf_exempt
def admin_ver_ciudades(request):

    ciudad = Ciudad.objects.all()

    ciudades= []

    for c in ciudad:

        c_serializado ={
            'value': c.nombre.lower(),
            'label': c.nombre,
            }

        ciudades.append(c_serializado)  


    return JsonResponse({'ciudades':ciudades})
    
@csrf_exempt
def admin_crear_camara(request):
    if request.method == 'POST':
        # Obtener el cuerpo de la solicitud como un diccionario
        body_unicode = request.body.decode('utf-8')
        body_data = json.loads(body_unicode)

        # Obtener los datos de la solicitud
        nombre = body_data.get('nombre')
        ubicacion = body_data.get('ubicacion')
        ciudad = body_data.get('ciudad')

        nombre = nombre.upper()
        ubicacion = ubicacion.upper()

        nombre_camara = 'C:/FTP/'+nombre+'/'

        print(f'Camara {nombre_camara}')

        ciudades = Ciudad.objects.get(nombre=ciudad)

        camara = Carpeta.objects.create(nombre=nombre_camara, ubicacion=ubicacion, ciudad=ciudades)
        
        camara.save()
        
        return JsonResponse({'data':'Carpeta creada '+camara.nombre})
    
@csrf_exempt
def admin_enviar_datos(request):
    id_dato = request.GET.get('id')

    camaras = []

    if id_dato:
        camara = Carpeta.objects.filter(id=id_dato).first()  # Usar first() para obtener el primer objeto o None

        if camara:
            ciudad = camara.ciudad

            nombre_camara = camara.nombre.split('/')[-2]  # Obtener el último texto después de "/"

            c_serializado ={
                'nombre': nombre_camara,
                'ubicacion': camara.ubicacion,
                'ciudad':{
                    'value': ciudad.nombre.lower(),
                    'label': ciudad.nombre
                }
            }

            camaras.append(c_serializado)

    return JsonResponse({'camaras':camaras})


@csrf_exempt
def admin_editar_camara(request):
    if request.method == 'POST':
        body_unicode = request.body.decode('utf-8')
        body_data = json.loads(body_unicode)

        try:
            # Obtener los datos de la solicitud
            id = body_data.get('id')

            camara = Carpeta.objects.get(id=id)

            nombre = body_data.get('nombre')
            ubicacion = body_data.get('ubicacion')
            ciudad = body_data.get('ciudad')

            print(f'ID: {id}, Nombre: {nombre}, Ubicacion: {ubicacion}, Ciudad: {ciudad}')

            # Convertir nombre y ubicación a mayúsculas
            nombre = nombre.upper()
            ubicacion = ubicacion.upper()

            # Construir la ruta de la carpeta
            nombre_carpeta = 'C:/FTP/' + nombre + '/'

            # Obtener el objeto Ciudad correspondiente al nombre recibido
            ciudad_obj = Ciudad.objects.get(nombre=ciudad)

            # Actualizar los atributos de la cámara
            camara.nombre = nombre_carpeta
            camara.ubicacion = ubicacion
            camara.ciudad = ciudad_obj

            # Guardar los cambios en la base de datos
            camara.save()

            return JsonResponse({'data': 'success'})
        except Carpeta.DoesNotExist:
            return JsonResponse({'error': 'La cámara con el ID proporcionado no existe'}, status=404)
    else:
        return JsonResponse({'error': 'Esta vista solo acepta solicitudes POST'}, status=405)
