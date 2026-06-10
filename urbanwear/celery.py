"""
Настройка Celery для проекта UrbanWear.

Celery используется для фоновых и периодических задач:
- отправка отчётов;
- обработка задач, которые не должны выполняться прямо во время HTTP-запроса.
"""

from __future__ import annotations

import os

from celery import Celery


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "urbanwear.settings")


app = Celery("urbanwear")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()