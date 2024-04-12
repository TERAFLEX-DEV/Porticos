import asyncio
import base64
from datetime import datetime
import io
import base64
import time
import cv2
from django.utils import timezone
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from ftplib import FTP
from datetime import date
from datetime import timedelta

from aplicacion_porticos.consumers import PorticosConsumer

from aplicacion_porticos.models import Carpeta, Infraccion, ListaNegra, Registro


class MyHandler(FileSystemEventHandler):
    instances = PorticosConsumer.instances  # Obtener la misma variable de instancisas
    def __init__(self, usuario):
        super().__init__()
        self.usuario = usuario

    def on_any_event(self, event):
        # Aquí puedes definir lo que deseas hacer cuando ocurra un evento
        if event.event_type == 'created':  # Si el evento generado es de creación de archivo == imagen nueva
            print(f'Llamamos metodo para archivo, carpeta, patente, fecha y ruta')
            archivo, carpeta, patente, fecha_hora_str, ruta = self.creacion_variables(event) #Obtengo archivo, carpeta, patente, fecha tomada y ruta

            # Verificamos si se obtuvieron valores válidos
            if archivo is None:
                print("Archivo ignorado. No se procesará.")
            else:

                time.sleep(0.5)

                print(f'Descargamos imagen')
                image = self.descargar_imagen(carpeta, archivo) 

                print(f'Verificamos infracciones en patente')
                infraccion = self.obtener_infraccion(patente)   
                print(f'Infraccion: {infraccion}')             

                print(f'---Creamos el modelo de Registro---')
                registro = self.creacion_modelo(patente, carpeta, image, infraccion, fecha_hora_str, archivo)

                print(f'---Consultamos ubicacion patente---')
                a='C:/FTP/'+carpeta+'/'
                camaras = Carpeta.objects.filter(nombre=a)

                if camaras.exists():
                    camara = camaras.first()
                    ubicacion = camara.ubicacion
                    #print(f'Ubicacion es: {ubicacion}')

                print(f'---Consultamos patentes diarias leidas por usuario---')
                total_patente = self.total_patentes_leidas()
                print(f'Total patentes: {total_patente}')

                print(f'---Consultamos infracciones diarias leidas por usuario---')
                total_infracciones = self.total_infracciones_leidas()
                print(f'Total infracciones: {total_infracciones}')

                if infraccion.id == 1 :
                    a = 1
                else:
                    a = 2
                

                print(f'Enviamos notificación')
                asyncio.run(self.enviar_notificacion(patente, ubicacion, a, total_patente, total_infracciones, image))

    def total_infracciones_leidas(self):
        fecha_hoy = timezone.localtime(timezone.now())
        inicio_dia = datetime.combine(fecha_hoy, datetime.min.time())
        fin_dia = datetime.combine(fecha_hoy, datetime.max.time())

        total_infracciones = Registro.objects.filter(fecha_hora__range=(inicio_dia, fin_dia), infraccion__in=[2, 3, 4]).count()

        return total_infracciones

    def total_patentes_leidas(self):
        fecha_hoy = timezone.localtime(timezone.now())
        inicio_dia = datetime.combine(fecha_hoy, datetime.min.time())
        fin_dia = datetime.combine(fecha_hoy, datetime.max.time())

        total_leidas = Registro.objects.filter(fecha_hora__range=(inicio_dia, fin_dia), usuario=self.usuario).count()

        return total_leidas
                
    def creacion_modelo(self, patente, carpeta, image, infraccion, fecha_hora_str, archivo):
        path='C:/FTP/'+carpeta+'/'
        carpeta_usuario = Carpeta.objects.get(nombre=path)
        registro_kwargs = {
            "usuario": self.usuario,
            "patente": patente,
            "carpeta": carpeta_usuario,
            "imagen_binaria": image,
            "infraccion": infraccion,
        }

        # Validar si la fecha y hora es válida antes de agregarla al registro
        if fecha_hora_str.isdigit():
            fecha_hora = datetime.strptime(fecha_hora_str, '%Y%m%d%H%M%S')
            fecha_hora = timezone.make_aware(fecha_hora)
            registro_kwargs["fecha_hora"] = fecha_hora
                                
            if not Registro.objects.filter(patente=patente, fecha_hora=fecha_hora, carpeta=carpeta_usuario).exists():
                registro = Registro.objects.create(**registro_kwargs)
                print(f'---Registro con fecha y hora---')
                return registro
        else: 
            if not Registro.objects.filter(patente=patente, carpeta=carpeta_usuario).exists():
                registro = Registro.objects.create(**registro_kwargs)
                print(f'---Registro con fecha y hora nula---')
                return registro
            
    def descargar_imagen(self, carpeta, archivo):
        #ruta = 'C:/FTP/' + carpeta + '/' + archivo
        #ruta = 'C:/FTP/TCM_TRFX/KYJX90_20240401142721209.jpg'

        ruta = 'C:/FTP/' + carpeta + '/' + archivo
        print(f'Ruta del archivo: {ruta}')

        try:
            # Leer la imagen con OpenCV
            imagen = cv2.imread(ruta)

            if imagen is None:
                print(f'ERROR: No se pudo leer la imagen en {ruta}')
                return None

            # Convertir la imagen a formato de bytes
            _, buffer = cv2.imencode('.jpg', imagen)

            # Codificar la imagen en base64
            imagen_base64 = base64.b64encode(buffer).decode('utf-8')

            print("Longitud de la imagen en base64:", len(imagen_base64))
            return imagen_base64

        except FileNotFoundError:
            print(f'ERROR: El archivo {ruta} no fue encontrado.')
            return None
        except Exception as e:
            print(f'ERROR: Ocurrió un error al leer la imagen: {e}')
            return None

    def creacion_variables(self, event):
        archivo = event.src_path.split("/")[-1]  # Obtenemos nombre de la imagen
        carpeta = event.src_path.split("/")[2]    # Obtenemos el nombre de la carpeta
        if "unknown" not in archivo.lower() and "plate" not in archivo.lower():  # Si el archivo no contiene unknown o contiene plate, entonces lo procesamo            
            #print(f'Ruta completa: {event.src_path}')
            ruta = event.src_path
            print(f'Auto detectado: {archivo}')
            #print(f'Carpeta: {carpeta}')
            patente, fecha_hora_str = archivo.split("_", 1) 
            patente = patente[:6] #Obtenemos patente
            fecha_hora_str = fecha_hora_str[:14] #Obtenemos fecha y hora de la imagen
            print(f'Patente: {patente}')
            #print(f'Fecha y hora: {fecha_hora_str}')
        else:
            return None, None, None, None, None

        return archivo, carpeta, patente, fecha_hora_str, ruta

    async def enviar_notificacion(self, data, ubicacion, a, total_patentes, total_infracciones, image ):
        chat_consumer = self.obtener_chat_consumer(self.usuario.id)
        if chat_consumer:
            await chat_consumer.enviar_notificacion(data, ubicacion, a, total_patentes, total_infracciones, image 
            )
        #     print("Mensaje enviado desde ftp_monitor")
        # else:
        #     print("No se encontró la instancia del consumidor")

    def obtener_chat_consumer(self, usuario_id):
        group_name = f"usuario_{usuario_id}"
        for instance in PorticosConsumer.instances:
            if instance.group_name == group_name:
                return instance
        return None

    def obtener_infraccion(self, patente):
            if ListaNegra.objects.filter(patente=patente).exists():
                #print('Si patente está en lista negra...')
                return Infraccion.objects.get(id=2)
            else:
                #print('Patente está limpia')
                return Infraccion.objects.get(id=1)
        
