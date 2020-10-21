import math

from celery import shared_task
from django.db.models import Avg, Q, Sum
from django.utils import timezone

from edualert.catalogs.models import StudentCatalogPerSubject, SubjectGrade, StudentCatalogPerYear
from edualert.profiles.constants import FAILING_1_SUBJECT_LABEL, FAILING_2_SUBJECTS_LABEL
from edualert.profiles.models import UserProfile, Label
from edualert.statistics.models import SchoolUnitStats
from edualert.study_classes.models import StudyClass
from edualert.subjects.models import Subject


@shared_task
def calculate_students_risk_level_task():
    from edualert.catalogs.utils import calculate_students_risk_level
    calculate_students_risk_level()


@shared_task
def send_alerts_for_risks_task():
    from edualert.catalogs.utils import send_alerts_for_risks
    send_alerts_for_risks()


@shared_task
def send_alerts_for_school_situation_task():
    from edualert.catalogs.utils import send_alerts_for_school_situation
    send_alerts_for_school_situation()


@shared_task
def calculate_students_placements_task():
    from edualert.catalogs.utils import calculate_student_placements
    calculate_student_placements()


@shared_task()
def create_behavior_grades_task(student_ids):
    coordination_subject = Subject.objects.get(is_coordination=True)
    taken_at = timezone.now().date()
    grades = []
    catalogs_to_update = []

    for student_id in student_ids:
        student = UserProfile.objects.filter(id=student_id, user_role=UserProfile.UserRoles.STUDENT).first()
        if not student:
            continue

        catalog = StudentCatalogPerSubject.objects.filter(student_id=student_id, study_class_id=student.student_in_class.id,
                                                          subject_id=coordination_subject.id).first()
        catalog.avg_sem1 = 10
        catalog.avg_sem2 = 10
        catalog.avg_annual = 10
        catalog.avg_final = 10
        catalogs_to_update.append(catalog)

        for semester in [1, 2]:
            grades.append(
                SubjectGrade(catalog_per_subject=catalog, student=student, subject_name=coordination_subject.name,
                             academic_year=catalog.academic_year, semester=semester, taken_at=taken_at,
                             grade_type=SubjectGrade.GradeTypes.REGULAR, grade=10)
            )
    SubjectGrade.objects.bulk_create(grades)
    StudentCatalogPerSubject.objects.bulk_update(catalogs_to_update, ['avg_sem1', 'avg_sem2', 'avg_annual', 'avg_final'])


@shared_task()
def update_behavior_grades_task(student_id, semester, grade):
    student = UserProfile.objects.filter(id=student_id, user_role=UserProfile.UserRoles.STUDENT).first()
    if not student:
        return

    catalog = StudentCatalogPerYear.objects.filter(student_id=student_id, study_class=student.student_in_class).first()
    if not catalog:
        return

    if semester == 1:
        catalog.behavior_grade_sem1 = grade
    else:
        catalog.behavior_grade_sem2 = grade

    catalog.behavior_grade_annual = (catalog.behavior_grade_sem1 + catalog.behavior_grade_sem2) / 2
    catalog.save()
    update_averages_for_students_task([student_id], catalog.study_class_id, catalog.academic_year)


@shared_task()
def update_averages_for_students_task(student_ids, study_class_id, academic_year):
    students = []
    for student_id in set(student_ids):
        student = UserProfile.objects.filter(id=student_id, user_role=UserProfile.UserRoles.STUDENT).first()
        if student:
            students.append(student)
    if not students:
        return

    study_class = StudyClass.objects.get(id=study_class_id)
    core_subject = study_class.academic_program.core_subject

    for student in students:
        # Update averages for student's catalog per year
        update_catalog_per_year_averages(student.id, study_class.id, core_subject)

    # Update averages for study class
    update_study_class_averages(study_class)

    academic_program = study_class.academic_program
    if academic_program:
        # Update averages for academic profile
        update_academic_program_averages(academic_program)

    # Update averages for school_unit
    update_school_unit_averages(study_class.school_unit_id, academic_year)


