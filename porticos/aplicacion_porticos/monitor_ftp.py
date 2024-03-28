import asyncio
import base64
from datetime import datetime
from io import BytesIO
from django.utils import timezone
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from ftplib import FTP

from aplicacion_porticos.consumers import PorticosConsumer

from aplicacion_porticos.models import Carpeta, Infraccion, ListaNegra, Registro


class MyHandler(FileSystemEventHandler):
    instances = PorticosConsumer.instances  # Obtener la misma variable de instancisas
    def __init__(self, usuario):
        super().__init__()
        self.ftp_host = '127.0.0.1'
        self.ftp_user = 'teraflex'
        self.ftp_passwd = 'Teraf2022.'
        self.ftp = None
        self.usuario = usuario

    def conectar_ftp(self):
        self.ftp = FTP(self.ftp_host)
        self.ftp.login(user=self.ftp_user, passwd=self.ftp_passwd)
        print(f'Conexión FTP establecida')

    def desconectar_ftp(self):
        if self.ftp:
            self.ftp.quit()

    def on_any_event(self, event):
        # Aquí puedes definir lo que deseas hacer cuando ocurra un evento
        if event.event_type == 'created':  # Si el evento generado es de creación de archivo == imagen nueva
            print(f'Llamamos metodo para archivo, carpeta, patente, fecha y ruta')
            archivo, carpeta, patente, fecha_hora_str, ruta = self.creacion_variables(event) #Obtengo archivo, carpeta, patente, fecha tomada y ruta

            # Verificamos si se obtuvieron valores válidos
            if archivo is None:
                print("Archivo ignorado. No se procesará.")
            else:
                print(f'Conectamos FTP')
                #self.conectar_ftp()

                print(f'Descargamos imagen')
                #image = self.descargar_imagen(carpeta, archivo) 
                image=''

                print(f'Verificamos infracciones en patente')
                infraccion = self.obtener_infraccion(patente)                

                print(f'---Creamos el modelo de Registro---')
                registro = self.creacion_modelo(patente, carpeta, image, infraccion, fecha_hora_str, archivo)

                print(f'Enviamos notificación')
                asyncio.run(self.enviar_notificacion(patente, image))
            
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
        #print(f'---Descargamos imagen binaria---')
        self.ftp.cwd(carpeta)
        #print(f'{carpeta}')
        with BytesIO() as file_content: #Descargamos la imagen
            self.ftp.retrbinary(f"RETR {archivo}", file_content.write)
            file_content.seek(0)

            imagen_base64 = base64.b64encode(file_content.read()).decode('utf-8') #Tenemos la imagen de forma binaria

        if imagen_base64: #Si la imagen se descargo de forma correcta
            # print(f'---Imagen descargada correctamente---')
            print("Longitud de la imagen en base64:", len(imagen_base64))
            file_content.seek(0)
            return imagen_base64

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

    async def enviar_notificacion(self, data, image):
        chat_consumer = self.obtener_chat_consumer(self.usuario.id)
        if chat_consumer:
            await chat_consumer.enviar_notificacion(data, image
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
        if usuario.id not in MONITOREO_POR_USUARIO:
            MONITOREO_POR_USUARIO[usuario.id] = []

        observadores = []
        for carpeta in carpetas:
            event_handler = MyHandler(usuario)  # Debes definir tu propia clase MyHandler
            observer = Observer()
            observer.schedule(event_handler, carpeta, recursive=True)
            observer.start()
            observadores.append(observer)

            print(f'Monitoreo iniciado para: {usuario.username}')
            print(f'Carpetas a monitorear {carpeta}')

        MONITOREO_POR_USUARIO[usuario.id].extend(observadores)

def detener_monitoreo_usuario(usuario):
    global MONITOREO_POR_USUARIO
    
    with MONITOREO_LOCK:
        observadores = MONITOREO_POR_USUARIO.pop(usuario.id, [])
        for observer in observadores:
            observer.stop()
            observer.join()
    
