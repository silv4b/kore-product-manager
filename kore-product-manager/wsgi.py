import os
from pathlib import Path

from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kore-product-manager.settings")

application = get_wsgi_application()
BASE_DIR = Path(__file__).resolve().parent.parent

# Caminhos das pastas
STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_SRC = BASE_DIR / "static"

# Inicializa o WhiteNoise
application = WhiteNoise(application)

# SÓ adiciona as pastas se elas realmente existirem no disco
if STATIC_ROOT.exists():
    application.add_files(str(STATIC_ROOT), prefix="static/")

if STATIC_SRC.exists():
    application.add_files(str(STATIC_SRC), prefix="static/")

app = application
