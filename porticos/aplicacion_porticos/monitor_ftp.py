import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from ftplib import FTP
import base64
from io import BytesIO


from datetime import datetime
from django.utils import timezone

class MyHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.ftp_host = '127.0.0.1'
        self.ftp_user = 'teraflex'
        self.ftp_passwd = 'Teraf2022.'
        self.ftp = None

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
            archivo = event.src_path.split("/")[-1]  # Obtenemos nombre de la imagen
            carpeta = event.src_path.split("/")[2]    # Obtenemos el nombre de la carpeta
            if "unknown" not in archivo.lower() and "plate" not in archivo.lower():  # Si el archivo no contiene unknown o contiene plate, entonces lo procesamos
                print(f'Ruta completa: {event.src_path}')
                print(f'Auto detectado: {archivo}')
                print(f'Carpeta: {carpeta}')
                patente, fecha_hora_str = archivo.split("_", 1) 
                patente = patente[:6] #Obtenemos patente
                fecha_hora_str = fecha_hora_str[:14] #Obtenemos fecha y hora de la imagen
                print(f'Patente: {patente}')
                print(f'Fecha y hora: {fecha_hora_str}')

                print(f'---Descargamos imagen binaria---')
                
                try:
                    if not self.ftp: #Si no hay conexión ftp la crea
                        self.conectar_ftp()

                    self.ftp.cwd(carpeta) #Nos movemos a la carpeta que tenemos la imagen

                    with BytesIO() as file_content: #Descargamos la imagen
                        self.ftp.retrbinary(f"RETR {archivo}", file_content.write)
                        file_content.seek(0)

                        imagen_base64 = base64.b64encode(file_content.read()).decode('utf-8') #Tenemos la imagen de forma binaria

                        if imagen_base64: #Si la imagen se descargo de forma correcta
                            print(f'---Imagen descargada correctamente---')
                            print("Longitud de la imagen en base64:", len(imagen_base64))

                            print(f'---Creamos el modelo de Registro---')

                            print(f'Verificamos infracciones en patente')
                            #infraccion_instance = self.obtener_infraccion(patente)

                            #registro_kwargs = {
                            #    "usuario": self.usuario,
                            #    "patente": patente,
                            #    "carpeta": carpeta,
                            #    "imagen_binaria": imagen_base64,
                            #    "infraccion": infraccion_instance,
                            #}

                            # Validar si la fecha y hora es válida antes de agregarla al registro
                            if fecha_hora_str.isdigit():
                                fecha_hora = datetime.strptime(fecha_hora_str, '%Y%m%d%H%M%S')
                                fecha_hora = timezone.make_aware(fecha_hora)
                            #    registro_kwargs["fecha_hora"] = fecha_hora
                                
                             #   with self.lock:   Adquirir el bloqueo antes de la validación y creación del registro
                            #    if not Registro.objects.filter(patente=patente, fecha_hora=fecha_hora, carpeta=carpeta).exists():
                            #        registro = Registro.objects.create(**registro_kwargs)
                            #        print(f'---Registro con fecha y hora---')
                            else:
                             #    with self.lock:  Adquirir el bloqueo antes de la creación del registro
                            #    if not Registro.objects.filter(patente=patente, carpeta=carpeta).exists():
                            #        registro = Registro.objects.create(**registro_kwargs)
                            #        print(f'---Registro con fecha y hora nula---')

                                print(f'---Después de crear el modelo---')

                            self.ftp.delete(archivo) #Eliminamos el archivo de la carpepeta despues de utilizarlo
                            print(f"Archivo {archivo} eliminado del servidor FTP")

                            file_content.seek(0) #Restablecemos el puntero de la imagen a 0
                            
                except Exception as e:
                    print(f'Error al descargar y convertir la imagen a base64: {e}')

    #def obtener_infraccion(self, patente):
    #        if ListaNegra.objects.filter(patente=patente).exists():
    #            print('Si patente está en lista negra...')
    #            return Infraccion.objects.get(id=2)
    #        else:
    #            print('Patente está limpia')
    #            return Infraccion.objects.get(id=1)
        
def main():
    paths = ['C:/FTP/TCM TRFX/', 'C:/FTP/PTZ TRFX/']  # Lista de directorios a monitorear, puedes cambiarlos según tus necesidades
    event_handlers = []
    observers = []

    # Configurar un observador para cada carpeta
    for path in paths:
        event_handler = MyHandler()
        observer = Observer()
        observer.schedule(event_handler, path, recursive=True)
        observer.start()
        event_handlers.append(event_handler)
        observers.append(observer)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        for observer in observers:
            observer.stop()
        for observer in observers:
            observer.join()

if __name__ == "__main__":
    main()
