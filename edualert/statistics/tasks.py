import datetime
from calendar import monthrange

from celery import shared_task
from dateutil.relativedelta import relativedelta
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from edualert.academic_calendars.utils import get_current_academic_calendar
from edualert.common.constants import WEEKDAYS_MAP
from edualert.schools.models import RegisteredSchoolUnit
from edualert.statistics.models import StudentAtRiskCounts, SchoolUnitEnrollmentStats
from edualert.study_classes.models import StudyClass


@shared_task
def create_students_at_risk_counts_task():
    today = timezone.now().date()
    days_in_month = monthrange(today.year, today.month)[1]
    current_calendar = get_current_academic_calendar()
    if not current_calendar:
        return

    for school_unit in RegisteredSchoolUnit.objects.all():
        StudentAtRiskCounts.objects.create(
            month=today.month,
            year=today.year,
            school_unit=school_unit,
            daily_counts=[
                {
                    'day': day,
                    'weekday': WEEKDAYS_MAP[datetime.datetime(today.year, today.month, day).weekday()],
                    'count': 0
                } for day in range(1, days_in_month + 1)
            ]
        )
        for study_class in school_unit.study_classes.filter(academic_year=current_calendar.academic_year):
            StudentAtRiskCounts.objects.create(
                month=today.month,
                year=today.year,
                study_class=study_class,
                daily_counts=[
                    {
                        'day': day,
                        'weekday': WEEKDAYS_MAP[datetime.datetime(today.year, today.month, day).weekday()],
                        'count': 0
                    } for day in range(1, days_in_month + 1)
                ]
            )

    StudentAtRiskCounts.objects.create(
        month=today.month,
        year=today.year,
        by_country=True,
        daily_counts=[
            {
                'day': day,
                'weekday': WEEKDAYS_MAP[datetime.datetime(today.year, today.month, day).weekday()],
                'count': 0
            } for day in range(1, days_in_month + 1)
        ]
    )


@shared_task
def create_students_at_risk_counts_for_school_unit_task(school_unit_id):
    try:
        school_unit = RegisteredSchoolUnit.objects.get(id=school_unit_id)
    except ObjectDoesNotExist:
        return

    current_calendar = get_current_academic_calendar()
    if not current_calendar:
        return

    months_since_academic_year_start = get_months_since_academic_calendar_start(current_calendar)
    objects_to_create = []
    for year, month in months_since_academic_year_start:
        days_in_month = monthrange(year, month)[1]
        if not StudentAtRiskCounts.objects.filter(month=month, year=year, school_unit=school_unit).exists():
            objects_to_create.append(
                StudentAtRiskCounts(
                    month=month,
                    year=year,
                    school_unit=school_unit,
                    daily_counts=[
                        {
                            'count': 0,
                            'day': day,
                            'weekday': WEEKDAYS_MAP[datetime.datetime(year, month, day).weekday()]
                        } for day in range(1, days_in_month + 1)
                    ]
                )
            )
    StudentAtRiskCounts.objects.bulk_create(objects_to_create)


@shared_task
def create_students_at_risk_counts_for_study_class_task(study_class_id):
    try:
        study_class = StudyClass.objects.get(id=study_class_id)
    except ObjectDoesNotExist:
        return

    current_calendar = get_current_academic_calendar()
    if not current_calendar:
        return

    months_since_academic_year_start = get_months_since_academic_calendar_start(current_calendar)
    objects_to_create = []
    for year, month in months_since_academic_year_start:
        days_in_month = monthrange(year, month)[1]
        if not StudentAtRiskCounts.objects.filter(month=month, year=year, study_class=study_class).exists():
            objects_to_create.append(
                StudentAtRiskCounts(
                    month=month,
                    year=year,
                    study_class=study_class,
                    daily_counts=[
                        {
                            'count': 0,
                            'day': day,
                            'weekday': WEEKDAYS_MAP[datetime.datetime(year, month, day).weekday()]
                        } for day in range(1, days_in_month + 1)
                    ]
                )
            )
    StudentAtRiskCounts.objects.bulk_create(objects_to_create)


@shared_task
def create_school_unit_enrollment_stats_task():
    today = timezone.now().date()
    days_in_month = monthrange(today.year, today.month)[1]
    if not SchoolUnitEnrollmentStats.objects.filter(month=today.month, year=today.year).exists():
        SchoolUnitEnrollmentStats.objects.create(
            month=today.month,
            year=today.year,
            daily_statistics=[{
                'count': 0,
                'day': day,
                'weekday': WEEKDAYS_MAP[datetime.datetime(today.year, today.month, day).weekday()]
            } for day in range(1, days_in_month + 1)]
        )


@shared_task
def update_school_unit_enrollment_stats_task():
    today = timezone.now().date()

    stats = SchoolUnitEnrollmentStats.objects.get_or_create(month=today.month, year=today.year)[0]

    for index, daily_stat in enumerate(stats.daily_statistics):
        if daily_stat['day'] == today.day:
            stats.daily_statistics[index]['count'] += 1
            stats.save()
            break


def get_months_since_academic_calendar_start(current_calendar):
    today = timezone.now().date()
    date = current_calendar.first_semester.starts_at.replace(day=1)

    months = []
    while date <= today:
        months.append((date.year, date.month))
        date += relativedelta(months=1)

    return months