def update_catalog_per_year_averages(student_id, study_class_id, core_subject):
    catalog = StudentCatalogPerYear.objects.filter(student_id=student_id, study_class_id=study_class_id).first()
    if not catalog:
        return

    aggregates = StudentCatalogPerSubject.objects \
        .filter(student_id=student_id, study_class_id=study_class_id, is_enrolled=True, is_exempted=False) \
        .aggregate(Avg('avg_sem1'), Avg('avg_sem2'), Avg('avg_annual'), Avg('avg_final'))
    catalog.avg_sem1 = math.floor(aggregates['avg_sem1__avg'] * 100) / 100 if aggregates['avg_sem1__avg'] else None
    catalog.avg_sem2 = math.floor(aggregates['avg_sem2__avg'] * 100) / 100 if aggregates['avg_sem2__avg'] else None
    catalog.avg_annual = math.floor(aggregates['avg_annual__avg'] * 100) / 100 if aggregates['avg_annual__avg'] else None
    catalog.avg_final = math.floor(aggregates['avg_final__avg'] * 100) / 100 if aggregates['avg_final__avg'] else None
    catalog.save()

    subjects_ids = [core_subject.id] if core_subject else []
    catalog.second_examinations_count = \
        StudentCatalogPerSubject.objects.filter(
            Q(avg_sem1__lt=5) | Q(avg_sem1__lt=6, subject_id__in=subjects_ids),
            student_id=student_id, study_class_id=study_class_id
        ).union(StudentCatalogPerSubject.objects.filter(
            Q(avg_sem2__lt=5) | Q(avg_sem2__lt=6, subject_id__in=subjects_ids),
            student_id=student_id, study_class_id=study_class_id
        ), all=True).count()
    catalog.save()

    label_for_one = Label.objects.filter(text=FAILING_1_SUBJECT_LABEL).first()
    label_for_two = Label.objects.filter(text=FAILING_2_SUBJECTS_LABEL).first()
    catalog.student.labels.remove(label_for_one)
    catalog.student.labels.remove(label_for_two)
    if catalog.second_examinations_count == 1:
        catalog.student.labels.add(label_for_one)
    elif catalog.second_examinations_count == 2:
        catalog.student.labels.add(label_for_two)


def update_study_class_averages(study_class):
    aggregates = study_class.student_catalogs_per_year \
        .aggregate(Avg('avg_sem1'), Avg('avg_sem2'), Avg('avg_final'))
    study_class.avg_sem1 = math.floor(aggregates['avg_sem1__avg'] * 100) / 100 if aggregates['avg_sem1__avg'] else None
    study_class.avg_sem2 = math.floor(aggregates['avg_sem2__avg'] * 100) / 100 if aggregates['avg_sem2__avg'] else None
    study_class.avg_annual = math.floor(aggregates['avg_final__avg'] * 100) / 100 if aggregates['avg_final__avg'] else None
    study_class.save()


def update_academic_program_averages(academic_program):
    aggregates = StudentCatalogPerYear.objects.filter(study_class__academic_program_id=academic_program.id) \
        .aggregate(Avg('avg_sem1'), Avg('avg_sem2'), Avg('avg_final'))
    academic_program.avg_sem1 = math.floor(aggregates['avg_sem1__avg'] * 100) / 100 if aggregates['avg_sem1__avg'] else None
    academic_program.avg_sem2 = math.floor(aggregates['avg_sem2__avg'] * 100) / 100 if aggregates['avg_sem2__avg'] else None
    academic_program.avg_annual = math.floor(aggregates['avg_final__avg'] * 100) / 100 if aggregates['avg_final__avg'] else None
    academic_program.save()


def update_school_unit_averages(school_unit_id, academic_year):
    stats = SchoolUnitStats.objects.filter(school_unit_id=school_unit_id, academic_year=academic_year).first()
    if not stats:
        return

    aggregates = StudentCatalogPerYear.objects.filter(study_class__school_unit_id=school_unit_id) \
        .aggregate(Avg('avg_sem1'), Avg('avg_sem2'), Avg('avg_final'))
    stats.avg_sem1 = math.floor(aggregates['avg_sem1__avg'] * 100) / 100 if aggregates['avg_sem1__avg'] else None
    stats.avg_sem2 = math.floor(aggregates['avg_sem2__avg'] * 100) / 100 if aggregates['avg_sem2__avg'] else None
    stats.avg_annual = math.floor(aggregates['avg_final__avg'] * 100) / 100 if aggregates['avg_final__avg'] else None
    stats.save()


