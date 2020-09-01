from django.conf import settings
from django.db.models.functions import Lower
from django.utils.translation import gettext as _
from rest_framework import serializers

from edualert.common.fields import PrimaryKeyRelatedField
from edualert.common.utils import convert_datetime_to_timezone
from edualert.notifications.constants import TARGET_USERS_ROLE_MAP
from edualert.notifications.models import Notification, TargetUserThrough
from edualert.profiles.models import UserProfile
from edualert.profiles.serializers import UserProfileWithStudyClass
from edualert.study_classes.serializers import StudyClassNameSerializer


class NotificationSerializer(serializers.ModelSerializer):
    created = serializers.SerializerMethodField()
    from_user_subjects = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ('title', 'created', 'from_user', 'from_user_full_name', 'from_user_role', 'from_user_subjects')

    @staticmethod
    def get_from_user_subjects(obj):
        return obj.from_user_subjects.split('__') if obj.from_user_subjects else None

    @staticmethod
    def get_created(obj):
        return convert_datetime_to_timezone(obj.created).strftime(settings.DATETIME_FORMAT)


class SentNotificationListSerializer(serializers.ModelSerializer):
    created = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    target_user_through = serializers.SerializerMethodField()
    target_study_class = StudyClassNameSerializer()

    class Meta:
        model = Notification
        fields = ('id', 'title', 'created', 'send_sms', 'status', 'receiver_type',
                  'target_users_role', 'target_study_class', 'target_user_through')

    @staticmethod
    def get_created(obj):
        return convert_datetime_to_timezone(obj.created).strftime(settings.DATETIME_FORMAT)

    @staticmethod
    def get_status(obj):
        return {
            'sent_to_count': obj.targets_count,
            'read_by_count': obj.read_by_count
        }

    @staticmethod
    def get_target_user_through(obj):
        if obj.receiver_type in [Notification.ReceiverTypes.CLASS_STUDENTS,
                                 Notification.ReceiverTypes.CLASS_PARENTS]:
            return None

        target_user_through = obj.target_users_through.first()
        if target_user_through is None:
            return None

        data = {
            'user_profile': target_user_through.user_profile_id,
            'user_profile_full_name': target_user_through.user_profile_full_name
        }

        if obj.receiver_type == Notification.ReceiverTypes.ONE_PARENT:
            children = target_user_through.children.select_related('student_in_class')
            data['children'] = UserProfileWithStudyClass(children, many=True).data

        return data


class SentNotificationDetailSerializer(SentNotificationListSerializer):
    class Meta(SentNotificationListSerializer.Meta):
        fields = ('id', 'title', 'created', 'send_sms', 'status', 'receiver_type',
                  'target_users_role', 'target_study_class', 'target_user_through', 'body')


