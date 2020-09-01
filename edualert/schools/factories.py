import factory
from factory.django import DjangoModelFactory

from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.models import SchoolUnit, SchoolUnitCategory, SchoolUnitProfile, RegisteredSchoolUnit


class SchoolUnitFactory(DjangoModelFactory):
    class Meta:
        model = SchoolUnit

    name = factory.Faker('name')
    district = factory.Faker('state')
    city = factory.Faker('city')


class SchoolUnitCategoryFactory(DjangoModelFactory):
    class Meta:
        model = SchoolUnitCategory

    name = factory.Faker('name')
    category_level = SchoolUnitCategory.CategoryLevels.HIGHSCHOOL


class SchoolUnitProfileFactory(DjangoModelFactory):
    class Meta:
        model = SchoolUnitProfile

    name = factory.Faker('name')
    category = factory.SubFactory(
        SchoolUnitCategoryFactory
    )


class RegisteredSchoolUnitFactory(DjangoModelFactory):
    class Meta:
        model = RegisteredSchoolUnit

    name = factory.Faker('name')
    district = factory.Faker('state')
    city = factory.Faker('city')
    address = factory.Faker('address')
    email = factory.Faker('email')
    phone_number = '+40799000111'
    school_principal = factory.SubFactory(
        UserProfileFactory,
        user_role=UserProfile.UserRoles.PRINCIPAL
    )

    @factory.post_generation
    def set_principal_school(self, create, extracted, **kwargs):
        if not create:
            return
        self.school_principal.school_unit = self
        self.school_principal.save()