from watchdog.observers import Observer
from threading import Lock

# Define una variable global para controlar si el monitoreo está en curso para cada usuario
MONITOREO_POR_USUARIO = {}
MONITOREO_LOCK = Lock()  # Lock para garantizar la consistencia del diccionario MONITOREO_POR_USUARIO

def iniciar_monitoreo_usuario(usuario, carpetas):
    global MONITOREO_POR_USUARIO
    
    with MONITOREO_LOCK:
        if isinstance(MONITOREO_POR_USUARIO, dict):
            if usuario.id not in MONITOREO_POR_USUARIO:
                MONITOREO_POR_USUARIO[usuario.id] = set()  
            observadores_activos = MONITOREO_POR_USUARIO[usuario.id]
            if not observadores_activos:  # Verificar si no hay sesiones activas para este usuario
                for carpeta in carpetas:
                    event_handler = MyHandler(usuario)  
                    observer = Observer()
                    observer.schedule(event_handler, carpeta, recursive=True)
                    observer.start()
                    observadores_activos.add(observer)  
                    print(f'Monitorización iniciada para: {usuario.username}')
                    print(f'Carpetas a monitorear: {carpeta}')
                MONITOREO_POR_USUARIO[usuario.id] = observadores_activos
            else:
                print(f'El usuario {usuario.username} ya tiene una sesión activa.')

def detener_monitoreo_usuario(usuario):
    global MONITOREO_POR_USUARIO
    with MONITOREO_LOCK:
        if isinstance(MONITOREO_POR_USUARIO, dict):
            if usuario.id in MONITOREO_POR_USUARIO:  # Verificar si la clave del usuario existe
                observadores = MONITOREO_POR_USUARIO.pop(usuario.id, set())  
                for observer in observadores:
                    observer.stop()  
                    observer.join()
            else:
                print(f'El usuario con ID {usuario.id} no está presente en el diccionario MONITOREO_POR_USUARIO.')



