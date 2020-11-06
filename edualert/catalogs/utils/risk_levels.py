from django.utils import timezone

from edualert.academic_calendars.utils import get_current_academic_calendar, get_second_semester_end_events
from edualert.academic_programs.models import AcademicProgram
from edualert.catalogs.models import StudentCatalogPerSubject, StudentCatalogPerYear
from edualert.catalogs.utils import has_technological_category, get_current_semester
from edualert.profiles.constants import ABANDONMENT_RISK_1_LABEL, ABANDONMENT_RISK_2_LABEL
from edualert.profiles.models import Label, UserProfile
from edualert.schools.models import RegisteredSchoolUnit
from edualert.statistics.models import StudentAtRiskCounts
from edualert.study_classes.models import StudyClass


def calculate_students_risk_level():
    today = timezone.now().date()
    thirty_days_ago = today - timezone.timedelta(days=30)

    current_calendar = get_current_academic_calendar()
    if not current_calendar:
        return
    second_semester_end_events = get_second_semester_end_events(current_calendar)

    risk_1_label = Label.objects.filter(text=ABANDONMENT_RISK_1_LABEL).first()
    risk_2_label = Label.objects.filter(text=ABANDONMENT_RISK_2_LABEL).first()
    risk_stats_map = get_mapped_risk_stats(today.year, today.month)
    students_at_risk_count_by_country = 0

    catalogs_per_subject_to_update = []
    students_to_update = []

    for school_unit in RegisteredSchoolUnit.objects.all():
        students_at_risk_count_by_school = 0
        is_technological_school = has_technological_category(school_unit)

        catalogs_per_year = StudentCatalogPerYear.objects.filter(academic_year=current_calendar.academic_year,
                                                                 student__is_active=True,
                                                                 study_class__school_unit_id=school_unit.id) \
            .select_related('student')
        catalogs_per_subject = get_mapped_catalogs_per_subject(current_calendar.academic_year, school_unit.id)

        for catalog in catalogs_per_year:
            current_semester = get_current_semester(today, current_calendar, second_semester_end_events,
                                                    catalog.study_class.class_grade_arabic, is_technological_school)
            student = catalog.student
            student.is_at_risk = False
            student.risk_description = None
            student.labels.remove(risk_1_label, risk_2_label)

            max_attendance_risk_level = 0
            max_grades_risk_level = 0
            behavior_risk_level = 0

            student_catalogs_per_subject = catalogs_per_subject.get(catalog.student_id, [])
            for catalog_per_subject in student_catalogs_per_subject:
                catalog_per_subject.is_at_risk = False

                # Check attendance
                attendance_risk_level = get_attendance_risk_level(catalog_per_subject, thirty_days_ago)
                if attendance_risk_level > 0:
                    catalog_per_subject.is_at_risk = True
                    if attendance_risk_level > max_attendance_risk_level:
                        max_attendance_risk_level = attendance_risk_level

                # Check grades
                if current_semester != 1 and catalog_per_subject.subject_name in ['Matematică', 'Limba Română', 'Limba și literatura română']:
                    grades_risk_level = get_grades_risk_level(catalog_per_subject, current_semester)
                    if grades_risk_level > 0:
                        catalog_per_subject.is_at_risk = True
                        if grades_risk_level > max_grades_risk_level:
                            max_grades_risk_level = grades_risk_level

                catalogs_per_subject_to_update.append(catalog_per_subject)

            if current_semester != 1:
                # Check behavior
                behavior_risk_level = get_behavior_risk_level(catalog, current_semester)

            # Set corresponding risk labels & description
            set_student_risk_level(student, risk_1_label, risk_2_label, max_attendance_risk_level, max_grades_risk_level, behavior_risk_level)

            students_to_update.append(student)
            if student.is_at_risk:
                students_at_risk_count_by_school += 1

        set_school_unit_students_at_risk_count(school_unit, students_at_risk_count_by_school, risk_stats_map, today.day)
        students_at_risk_count_by_country += students_at_risk_count_by_school

    if catalogs_per_subject_to_update:
        StudentCatalogPerSubject.objects.bulk_update(catalogs_per_subject_to_update, ['is_at_risk'], batch_size=100)
    if students_to_update:
        UserProfile.objects.bulk_update(students_to_update, ['is_at_risk', 'risk_description'], batch_size=100)

    country_risk_stats = risk_stats_map.get('by_country')
    set_daily_risk_count(country_risk_stats, students_at_risk_count_by_country, today.day)

    set_academic_programs_students_at_risk_count(current_calendar.academic_year)
    set_study_classes_students_at_risk_count(current_calendar.academic_year, risk_stats_map, today.day)


def get_mapped_risk_stats(year, month):
    student_at_risk_counts = StudentAtRiskCounts.objects.filter(year=year, month=month)
    risk_stats_map = {
        'by_school': {},
        'by_study_class': {}
    }

    for risk_stats in student_at_risk_counts:
        if risk_stats.by_country:
            risk_stats_map['by_country'] = risk_stats
        elif risk_stats.school_unit:
            risk_stats_map['by_school'][risk_stats.school_unit_id] = risk_stats
        elif risk_stats.study_class:
            risk_stats_map['by_study_class'][risk_stats.study_class_id] = risk_stats

    return risk_stats_map


