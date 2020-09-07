# Generated by Django 3.0.4 on 2020-06-17 10:14
import datetime
from calendar import monthrange

import django.contrib.postgres.fields.jsonb
from dateutil.relativedelta import relativedelta
from django.db import migrations
from django.utils import timezone

from edualert.common.constants import WEEKDAYS_MAP


def create_school_enrollment_stats(apps, schema_editor):
    today = timezone.now().date()
    SchoolUnitEnrollmentStats = apps.get_model('statistics', 'SchoolUnitEnrollmentStats')
    AcademicYearCalendar = apps.get_model('academic_calendars', 'AcademicYearCalendar')
    current_calendar = AcademicYearCalendar.objects.last()
    if not current_calendar:
        return

    months_since_academic_year_start = []
    date = current_calendar.first_semester.starts_at
    while date <= today:
        months_since_academic_year_start.append((date.year, date.month))
        date += relativedelta(months=1)

    for year, month in months_since_academic_year_start:
        days_in_month = monthrange(year, month)[1]
        if not SchoolUnitEnrollmentStats.objects.filter(month=month, year=year).exists():
            SchoolUnitEnrollmentStats.objects.create(
                month=month,
                year=year,
                daily_statistics=[
                    {
                        'count': 0,
                        'day': day,
                        'weekday': WEEKDAYS_MAP[datetime.datetime(year, month, day).weekday()]
                    } for day in range(1, days_in_month + 1)
                ]
            )


class Migration(migrations.Migration):

    dependencies = [
        ('statistics', '0003_auto_20200526_1522'),
    ]

    operations = [
        migrations.AlterField(
            model_name='schoolunitenrollmentstats',
            name='daily_statistics',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=list),
        ),
        migrations.RunPython(create_school_enrollment_stats, reverse_code=migrations.RunPython.noop)
    ]