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

    async def enviar_notificacion(self, data, ubicacion, a, total_patentes, total_infracciones, image ):
        print(f'Websocket envio notificacion')
        message = {
            'type': 'registro_nuevo',
            'data':data,
            'ubicacion':ubicacion,
            'infraccion':a, #Si es 1 no hay infraccion, si es 2, mostrar pop up
            'total_patentes':total_patentes,
            'total_infracciones':total_infracciones,
            'image':image,
        }
        await self.send(text_data=json.dumps(message))
        print(f'Mensaje enviado')
        
    async def enviar_notificacion_desde_handler(self, message):
        # Este método permite recibir una notificación desde MyHandler
        await self.enviar_notificacion(message)

    @classmethod
    async def enviar_notificacion_global(cls, origen, destino, patente):
        message = {
            'type': 'notificacion',
            'origen': origen,
            'destino': destino,
            'patente': patente
        }
        await cls.broadcast_message(json.dumps(message))

    @classmethod
    async def broadcast_message(cls, message):
        for instance in cls.instances:
            await instance.send(text_data=message)