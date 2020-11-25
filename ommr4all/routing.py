from channels.routing import ProtocolTypeRouter
from django.core.asgi import get_asgi_application

application = ProtocolTypeRouter({
    # (http->django views is added by default)
    'http': get_asgi_application(),
})