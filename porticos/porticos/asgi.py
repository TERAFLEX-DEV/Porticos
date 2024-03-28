# asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter
from porticos.routing import application as routing_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'porticos.settings')

# Configura la aplicación de Django
django_application = get_asgi_application()

# Configura la aplicación para manejar solicitudes HTTP y WebSocket
application = ProtocolTypeRouter({
    'http': django_application,
    'websocket': routing_application,
})
