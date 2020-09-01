import factory
from factory.django import DjangoModelFactory

from edualert.profiles.models import UserProfile, Label


class UserFactory(DjangoModelFactory):
    """
    Factory which returns a standard Django auth.User model instance.
    Will perform:
        get_or_create by username for a User instance.
    """

    class Meta:
        model = 'auth.User'

    username = factory.Faker('user_name')
    email = factory.Faker('email')

    # Set user's password after generation
    password = factory.PostGenerationMethodCall('set_password', 'passwd')


class UserProfileFactory(DjangoModelFactory):
    class Meta:
        model = UserProfile

    full_name = factory.Faker('name')
    email = factory.Sequence(lambda n:  f"{n}" + factory.Faker("email").generate())
    username = factory.SelfAttribute('email')
    birth_date = factory.Faker('date')
    phone_number = '+40799000111'
    personal_id_number = factory.Faker('ssn')
    address = factory.Faker('address')

    user = factory.SubFactory(
        UserFactory,
        username=factory.SelfAttribute('..username'),
        email=factory.SelfAttribute('..email'),
    )


class LabelFactory(DjangoModelFactory):
    class Meta:
        model = Label

    text = 'label text'
