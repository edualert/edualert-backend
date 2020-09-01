from django.contrib.auth.models import User
from django.db.models.functions import Lower
from django.utils import timezone
from django.utils.translation import gettext as _
from rest_framework import serializers

from edualert.common.validators import PasswordValidator, PhoneNumberValidator, PersonalIdNumberValidator
from edualert.profiles.models import UserProfile
from edualert.profiles.serializers import BaseUserProfileDetailSerializer, BIRTH_DATE_IN_THE_PAST_ERROR, UserProfileBaseSerializer, USERNAME_UNIQUE_ERROR


class MyAccountSerializer(serializers.ModelSerializer):
    current_password = serializers.CharField(required=False, allow_null=True, allow_blank=True, write_only=True)
    new_password = serializers.CharField(validators=[PasswordValidator, ], required=False,
                                         allow_null=True, allow_blank=True, write_only=True)
    phone_number = serializers.CharField(validators=[PhoneNumberValidator, ], required=False, allow_null=True)
    use_phone_as_username = serializers.BooleanField(required=True)
    email_notifications_enabled = serializers.BooleanField(required=True)
    sms_notifications_enabled = serializers.BooleanField(required=True)
    push_notifications_enabled = serializers.BooleanField(required=True)

    def validate(self, attrs):
        current_password = attrs.get('current_password')
        new_password = attrs.get('new_password')
        if current_password and not new_password:
            raise serializers.ValidationError({'new_password': _('This field is required.')})
        if new_password and not current_password:
            raise serializers.ValidationError({'current_password': _('This field is required.')})

        if current_password and not self.context['request'].user.check_password(current_password):
            raise serializers.ValidationError({'current_password': _("Does not match the user's current password.")})

        BaseUserProfileDetailSerializer.validate_username_required_fields(attrs)

        # Validate username uniqueness
        username = BaseUserProfileDetailSerializer.get_username_from_data(attrs)
        if self.instance.user_role not in [UserProfile.UserRoles.ADMINISTRATOR, UserProfile.UserRoles.PRINCIPAL]:
            username = '{}_{}'.format(self.instance.school_unit_id, username)
        if UserProfile.objects.filter(username=username).exclude(id=self.instance.id).exists() or \
                User.objects.filter(username=username).exclude(id=self.instance.user.id).exists():
            raise serializers.ValidationError({'username': USERNAME_UNIQUE_ERROR})

        birth_date = attrs.get('birth_date')
        if birth_date and birth_date >= timezone.now().date():
            raise serializers.ValidationError({'birth_date': BIRTH_DATE_IN_THE_PAST_ERROR})

        return attrs

    def update(self, instance, validated_data):
        update_user = False

        username = BaseUserProfileDetailSerializer.get_username_from_data(validated_data)
        if instance.user_role not in [UserProfile.UserRoles.ADMINISTRATOR, UserProfile.UserRoles.PRINCIPAL]:
            username = '{}_{}'.format(instance.school_unit_id, username)
        if instance.username != username:
            instance.username = username
            instance.user.username = username
            update_user = True

        password = validated_data.pop('new_password', None)
        if password:
            instance.user.set_password(password)
            update_user = True

        if update_user:
            instance.user.save()

        return super().update(instance, validated_data)

    class Meta:
        model = UserProfile
        fields = (
            'id', 'full_name', 'user_role', 'email', 'phone_number', 'use_phone_as_username',
            'email_notifications_enabled', 'sms_notifications_enabled', 'push_notifications_enabled',
            'current_password', 'new_password', 'school_unit'
        )
        read_only_fields = ('school_unit',)


class MyAccountParentSerializer(MyAccountSerializer):
    children = serializers.SerializerMethodField()

    class Meta(MyAccountSerializer.Meta):
        fields = MyAccountSerializer.Meta.fields + ('address', 'children')

    @staticmethod
    def get_children(obj):
        return UserProfileBaseSerializer(obj.children.order_by(Lower('full_name')), many=True).data


class MyAccountStudentSerializer(MyAccountSerializer):
    personal_id_number = serializers.CharField(validators=[PersonalIdNumberValidator, ], required=False, allow_null=True)
    class_grade = serializers.CharField(source="student_in_class.class_grade", read_only=True, allow_null=True)
    class_letter = serializers.CharField(source="student_in_class.class_letter", read_only=True, allow_null=True)

    class Meta(MyAccountSerializer.Meta):
        extra_fields = ('address', 'class_grade', 'class_letter', 'personal_id_number', 'birth_date')
        fields = MyAccountSerializer.Meta.fields + extra_fields
