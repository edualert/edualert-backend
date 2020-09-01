from oauth2_provider.models import AccessToken, RefreshToken

from django.utils.translation import gettext as _
from rest_framework import serializers

from edualert.academic_calendars.utils import get_current_academic_calendar
from edualert.common.fields import PrimaryKeyRelatedField
from edualert.common.validators import PhoneNumberValidator
from edualert.profiles.models import UserProfile
from edualert.profiles.serializers import UserProfileBaseSerializer
from edualert.schools.models import SchoolUnitCategory, SchoolUnitProfile, RegisteredSchoolUnit, SchoolUnit
from edualert.statistics.models import SchoolUnitStats
from edualert.statistics.tasks import update_school_unit_enrollment_stats_task, create_students_at_risk_counts_for_school_unit_task


class SchoolUnitCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolUnitCategory
        fields = ('id', 'name', 'category_level')


class SchoolUnitProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolUnitProfile
        fields = ('id', 'name',)


class RegisteredSchoolUnitBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegisteredSchoolUnit
        fields = ('id', 'name')


class RegisteredSchoolUnitNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegisteredSchoolUnit
        fields = ('id', 'name', 'city',)


class RegisteredSchoolUnitListSerializer(serializers.ModelSerializer):
    categories = SchoolUnitCategorySerializer(many=True)
    academic_profile = SchoolUnitProfileSerializer()

    class Meta:
        model = RegisteredSchoolUnit
        fields = ('id', 'name', 'categories', 'academic_profile', 'is_active', 'district', 'city',)


class RegisteredSchoolUnitDetailSerializer(serializers.ModelSerializer):
    categories = SchoolUnitCategorySerializer(many=True)
    academic_profile = SchoolUnitProfileSerializer()
    school_principal = UserProfileBaseSerializer()

    class Meta:
        model = RegisteredSchoolUnit
        fields = (
            'id', 'categories', 'academic_profile', 'address', 'phone_number', 'email',
            'district', 'city', 'name', 'is_active', 'school_principal',
        )


class RegisteredSchoolUnitCreateUpdateBaseSerializer(serializers.ModelSerializer):
    categories = PrimaryKeyRelatedField(
        queryset=SchoolUnitCategory.objects.all(),
        many=True
    )
    phone_number = serializers.CharField(validators=[PhoneNumberValidator, ])

    class Meta:
        model = RegisteredSchoolUnit

    def validate(self, attrs):
        validated_data = super().validate(attrs)

        if not self.instance and RegisteredSchoolUnit.objects.filter(name=attrs['name'], district=attrs['district'], city=attrs['city']).exists():
            raise serializers.ValidationError(
                {'general_errors': _('This school is already registered.')}
            )

        categories = validated_data['categories']
        if len(categories) != len(set(category.category_level for category in categories)):
            raise serializers.ValidationError(
                {'categories': _('Cannot have multiple categories for the same school level.')}
            )

        academic_profile = validated_data.get('academic_profile', None)
        if academic_profile and academic_profile.category not in categories:
            raise serializers.ValidationError(
                {'academic_profile': _('The academic profile does not correspond with the school category.')}
            )

        school_principal = validated_data['school_principal']
        if school_principal.user_role != UserProfile.UserRoles.PRINCIPAL or not school_principal.is_active:
            raise serializers.ValidationError(
                {'school_principal': _('Invalid user.')}
            )
        if getattr(school_principal, 'registered_school_unit', None) and school_principal.registered_school_unit != self.instance:
            raise serializers.ValidationError(
                {'school_principal': _('This school principal already has a school assigned.')}
            )

        return validated_data

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        representation['categories'] = SchoolUnitCategorySerializer(instance.categories, many=True).data
        if instance.academic_profile:
            representation['academic_profile'] = SchoolUnitProfileSerializer(instance.academic_profile).data
        representation['school_principal'] = UserProfileBaseSerializer(instance.school_principal).data

        return representation


class RegisteredSchoolUnitCreateSerializer(RegisteredSchoolUnitCreateUpdateBaseSerializer):
    class Meta(RegisteredSchoolUnitCreateUpdateBaseSerializer.Meta):
        fields = (
            'id', 'is_active', 'categories', 'academic_profile', 'address',
            'phone_number', 'email', 'district', 'city', 'name', 'school_principal',
        )
        read_only_fields = ('id', 'is_active',)

    def create(self, validated_data):
        instance = super().create(validated_data)
        instance.school_principal.school_unit = instance
        instance.school_principal.save()

        current_calendar = get_current_academic_calendar()
        if current_calendar:
            SchoolUnitStats.objects.create(school_unit=instance, school_unit_name=instance.name, academic_year=current_calendar.academic_year)

        update_school_unit_enrollment_stats_task.delay()
        create_students_at_risk_counts_for_school_unit_task.delay(instance.id)

        return instance


class RegisteredSchoolUnitUpdateSerializer(RegisteredSchoolUnitCreateUpdateBaseSerializer):
    class Meta(RegisteredSchoolUnitCreateUpdateBaseSerializer.Meta):
        read_only_fields = ('district', 'city', 'name', 'id', 'is_active',)
        fields = read_only_fields + (
            'categories', 'academic_profile', 'school_principal', 'address', 'email', 'phone_number',
        )

    def update(self, instance, validated_data):
        principal_before_update = instance.school_principal
        principal_after_update = validated_data['school_principal']

        instance = super().update(instance, validated_data)

        if principal_before_update != principal_after_update:
            principal_after_update.school_unit = instance
            principal_after_update.save()

            principal_before_update.school_unit = None
            principal_before_update.save()
            # Delete all tokens & Refresh tokens for this users
            AccessToken.objects.filter(user__user_profile=principal_before_update).delete()
            RefreshToken.objects.filter(user__user_profile=principal_before_update).delete()

        return instance


class UnregisteredSchoolUnitListSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolUnit
        fields = ('id', 'name', 'city', 'district',)
