# consumers.py

from channels.generic.websocket import AsyncWebsocketConsumer
import json

class PorticosConsumer(AsyncWebsocketConsumer):
    instances = set()  # Almacén de instancias de consumidores

    async def connect(self):
        await self.accept()
        group_name = f"usuario_{self.scope['user'].id}"
        
        # Verificar si la instancia ya existe
        if self not in PorticosConsumer.instances:
            self.group_name = group_name
            PorticosConsumer.instances.add(self)  # Registrar la instancia
            print(f'Grupo {group_name}')
        else:
            # Si la instancia ya existe, no se acepta la conexión
            self.close()

    async def disconnect(self, close_code):
        PorticosConsumer.instances.remove(self)  # Eliminar la instancia al desconectar

    async def receive(self, text_data):
        pass

    async def enviar_notificacion(self, data, image):
        print(f'Websocket envio notificacion')
        message = {
            'type': 'registro_nuevo',
            'data':data,
            'image':image,
        }
        await self.send(text_data=json.dumps(message))
        print(f'Mensaje enviado')
        
    async def enviar_notificacion_desde_handler(self, message):
        # Este método permite recibir una notificación desde MyHandler
        await self.enviar_notificacion(message)