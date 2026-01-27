from celery import Celery
from celery.schedules import crontab

app = Celery('online_cinema')

app.conf.broker_url = 'redis://localhost:6379/0'
app.conf.result_backend = 'redis://localhost:6379/0'

app.conf.beat_schedule = {
    'cleanup-expired-tokens-nightly': {
        'task': 'online_cinema.database.tasks.cleanup_expired_tokens',
        'schedule': crontab(hour=0, minute=0),
    },
}

app.autodiscover_tasks(['online_cinema.database'])
