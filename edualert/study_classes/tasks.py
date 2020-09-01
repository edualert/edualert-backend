from celery import shared_task

from edualert.catalogs.models import StudentCatalogPerYear, StudentCatalogPerSubject, SubjectGrade, SubjectAbsence, ExaminationGrade
from edualert.profiles.models import UserProfile
from edualert.study_classes.models import StudyClass
from edualert.study_classes.utils import get_school_cycle_for_class_grade


@shared_task
def import_students_data(student_ids, class_grade_arabic):
    current_cycle_grades = [
        grade for grade in get_school_cycle_for_class_grade(class_grade_arabic)
        if grade < class_grade_arabic
    ]

    if not current_cycle_grades:
        return

    created_catalogs_per_year = []
    created_catalogs_per_subject = []
    created_grades = []
    created_absences = []
    created_examination_grades = []

    for student_id in student_ids:
        student = UserProfile.objects.filter(id=student_id, user_role=UserProfile.UserRoles.STUDENT).first()
        if not student:
            continue

        if not student.labels.filter(is_label_for_transfers_between_schools=True).exists():
            continue

        another_school_profile = UserProfile.objects.filter(full_name=student.full_name, email=student.email,
                                                            phone_number=student.phone_number,
                                                            user_role=UserProfile.UserRoles.STUDENT).first()
        if not another_school_profile:
            continue

        catalogs_per_year = get_catalogs_per_year(another_school_profile, current_cycle_grades)
        catalogs_per_subject = get_catalogs_per_subject(another_school_profile, current_cycle_grades)

        for grade in current_cycle_grades:
            catalog_per_year = catalogs_per_year.get(grade)
            if not catalog_per_year:
                continue

            study_class = StudyClass.objects.filter(school_unit_id=student.school_unit_id,
                                                    academic_year=catalog_per_year.academic_year,
                                                    class_grade_arabic=grade).first()
            if not study_class:
                continue

            # Copy catalog per year
            catalog_per_year_copy = StudentCatalogPerYear(student=student, study_class=study_class, academic_year=catalog_per_year.academic_year)
            for field in ['avg_sem1', 'avg_sem2', 'avg_annual', 'avg_final', 'abs_count_sem1', 'abs_count_sem2', 'abs_count_annual',
                          'unfounded_abs_count_sem1', 'unfounded_abs_count_sem2', 'unfounded_abs_count_annual',
                          'founded_abs_count_sem1', 'founded_abs_count_sem2', 'founded_abs_count_annual',
                          'remarks', 'second_examinations_count', 'behavior_grade_sem1', 'behavior_grade_sem2', 'behavior_grade_annual']:
                setattr(catalog_per_year_copy, field, getattr(catalog_per_year, field, None))
            created_catalogs_per_year.append(catalog_per_year_copy)

            catalogs_per_subject_for_grade = catalogs_per_subject.get(grade)
            if not catalogs_per_subject_for_grade:
                continue

            # Copy the catalogs per subject
            subjects = get_study_class_subjects(study_class)
            for subject in subjects:
                found = False
                for catalog in catalogs_per_subject_for_grade:
                    if catalog.subject_id == subject.subject_id:
                        catalog_per_subject_copy = StudentCatalogPerSubject(student=student, study_class=study_class, teacher=subject.teacher,
                                                                            academic_year=study_class.academic_year, subject=subject.subject,
                                                                            subject_name=subject.subject_name,
                                                                            is_coordination_subject=subject.is_coordination_subject)
                        for field in ['avg_sem1', 'avg_sem2', 'avg_annual', 'avg_after_2nd_examination', 'avg_final',
                                      'abs_count_sem1', 'abs_count_sem2', 'abs_count_annual',
                                      'unfounded_abs_count_sem1', 'unfounded_abs_count_sem2', 'unfounded_abs_count_annual',
                                      'founded_abs_count_sem1', 'founded_abs_count_sem2', 'founded_abs_count_annual',
                                      'remarks', 'wants_level_testing_grade', 'wants_thesis', 'wants_simulation', 'is_exempted', 'is_enrolled']:
                            setattr(catalog_per_subject_copy, field, getattr(catalog, field, None))
                        catalog_per_subject_copy.save()

                        # Copy the grades
                        for subject_grade in catalog.grades.all():
                            created_grades.append(
                                SubjectGrade(catalog_per_subject=catalog_per_subject_copy, student=student, subject_name=subject_grade.subject_name,
                                             academic_year=subject_grade.academic_year, semester=subject_grade.semester, taken_at=subject_grade.taken_at,
                                             grade=subject_grade.grade, grade_type=subject_grade.grade_type)
                            )
                        # Copy the absences
                        for subject_absence in catalog.absences.all():
                            created_absences.append(
                                SubjectAbsence(catalog_per_subject=catalog_per_subject_copy, student=student, subject_name=subject_absence.subject_name,
                                               academic_year=subject_absence.academic_year, semester=subject_absence.semester,
                                               taken_at=subject_absence.taken_at, is_founded=subject_absence.is_founded)
                            )
                        # Copy the examination grades
                        for exam_grade in catalog.examination_grades.all():
                            created_examination_grades.append(
                                ExaminationGrade(catalog_per_subject=catalog_per_subject_copy, student=student, subject_name=exam_grade.subject_name,
                                                 academic_year=exam_grade.academic_year, taken_at=exam_grade.taken_at,
                                                 examination_type=exam_grade.examination_type, grade_type=exam_grade.grade_type,
                                                 grade1=exam_grade.grade1, grade2=exam_grade.grade2, semester=exam_grade.semester)
                            )

                        found = True
                        break
                if not found:
                    created_catalogs_per_subject.append(
                        StudentCatalogPerSubject(student=student, teacher=subject.teacher, study_class=study_class,
                                                 academic_year=study_class.academic_year, subject=subject.subject,
                                                 subject_name=subject.subject_name,
                                                 is_coordination_subject=subject.is_coordination_subject,
                                                 is_enrolled=not subject.is_optional_subject)
                    )

    StudentCatalogPerYear.objects.bulk_create(created_catalogs_per_year)
    StudentCatalogPerSubject.objects.bulk_create(created_catalogs_per_subject)
    SubjectGrade.objects.bulk_create(created_grades)
    SubjectAbsence.objects.bulk_create(created_absences)
    ExaminationGrade.objects.bulk_create(created_examination_grades)


def get_catalogs_per_year(student, class_grades):
    catalogs = student.student_catalogs_per_year.filter(
        study_class__class_grade_arabic__in=class_grades
    ).select_related('study_class')

    catalogs_per_year = {}
    for catalog in catalogs:
        catalogs_per_year[catalog.study_class.class_grade_arabic] = catalog
    return catalogs_per_year


def get_catalogs_per_subject(student, class_grades):
    catalogs = student.student_catalogs_per_subject.filter(
        study_class__class_grade_arabic__in=class_grades
    ).select_related('study_class')

    catalogs_per_subject = {}
    for catalog in catalogs:
        class_grade_arabic = catalog.study_class.class_grade_arabic
        if catalogs_per_subject.get(class_grade_arabic):
            catalogs_per_subject[class_grade_arabic].append(catalog)
        else:
            catalogs_per_subject[class_grade_arabic] = [catalog]

    return catalogs_per_subject


def get_study_class_subjects(study_class):
    return study_class.teacher_class_through.select_related('teacher', 'subject')
