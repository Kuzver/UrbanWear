"""
Инициализация Celery при запуске Django-проекта.
"""

from .celery import app as celery_app


__all__ = ("celery_app",)