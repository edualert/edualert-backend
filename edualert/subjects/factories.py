import factory
from factory.django import DjangoModelFactory

from edualert.subjects.models import Subject, ProgramSubjectThrough


class SubjectFactory(DjangoModelFactory):
    class Meta:
        model = Subject

    name = factory.Faker('bs')


class ProgramSubjectThroughFactory(DjangoModelFactory):
    class Meta:
        model = ProgramSubjectThrough

    subject_name = factory.SelfAttribute('subject.name')
    class_grade = 'IX'
    class_grade_arabic = 9
    weekly_hours_count = 5