class SentNotificationCreateSerializer(serializers.ModelSerializer):
    target_user = PrimaryKeyRelatedField(queryset=UserProfile.objects.filter(
        is_active=True,
        user_role__in=[UserProfile.UserRoles.PARENT, UserProfile.UserRoles.STUDENT]
    ), required=False)
    send_sms = serializers.BooleanField(required=True)

    class Meta:
        model = Notification
        fields = ('title', 'send_sms', 'receiver_type', 'target_study_class', 'target_user', 'body')

    def validate(self, attrs):
        receiver_type = attrs['receiver_type']
        target_study_class = attrs.get('target_study_class')
        target_user = attrs.get('target_user')

        if receiver_type in [Notification.ReceiverTypes.CLASS_STUDENTS, Notification.ReceiverTypes.CLASS_PARENTS]:
            if target_study_class is None:
                raise serializers.ValidationError({'target_study_class': _('This field is required.')})
            if target_user is not None:
                raise serializers.ValidationError({'target_user': _('This field is incompatible with the receiver type.')})
        else:
            if target_study_class is not None:
                raise serializers.ValidationError({'target_study_class': _('This field is incompatible with the receiver type.')})
            if target_user is None:
                raise serializers.ValidationError({'target_user': _('This field is required.')})
            if receiver_type == Notification.ReceiverTypes.ONE_STUDENT and target_user.user_role != UserProfile.UserRoles.STUDENT:
                raise serializers.ValidationError({'target_user': _('This user must be a student.')})
            if receiver_type == Notification.ReceiverTypes.ONE_PARENT and target_user.user_role != UserProfile.UserRoles.PARENT:
                raise serializers.ValidationError({'target_user': _('This user must be a parent.')})

        body_max_length = 500
        if attrs['send_sms']:
            body_max_length = 160

        if len(attrs['body']) > body_max_length:
            raise serializers.ValidationError({'body': _('Maximum characters numbers was exceeded.')})

        return attrs

    def create(self, validated_data):
        from_user = self.context['request'].user.user_profile
        target_user = validated_data.pop('target_user', None)
        receiver_type = validated_data['receiver_type']

        target_study_class = validated_data.pop('target_study_class', None)
        if receiver_type == Notification.ReceiverTypes.ONE_STUDENT:
            target_study_class = target_user.student_in_class

        target_students = []
        target_parents = []
        children = []
        if receiver_type == Notification.ReceiverTypes.CLASS_STUDENTS:
            target_students = target_study_class.students.all()
            targets_count = target_students.count()
        elif receiver_type == Notification.ReceiverTypes.CLASS_PARENTS:
            target_parents = UserProfile.objects.filter(user_role=UserProfile.UserRoles.PARENT, is_active=True,
                                                        school_unit=from_user.school_unit, child__student_in_class=target_study_class).distinct()
            targets_count = target_parents.count()
        else:
            targets_count = 1
            if receiver_type == Notification.ReceiverTypes.ONE_PARENT:
                if from_user.user_role == UserProfile.UserRoles.PRINCIPAL:
                    children = target_user.children.all()
                else:
                    children = target_user.children.filter(student_in_class__teachers=from_user).distinct()

        from_user_subjects = None
        if from_user.user_role == UserProfile.UserRoles.TEACHER:
            if target_study_class:
                from_user_subjects = '__'.join(from_user.teacher_class_through.filter(study_class=target_study_class)
                                               .values_list('subject_name', flat=True).order_by(Lower('subject_name')))
            else:
                children_study_classes = children.values_list('student_in_class', flat=True)
                from_user_subjects = '__'.join(from_user.teacher_class_through.filter(study_class__in=children_study_classes).distinct()
                                               .values_list('subject_name', flat=True).order_by(Lower('subject_name')))

        instance = Notification.objects.create(from_user=from_user, from_user_full_name=from_user.full_name, from_user_role=from_user.user_role,
                                               from_user_subjects=from_user_subjects, target_users_role=TARGET_USERS_ROLE_MAP[receiver_type],
                                               target_study_class=target_study_class, targets_count=targets_count, **validated_data)

        if receiver_type == Notification.ReceiverTypes.ONE_STUDENT:
            TargetUserThrough.objects.create_and_send(notification=instance, user_profile=target_user, user_profile_full_name=target_user.full_name,
                                                      sent_at_email=target_user.email, sent_at_phone_number=target_user.phone_number)
        elif receiver_type == Notification.ReceiverTypes.ONE_PARENT:
            target_user_through = TargetUserThrough.objects.create_and_send(notification=instance, user_profile=target_user,
                                                                            user_profile_full_name=target_user.full_name,
                                                                            sent_at_email=target_user.email, sent_at_phone_number=target_user.phone_number)
            target_user_through.children.add(*children)
        elif receiver_type == Notification.ReceiverTypes.CLASS_STUDENTS:
            target_users_through = []
            for student in target_students:
                target_users_through.append(
                    TargetUserThrough(notification=instance, user_profile=student, user_profile_full_name=student.full_name,
                                      sent_at_email=student.email, sent_at_phone_number=student.phone_number)
                )
            TargetUserThrough.objects.bulk_create_and_send(target_users_through)
        else:
            target_users_through = []
            for parent in target_parents:
                target_users_through.append(
                    TargetUserThrough(notification=instance, user_profile=parent, user_profile_full_name=parent.full_name,
                                      sent_at_email=parent.email, sent_at_phone_number=parent.phone_number)
                )
            TargetUserThrough.objects.bulk_create_and_send(target_users_through)

        return instance

    def to_representation(self, instance):
        instance.read_by_count = 0
        return SentNotificationDetailSerializer(instance).data


class ReceivedNotificationListSerializer(serializers.ModelSerializer):
    notification = NotificationSerializer()

    class Meta:
        model = TargetUserThrough
        fields = ('id', 'is_read', 'notification')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        notification_representation = representation.pop('notification')

        for key, value in notification_representation.items():
            representation[key] = value

        return representation


class ReceivedNotificationDetailSerializer(ReceivedNotificationListSerializer):
    body = serializers.CharField(source='notification.body')

    class Meta:
        model = TargetUserThrough
        fields = ('id', 'is_read', 'body', 'notification')
