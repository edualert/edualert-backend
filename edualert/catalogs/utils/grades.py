import decimal
import math

from django.db.models import Q

from edualert.catalogs.models import SubjectGrade, ExaminationGrade
from edualert.catalogs.tasks import update_averages_for_students_task
from edualert.schools.constants import BEHAVIOR_GRADE_EXCEPTIONS_PROFILES, PROFILES_WITH_CORE_SUBJECTS
from edualert.subjects.models import ProgramSubjectThrough


def grades_mean(grades):
    avg = sum(grades) / len(grades)
    return decimal.Decimal(avg).quantize(decimal.Decimal('.01'))


def normal_round(n):
    if n - math.floor(n) < 0.5:
        return math.floor(n)
    return math.ceil(n)


def compute_averages(catalogs, semester, is_async=True):
    if len(catalogs) == 0:
        return

    study_class = catalogs[0].study_class
    weekly_hours_count = ProgramSubjectThrough.objects \
        .get(Q(academic_program_id=study_class.academic_program_id) |
             Q(generic_academic_program_id=study_class.academic_program.generic_academic_program_id),
             subject_id=catalogs[0].subject_id, class_grade=study_class.class_grade).weekly_hours_count

    student_ids = []
    for catalog in catalogs:
        student_ids.append(catalog.student_id)
        grades = catalog.grades.filter(semester=semester)
        if len(grades) < weekly_hours_count + 1:
            set_avg_null(catalog, semester)
            continue

        if catalog.wants_thesis:
            thesis = None
            for grade in grades:
                if grade.grade_type == SubjectGrade.GradeTypes.THESIS:
                    thesis = grade
                    break
            if not thesis:
                set_avg_null(catalog, semester)
                continue
            sem_avg = (grades_mean([grade.grade for grade in grades if grade.grade_type == SubjectGrade.GradeTypes.REGULAR]) * 3 + thesis.grade) / 4
        else:
            sem_avg = grades_mean([grade.grade for grade in grades])

        if semester == 1:
            catalog.avg_sem1 = normal_round(sem_avg)
        else:
            catalog.avg_sem2 = normal_round(sem_avg)
            if catalog.avg_sem1:
                catalog.avg_annual = (catalog.avg_sem1 + catalog.avg_sem2) / 2
            else:
                catalog.avg_annual = catalog.avg_sem2
            catalog.avg_final = catalog.avg_annual

        catalog.save()

    if is_async:
        update_averages_for_students_task.delay(student_ids, catalogs[0].study_class_id, catalogs[0].academic_year)
    else:
        update_averages_for_students_task(student_ids, catalogs[0].study_class_id, catalogs[0].academic_year)


def change_averages_after_examination_grade_operation(catalogs, grade_type, semester):
    if not catalogs:
        return

    student_ids = []
    study_class_id = None
    academic_year = None
    for catalog in catalogs:
        if semester is None:
            # This is either for 2nd examination grades, or for difference grades per year
            grades = catalog.examination_grades.filter(grade_type=grade_type)
            if len(grades) != 2:
                catalog.avg_final = catalog.avg_annual
                if grade_type == ExaminationGrade.GradeTypes.SECOND_EXAMINATION:
                    catalog.avg_after_2nd_examination = None
            else:
                catalog.avg_final = compute_examinations_average(grades[0], grades[1])
                if grade_type == ExaminationGrade.GradeTypes.SECOND_EXAMINATION:
                    catalog.avg_after_2nd_examination = catalog.avg_final
                else:
                    catalog.avg_annual = catalog.avg_final
        else:
            # This is for difference grades per one semester
            grades = catalog.examination_grades.filter(grade_type=grade_type, semester=semester)
            if len(grades) != 2:
                if semester == 1:
                    catalog.avg_sem1 = None
                else:
                    catalog.avg_sem2 = None
            else:
                average = normal_round(compute_examinations_average(grades[0], grades[1]))
                if semester == 1:
                    catalog.avg_sem1 = average
                else:
                    catalog.avg_sem2 = average
                    if catalog.avg_sem1:
                        catalog.avg_annual = (catalog.avg_sem1 + catalog.avg_sem2) / 2
                    else:
                        catalog.avg_annual = catalog.avg_sem2
                    catalog.avg_final = catalog.avg_annual
        student_ids.append(catalog.student_id)
        study_class_id = catalog.study_class_id
        academic_year = catalog.academic_year
        catalog.save()

    update_averages_for_students_task.delay(student_ids, study_class_id, academic_year)


def compute_examinations_average(grade_teacher1, grade_teacher2):
    return (grades_mean([grade_teacher1.grade1, grade_teacher1.grade2]) +
            grades_mean([grade_teacher2.grade1, grade_teacher2.grade2])) / 2


def set_avg_null(catalog, semester):
    if semester == 1:
        catalog.avg_sem1 = None
    else:
        catalog.avg_sem2 = None
        catalog.avg_annual = None
        catalog.avg_final = None

    catalog.save()


def get_avg_limit_for_subject(study_class, is_coordination_subject, subject_id, school_academic_profile=None):
    academic_profile = school_academic_profile or study_class.school_unit.academic_profile

    if is_coordination_subject:
        return get_behavior_grade_limit(academic_profile)
    else:
        if academic_profile and academic_profile.name in PROFILES_WITH_CORE_SUBJECTS:
            core_subject = study_class.academic_program.core_subject
            if core_subject and core_subject.id == subject_id:
                return 6
        return 5


def get_behavior_grade_limit(academic_profile):
    return 8 if academic_profile and academic_profile.name in BEHAVIOR_GRADE_EXCEPTIONS_PROFILES else 6
