# routing.py

from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from aplicacion_porticos.consumers import PorticosConsumer
from channels.auth import AuthMiddlewareStack

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter([
            path(r'ws/porticos/', PorticosConsumer.as_asgi()),
        ]),
    ),
})


