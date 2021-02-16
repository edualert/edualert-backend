from django.utils import timezone

from edualert.academic_calendars.constants import SEMESTER_END_EVENTS
from edualert.academic_calendars.models import SchoolEvent
from edualert.academic_calendars.utils import get_current_academic_calendar
from edualert.catalogs.models import StudentCatalogPerYear
from edualert.study_classes.models import StudyClass


def calculate_student_placements():
    today = timezone.now().date()

    current_calendar = get_current_academic_calendar()
    if not current_calendar:
        return False

    corigente_event = SchoolEvent.objects.filter(event_type=SchoolEvent.EventTypes.CORIGENTE, academic_year_calendar=current_calendar).first()
    first_semester_run_dates = [current_calendar.first_semester.ends_at]
    second_semester_run_dates = [
        current_calendar.second_semester.ends_at,
        corigente_event.ends_at if corigente_event else None,
        *SchoolEvent.objects.filter(event_type__in=SEMESTER_END_EVENTS, semester=current_calendar.second_semester).values_list('ends_at', flat=True)
    ]

    if today not in [*first_semester_run_dates, *second_semester_run_dates]:
        return False

    set_rankings(current_calendar, today, second_semester_run_dates)

    return True


def set_rankings(current_calendar, today, second_semester_run_dates):
    school_rankings = {}

    for study_class in StudyClass.objects.filter(
        academic_year=current_calendar.academic_year
    ).prefetch_related(
        'student_catalogs_per_year',
        'students'
    ):
        school_id = study_class.school_unit_id
        catalogs = study_class.student_catalogs_per_year.all()

        class_averages_ranking_sem1 = set()
        class_averages_ranking_sem2 = set()
        class_averages_ranking_annual = set()
        class_absences_ranking_sem1 = set()
        class_absences_ranking_sem2 = set()
        class_absences_ranking_annual = set()

        for catalog in catalogs:
            class_averages_ranking_sem1.add(catalog.avg_sem1)
            class_averages_ranking_sem2.add(catalog.avg_sem2)
            class_averages_ranking_annual.add(catalog.avg_final),
            class_absences_ranking_sem1.add(catalog.abs_count_sem1)
            class_absences_ranking_sem2.add(catalog.abs_count_sem2)
            class_absences_ranking_annual.add(catalog.abs_count_annual)

        class_averages_ranking_sem1 = sorted(list(class_averages_ranking_sem1), key=lambda x: 0 if x is None else x, reverse=True)
        class_averages_ranking_sem2 = sorted(list(class_averages_ranking_sem2), key=lambda x: 0 if x is None else x, reverse=True)
        class_averages_ranking_annual = sorted(list(class_averages_ranking_annual), key=lambda x: 0 if x is None else x, reverse=True)
        class_absences_ranking_sem1 = sorted(list(class_absences_ranking_sem1), reverse=True)
        class_absences_ranking_sem2 = sorted(list(class_absences_ranking_sem2), reverse=True)
        class_absences_ranking_annual = sorted(list(class_absences_ranking_annual), reverse=True)

        if school_id not in school_rankings:
            catalogs_from_school = StudentCatalogPerYear.objects.filter(study_class__school_unit_id=school_id, academic_year=current_calendar.academic_year)
            school_averages_ranking_sem1 = set()
            school_averages_ranking_sem2 = set()
            school_averages_ranking_annual = set()
            school_absences_ranking_sem1 = set()
            school_absences_ranking_sem2 = set()
            school_absences_ranking_annual = set()

            for catalog in catalogs_from_school:
                school_averages_ranking_sem1.add(catalog.avg_sem1)
                school_averages_ranking_sem2.add(catalog.avg_sem2)
                school_averages_ranking_annual.add(catalog.avg_final)
                school_absences_ranking_sem1.add(catalog.abs_count_sem1)
                school_absences_ranking_sem2.add(catalog.abs_count_sem2)
                school_absences_ranking_annual.add(catalog.abs_count_sem2)

            school_averages_ranking_sem1 = sorted(list(school_averages_ranking_sem1), key=lambda x: 0 if x is None else x, reverse=True)
            school_averages_ranking_sem2 = sorted(list(school_averages_ranking_sem2), key=lambda x: 0 if x is None else x, reverse=True)
            school_averages_ranking_annual = sorted(list(school_averages_ranking_annual), key=lambda x: 0 if x is None else x, reverse=True)
            school_absences_ranking_sem1 = sorted(list(school_absences_ranking_sem1), reverse=True)
            school_absences_ranking_sem2 = sorted(list(school_absences_ranking_sem2), reverse=True)
            school_absences_ranking_annual = sorted(list(school_absences_ranking_annual), reverse=True)

            school_rankings[school_id] = {
                'school_averages_ranking_sem1': school_averages_ranking_sem1,
                'school_averages_ranking_sem2': school_averages_ranking_sem2,
                'school_averages_ranking_annual': school_averages_ranking_annual,
                'school_absences_ranking_sem1': school_absences_ranking_sem1,
                'school_absences_ranking_sem2': school_absences_ranking_sem2,
                'school_absences_ranking_annual': school_absences_ranking_annual
            }

        for catalog in catalogs:
            catalog.class_place_by_avg_sem1 = class_averages_ranking_sem1.index(catalog.avg_sem1) + 1
            catalog.class_place_by_abs_sem1 = class_absences_ranking_sem1.index(catalog.abs_count_sem1) + 1
            catalog.school_place_by_avg_sem1 = school_rankings[school_id]['school_averages_ranking_sem1'].index(catalog.avg_sem1) + 1
            catalog.school_place_by_abs_sem1 = school_rankings[school_id]['school_absences_ranking_sem1'].index(catalog.abs_count_sem1) + 1

            if today in second_semester_run_dates:
                catalog.class_place_by_avg_sem2 = class_averages_ranking_sem2.index(catalog.avg_sem2) + 1
                catalog.class_place_by_abs_sem2 = class_absences_ranking_sem2.index(catalog.abs_count_sem2) + 1
                catalog.class_place_by_avg_annual = class_averages_ranking_annual.index(catalog.avg_final) + 1
                catalog.class_place_by_abs_annual = class_absences_ranking_annual.index(catalog.abs_count_annual) + 1
                catalog.school_place_by_avg_sem2 = school_rankings[school_id]['school_averages_ranking_sem2'].index(catalog.avg_sem2) + 1
                catalog.school_place_by_abs_sem2 = school_rankings[school_id]['school_absences_ranking_sem2'].index(catalog.abs_count_sem2) + 1
                catalog.school_place_by_avg_annual = school_rankings[school_id]['school_averages_ranking_annual'].index(catalog.avg_final) + 1
                catalog.school_place_by_abs_annual = school_rankings[school_id]['school_absences_ranking_annual'].index(catalog.abs_count_annual) + 1

            catalog.save()
