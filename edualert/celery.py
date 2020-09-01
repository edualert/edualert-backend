from __future__ import absolute_import, unicode_literals
from celery import Celery, shared_task
from celery.schedules import crontab

app = Celery('edualert')

app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'generate_next_study_year_task': {
        'task': 'edualert.common.tasks.generate_next_study_year_task',
        'schedule': crontab(hour=00, minute=00)
    },
    'create_school_unit_enrollment_stats_task': {
        'task': 'edualert.statistics.tasks.create_school_unit_enrollment_stats_task',
        'schedule': crontab(hour=00, minute=5, day_of_month=1)
    },
    'create_students_at_risk_counts_task': {
        'task': 'edualert.statistics.tasks.create_students_at_risk_counts_task',
        'schedule': crontab(hour=00, minute=10, day_of_month=1)
    },
    'calculate_students_risk_level_task': {
        'task': 'edualert.catalogs.tasks.calculate_students_risk_level_task',
        'schedule': crontab(hour=00, minute=15)
    },
    'send_alerts_for_risks_task': {
        'task': 'edualert.catalogs.tasks.send_alerts_for_risks_task',
        'schedule': crontab(hour=6, minute=30)
    },
    'calculate_students_placements_task': {
        'task': 'edualert.catalogs.tasks.calculate_students_placements_task',
        'schedule': crontab(hour=23, minute=59),
    },
}


@shared_task
def debug_task():
    print('Request:')
