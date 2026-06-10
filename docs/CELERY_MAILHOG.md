# Celery и MailHog в проекте UrbanWear

## 1. Назначение Celery

Celery используется для выполнения фоновых и периодических задач.

В проекте UrbanWear Celery применяется для отправки еженедельного отчёта по товарам с низким остатком.

Задача находится в файле:

shop/tasks.py

Название задачи:

shop.tasks.send_weekly_stock_report

## 2. Что делает задача

Задача выбирает товары, у которых остаток на складе меньше или равен 5.

После этого формируется текстовый отчёт, содержащий:

- название товара;
- артикул;
- категорию;
- бренд;
- текущий остаток.

Затем отчёт отправляется на почту администратора.

## 3. Настройки Celery

Настройки находятся в settings.py:

CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

В качестве брокера используется Redis.

## 4. Периодическая задача

В settings.py добавлен CELERY_BEAT_SCHEDULE.

Задача send_weekly_stock_report настроена как периодическая.

Интервал запуска:

один раз в 7 дней.

## 5. Назначение MailHog

MailHog используется для локального тестирования отправки писем.

Он перехватывает письма, отправленные Django, и показывает их в веб-интерфейсе.

Это удобно для разработки, потому что не нужно использовать реальную почту.

## 6. Настройки почты

В settings.py используются настройки:

EMAIL_HOST=localhost
EMAIL_PORT=1025
EMAIL_USE_TLS=False

MailHog принимает SMTP-сообщения на порту 1025.

Веб-интерфейс MailHog доступен на порту 8025.

## 7. Запуск Redis и MailHog

Для запуска используется Docker Compose:

docker compose up -d

Проверка контейнеров:

docker compose ps

## 8. Проверка MailHog

Открыть в браузере:

http://127.0.0.1:8025/

После вызова задачи письмо должно появиться в интерфейсе MailHog.

## 9. Проверка задачи вручную

Открыть Django shell:

python manage.py shell

Выполнить:

from shop.tasks import send_weekly_stock_report
send_weekly_stock_report()

Если MailHog запущен, письмо будет отправлено и появится в веб-интерфейсе.

## 10. Запуск Celery worker

В отдельном терминале:

celery -A urbanwear worker -l info

## 11. Запуск Celery beat

Во втором терминале:

celery -A urbanwear beat -l info

Celery beat отвечает за периодический запуск задач.
