import factory
from factory.django import DjangoModelFactory

from edualert.academic_programs.factories import AcademicProgramFactory
from edualert.study_classes.models import TeacherClassThrough
from edualert.subjects.factories import SubjectFactory
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.study_classes.models import StudyClass


class StudyClassFactory(DjangoModelFactory):
    class Meta:
        model = StudyClass

    school_unit = factory.SubFactory(
        RegisteredSchoolUnitFactory
    )

    academic_program = factory.SubFactory(
        AcademicProgramFactory
    )

    class_master = factory.SubFactory(
        UserProfileFactory,
        user_role=UserProfile.UserRoles.TEACHER,
        school_unit=factory.SelfAttribute('..school_unit')
    )

    academic_year = 2020
    class_grade = 'VI'
    class_grade_arabic = 6
    class_letter = 'A'
    academic_program_name = factory.SelfAttribute('academic_program.name')


class TeacherClassThroughFactory(DjangoModelFactory):
    class Meta:
        model = TeacherClassThrough

    study_class = factory.SubFactory(StudyClassFactory)
    teacher = factory.SelfAttribute('study_class.class_master')
    subject = factory.SubFactory(SubjectFactory)

    is_class_master = False
    academic_year = factory.SelfAttribute('study_class.academic_year')
    class_grade = factory.SelfAttribute('study_class.class_grade')
    class_letter = factory.SelfAttribute('study_class.class_letter')
    academic_program_name = factory.SelfAttribute('study_class.academic_program_name')
    subject_name = factory.SelfAttribute("subject.name")
    is_coordination_subject = factory.SelfAttribute("subject.is_coordination")