@shared_task()
def update_absences_counts_for_students_task(catalog_ids):
    catalogs = []
    for catalog_id in set(catalog_ids):
        catalog = StudentCatalogPerSubject.objects.filter(id=catalog_id).first()
        if catalog:
            catalogs.append(catalog)
    if not catalogs:
        return
    study_class = catalogs[0].study_class

    for catalog in catalogs:
        # Update absences for student's catalog per year
        update_catalog_per_year_absences(catalog.student_id, study_class.id)

    # Update absences averages for study class
    study_class.refresh_from_db()  # because we updated the averages
    update_study_class_absences(study_class)

    academic_program = study_class.academic_program
    if academic_program:
        # Update absences averages for academic profile
        update_academic_program_absences(academic_program)

    # Update absences averages for school_unit
    update_school_unit_absences(study_class.school_unit_id, study_class.academic_year)


def update_catalog_per_year_absences(student_id, study_class_id):
    catalog = StudentCatalogPerYear.objects.filter(student_id=student_id, study_class_id=study_class_id).first()
    if not catalog:
        return

    aggregates = StudentCatalogPerSubject.objects \
        .filter(student_id=student_id, study_class_id=study_class_id, is_enrolled=True) \
        .aggregate(Sum('abs_count_sem1'), Sum('abs_count_sem2'), Sum('abs_count_annual'),
                   Sum('unfounded_abs_count_sem1'), Sum('unfounded_abs_count_sem2'), Sum('unfounded_abs_count_annual'),
                   Sum('founded_abs_count_sem1'), Sum('founded_abs_count_sem2'), Sum('founded_abs_count_annual'))
    catalog.abs_count_sem1 = aggregates['abs_count_sem1__sum']
    catalog.abs_count_sem2 = aggregates['abs_count_sem2__sum']
    catalog.abs_count_annual = aggregates['abs_count_annual__sum']
    catalog.unfounded_abs_count_sem1 = aggregates['unfounded_abs_count_sem1__sum']
    catalog.unfounded_abs_count_sem2 = aggregates['unfounded_abs_count_sem2__sum']
    catalog.unfounded_abs_count_annual = aggregates['unfounded_abs_count_annual__sum']
    catalog.founded_abs_count_sem1 = aggregates['founded_abs_count_sem1__sum']
    catalog.founded_abs_count_sem2 = aggregates['founded_abs_count_sem2__sum']
    catalog.founded_abs_count_annual = aggregates['founded_abs_count_annual__sum']
    catalog.save()


def update_study_class_absences(study_class):
    aggregates = study_class.student_catalogs_per_year \
        .aggregate(Avg('unfounded_abs_count_sem1'), Avg('unfounded_abs_count_sem2'), Avg('unfounded_abs_count_annual'))
    study_class.unfounded_abs_avg_sem1 = int(aggregates['unfounded_abs_count_sem1__avg'])
    study_class.unfounded_abs_avg_sem2 = int(aggregates['unfounded_abs_count_sem2__avg'])
    study_class.unfounded_abs_avg_annual = int(aggregates['unfounded_abs_count_annual__avg'])
    study_class.save()


def update_academic_program_absences(academic_program):
    aggregates = StudentCatalogPerYear.objects.filter(study_class__academic_program_id=academic_program.id) \
        .aggregate(Avg('unfounded_abs_count_sem1'), Avg('unfounded_abs_count_sem2'), Avg('unfounded_abs_count_annual'))
    academic_program.unfounded_abs_avg_sem1 = int(aggregates['unfounded_abs_count_sem1__avg'])
    academic_program.unfounded_abs_avg_sem2 = int(aggregates['unfounded_abs_count_sem2__avg'])
    academic_program.unfounded_abs_avg_annual = int(aggregates['unfounded_abs_count_annual__avg'])
    academic_program.save()


def update_school_unit_absences(school_unit_id, academic_year):
    stats = SchoolUnitStats.objects.filter(school_unit_id=school_unit_id, academic_year=academic_year).first()
    if not stats:
        return

    aggregates = StudentCatalogPerYear.objects.filter(study_class__school_unit_id=school_unit_id) \
        .aggregate(Avg('unfounded_abs_count_sem1'), Avg('unfounded_abs_count_sem2'), Avg('unfounded_abs_count_annual'))
    stats.unfounded_abs_avg_sem1 = int(aggregates['unfounded_abs_count_sem1__avg'])
    stats.unfounded_abs_avg_sem2 = int(aggregates['unfounded_abs_count_sem2__avg'])
    stats.unfounded_abs_avg_annual = int(aggregates['unfounded_abs_count_annual__avg'])
    stats.save()
