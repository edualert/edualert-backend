import factory
from factory.django import DjangoModelFactory

from edualert.notifications.models import Notification, TargetUserThrough
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.study_classes.factories import StudyClassFactory


class NotificationFactory(DjangoModelFactory):
    class Meta:
        model = Notification

    title = 'title'
    body = 'message body'
    from_user = factory.SubFactory(
        UserProfileFactory,
        user_role=UserProfile.UserRoles.TEACHER
    )
    from_user_full_name = factory.SelfAttribute('from_user.full_name')
    from_user_role = factory.SelfAttribute('from_user.user_role')

    receiver_type = Notification.ReceiverTypes.ONE_STUDENT
    target_users_role = UserProfile.UserRoles.STUDENT

    target_study_class = factory.SubFactory(StudyClassFactory)


class TargetUserThroughFactory(DjangoModelFactory):
    class Meta:
        model = TargetUserThrough

    user_profile_full_name = factory.SelfAttribute('user_profile.full_name')
