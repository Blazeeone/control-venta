import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sistema.settings")

from sistema.wsgi import application

__all__ = ["application"]