def get_mapped_catalogs_per_subject(academic_year, school_unit_id):
    catalogs = StudentCatalogPerSubject.objects.filter(academic_year=academic_year, student__is_active=True,
                                                       study_class__school_unit_id=school_unit_id) \
        .select_related('student', 'study_class')

    catalogs_map = {}
    for catalog in catalogs:
        if catalog.student_id not in catalogs_map:
            catalogs_map[catalog.student_id] = []
        catalogs_map[catalog.student_id].append(catalog)

    return catalogs_map


def get_attendance_risk_level(catalog_per_subject, date_limit):
    absences_count = catalog_per_subject.absences.filter(taken_at__gte=date_limit, is_founded=False).count()
    attendance_risk_level = 0
    if 1 <= absences_count <= 3:
        attendance_risk_level = 1
    elif absences_count > 3:
        attendance_risk_level = 2
    return attendance_risk_level


def get_grades_risk_level(catalog_per_subject, current_semester):
    sem_average = catalog_per_subject.avg_sem1 if current_semester == 2 else catalog_per_subject.avg_sem2
    grades_risk_level = 0
    if sem_average:
        if 5 <= sem_average <= 6:
            grades_risk_level = 1
        elif sem_average <= 4:
            grades_risk_level = 2
    return grades_risk_level


def get_behavior_risk_level(catalog_per_year, current_semester):
    behavior_grade = catalog_per_year.behavior_grade_sem1 if current_semester == 2 else catalog_per_year.behavior_grade_sem2
    behavior_risk_level = 0
    if behavior_grade:
        if behavior_grade in [8, 9]:
            behavior_risk_level = 1
        elif behavior_grade <= 7:
            behavior_risk_level = 2
    return behavior_risk_level


def set_student_risk_level(student, risk_1_label, risk_2_label, max_attendance_risk_level, max_grades_risk_level, behavior_risk_level):
    if max_attendance_risk_level == 2 or max_grades_risk_level == 2 or behavior_risk_level == 2:
        student.is_at_risk = True
        student.labels.add(risk_2_label)
        risk_description = ''
        if max_attendance_risk_level == 2:
            risk_description += '4 sau mai multe absențe nemotivate'
        if max_grades_risk_level == 2:
            risk_description += 'Notă Limba română sau Matematică sub 5' if risk_description == '' else ' și notă Limba română sau Matematică sub 5'
        if behavior_risk_level == 2:
            risk_description += 'Notă purtare sub 8' if risk_description == '' else ' și notă purtare sub 8'
        student.risk_description = risk_description
    elif max_attendance_risk_level == 1 or max_grades_risk_level == 1 or behavior_risk_level == 1:
        student.is_at_risk = True
        student.labels.add(risk_1_label)
        risk_description = ''
        if max_attendance_risk_level == 1:
            risk_description += '1-3 absențe nemotivate'
        if max_grades_risk_level == 1:
            risk_description += '5-6 notă Limba română sau Matematică' if risk_description == '' else ' și 5-6 notă Limba română sau Matematică'
        if behavior_risk_level == 1:
            risk_description += '8-9 notă purtare' if risk_description == '' else ' și 8-9 notă purtare'
        student.risk_description = risk_description


def set_daily_risk_count(risk_stats, students_at_risk_count, current_day):
    if not risk_stats:
        return

    for index, daily_count in enumerate(risk_stats.daily_counts):
        if daily_count['day'] == current_day:
            risk_stats.daily_counts[index]['count'] = students_at_risk_count
            risk_stats.save()
            break


def set_school_unit_students_at_risk_count(school_unit, count, risk_stats_map, current_day):
    school_unit.students_at_risk_count = count
    school_unit.save()
    school_risk_stats = risk_stats_map['by_school'].get(school_unit.id)
    set_daily_risk_count(school_risk_stats, count, current_day)


def set_academic_programs_students_at_risk_count(academic_year):
    for academic_program in AcademicProgram.objects.filter(academic_year=academic_year):
        academic_program.students_at_risk_count = UserProfile.objects.filter(user_role=UserProfile.UserRoles.STUDENT, is_active=True, is_at_risk=True,
                                                                             student_in_class__academic_program_id=academic_program.id).count()
        academic_program.save()


def set_study_classes_students_at_risk_count(academic_year, risk_stats_map, current_day):
    for study_class in StudyClass.objects.filter(academic_year=academic_year):
        students_at_risk_count_by_study_class = UserProfile.objects.filter(user_role=UserProfile.UserRoles.STUDENT, is_active=True, is_at_risk=True,
                                                                           student_in_class_id=study_class.id).count()
        study_class.students_at_risk_count = students_at_risk_count_by_study_class
        study_class.save()

        study_class_risk_stats = risk_stats_map['by_study_class'].get(study_class.id)
        set_daily_risk_count(study_class_risk_stats, students_at_risk_count_by_study_class, current_day)
