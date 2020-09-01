import factory
from factory.django import DjangoModelFactory

from edualert.academic_programs.models import AcademicProgram, GenericAcademicProgram
from edualert.schools.factories import RegisteredSchoolUnitFactory, SchoolUnitCategoryFactory


class GenericAcademicProgramFactory(DjangoModelFactory):
    class Meta:
        model = GenericAcademicProgram

    name = factory.Faker('bs')
    category = factory.SubFactory(
        SchoolUnitCategoryFactory
    )


class AcademicProgramFactory(DjangoModelFactory):
    class Meta:
        model = AcademicProgram

    school_unit = factory.SubFactory(
        RegisteredSchoolUnitFactory
    )

    generic_academic_program = factory.SubFactory(
        GenericAcademicProgramFactory
    )

    name = factory.SelfAttribute("generic_academic_program.name")
    academic_year = 2020
