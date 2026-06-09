import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()

# En producción (DEBUG=False) Django no sirve /media/. WhiteNoise (middleware)
# ya sirve /static/; aquí añadimos las fotos de producto en /media/.
from django.conf import settings  # noqa: E402
from whitenoise import WhiteNoise  # noqa: E402

application = WhiteNoise(application)
application.add_files(str(settings.MEDIA_ROOT), prefix="media/")
