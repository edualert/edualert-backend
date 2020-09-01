import factory
from django.utils import timezone
from factory.django import DjangoModelFactory

from edualert.catalogs.models import StudentCatalogPerSubject, StudentCatalogPerYear, SubjectGrade, SubjectAbsence, ExaminationGrade
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.study_classes.factories import StudyClassFactory
from edualert.subjects.factories import SubjectFactory


class StudentCatalogPerSubjectFactory(DjangoModelFactory):
    class Meta:
        model = StudentCatalogPerSubject

    student = factory.SubFactory(
        UserProfileFactory,
        user_role=UserProfile.UserRoles.STUDENT
    )
    teacher = factory.SubFactory(
        UserProfileFactory,
        user_role=UserProfile.UserRoles.TEACHER
    )
    study_class = factory.SubFactory(
        StudyClassFactory
    )
    academic_year = factory.SelfAttribute('study_class.academic_year')
    subject = factory.SubFactory(
        SubjectFactory
    )
    subject_name = factory.SelfAttribute('subject.name')
    is_coordination_subject = factory.SelfAttribute('subject.is_coordination')


class StudentCatalogPerYearFactory(DjangoModelFactory):
    class Meta:
        model = StudentCatalogPerYear

    student = factory.SubFactory(
        UserProfileFactory,
        user_role=UserProfile.UserRoles.STUDENT
    )
    study_class = factory.SubFactory(
        StudyClassFactory
    )
    academic_year = factory.SelfAttribute('study_class.academic_year')


class SubjectGradeFactory(DjangoModelFactory):
    class Meta:
        model = SubjectGrade

    student = factory.SubFactory(
        UserProfileFactory,
        user_role=UserProfile.UserRoles.STUDENT
    )
    catalog_per_subject = factory.SubFactory(
        StudentCatalogPerSubjectFactory,
        student=factory.SelfAttribute('..student')
    )
    subject_name = factory.SelfAttribute('catalog_per_subject.subject_name')
    academic_year = factory.SelfAttribute('catalog_per_subject.academic_year')
    semester = 1
    taken_at = timezone.now().date()
    grade = 10
    grade_type = SubjectGrade.GradeTypes.REGULAR


class SubjectAbsenceFactory(DjangoModelFactory):
    class Meta:
        model = SubjectAbsence

    student = factory.SubFactory(
        UserProfileFactory,
        user_role=UserProfile.UserRoles.STUDENT
    )
    catalog_per_subject = factory.SubFactory(
        StudentCatalogPerSubjectFactory,
        student=factory.SelfAttribute('..student')
    )
    subject_name = factory.SelfAttribute('catalog_per_subject.subject_name')
    academic_year = factory.SelfAttribute('catalog_per_subject.academic_year')
    semester = 1
    taken_at = timezone.now().date()


class ExaminationGradeFactory(DjangoModelFactory):
    class Meta:
        model = ExaminationGrade

    student = factory.SubFactory(
        UserProfileFactory,
        user_role=UserProfile.UserRoles.STUDENT
    )
    catalog_per_subject = factory.SubFactory(
        StudentCatalogPerSubjectFactory,
        student=factory.SelfAttribute('..student')
    )
    subject_name = factory.SelfAttribute('catalog_per_subject.subject_name')
    academic_year = factory.SelfAttribute('catalog_per_subject.academic_year')
    taken_at = timezone.now().date()
    grade1 = 10
    grade2 = 10
    examination_type = ExaminationGrade.ExaminationTypes.WRITTEN
    grade_type = ExaminationGrade.GradeTypes.SECOND_EXAMINATION
