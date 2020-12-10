import secrets
import string
from methodtools import lru_cache

from django.contrib.auth.models import User
from django.db.models.functions import Lower
from django.utils import timezone
from django.utils.translation import gettext as _, gettext_lazy
from oauth2_provider.models import AccessToken, RefreshToken
from rest_framework import serializers

from edualert.academic_calendars.utils import get_current_academic_calendar
from edualert.common.fields import PrimaryKeyRelatedField
from edualert.catalogs.models import SubjectGrade, SubjectAbsence, ExaminationGrade, StudentCatalogPerSubject
from edualert.common.validators import PhoneNumberValidator, PersonalIdNumberValidator, PasswordValidator
from edualert.profiles.models import UserProfile, Label
from edualert.study_classes.models import TeacherClassThrough
from edualert.study_classes.serializers import StudyClassNameSerializer, TeacherClassThroughAssignedStudyClassSerializer, \
    TeacherClassThroughPartiallyUpdateSerializer
from edualert.subjects.models import Subject
from edualert.subjects.serializers import SubjectSerializer

BIRTH_DATE_IN_THE_PAST_ERROR = gettext_lazy('Birth date must be in the past.')
USERNAME_UNIQUE_ERROR = gettext_lazy('This username is already associated with another account.')
DISALLOWED_USER_ROLE_ERROR = gettext_lazy("You don't have permission to create a user with this role.")


class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = ('id', 'text')


class UserProfileBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('id', 'full_name')


class UserProfileWithUsernameSerializer(UserProfileBaseSerializer):
    class Meta(UserProfileBaseSerializer.Meta):
        fields = ('id', 'full_name', 'username')


class UserProfileWithTaughtSubjectsSerializer(UserProfileBaseSerializer):
    class Meta(UserProfileBaseSerializer.Meta):
        fields = ('id', 'full_name', 'taught_subjects')


class UserProfileWithStudyClass(UserProfileBaseSerializer):
    study_class = StudyClassNameSerializer(source="student_in_class")

    class Meta(UserProfileBaseSerializer.Meta):
        fields = ('id', 'full_name', 'study_class')


class ParentBaseSerializer(UserProfileBaseSerializer):
    class Meta(UserProfileBaseSerializer.Meta):
        fields = ('id', 'full_name', 'phone_number', 'email', 'address')


class StudentBaseSerializer(UserProfileBaseSerializer):
    labels = LabelSerializer(many=True)

    class Meta(UserProfileBaseSerializer.Meta):
        fields = ('id', 'full_name', 'labels', 'risk_description')


class UserProfileListSerializer(UserProfileBaseSerializer):
    labels = serializers.SerializerMethodField()
    school_unit = serializers.SerializerMethodField()
    assigned_study_classes = serializers.SerializerMethodField()

    class Meta(UserProfileBaseSerializer.Meta):
        fields = ('id', 'full_name', 'user_role', 'is_active', 'last_online', 'labels',
                  'school_unit', 'assigned_study_classes', 'risk_description')

    @staticmethod
    def get_labels(obj):
        return obj.labels.values_list('text', flat=True)

    @lru_cache(maxsize=None)
    def get_current_academic_calendar(self):
        return get_current_academic_calendar()

    @staticmethod
    def get_school_unit(obj):
        if obj.user_role != UserProfile.UserRoles.PRINCIPAL:
            return None

        from edualert.schools.serializers import RegisteredSchoolUnitBaseSerializer
        return RegisteredSchoolUnitBaseSerializer(obj.school_unit).data \
            if obj.school_unit is not None else None

    def get_assigned_study_classes(self, obj):
        if obj.user_role != UserProfile.UserRoles.TEACHER:
            return []

        current_academic_calendar = self.get_current_academic_calendar()
        if current_academic_calendar is None:
            return []

        return TeacherClassThroughAssignedStudyClassSerializer(
            obj.teacher_class_through.filter(academic_year=current_academic_calendar.academic_year)
                .order_by('study_class__class_grade_arabic', 'class_letter', Lower('subject_name')),
            many=True
        ).data


class BaseUserProfileDetailSerializer(UserProfileBaseSerializer):
    """
    Handles the validation of fields that are common across user roles and the creation and updating of objects.
    Calls other child serializers to handle role-specific validations.
    """
    password = serializers.CharField(validators=[PasswordValidator, ], write_only=True, required=False, allow_null=False)
    phone_number = serializers.CharField(validators=[PhoneNumberValidator, ], required=False, allow_null=True)
    use_phone_as_username = serializers.BooleanField(required=True)

    class Meta(UserProfileListSerializer.Meta):
        fields = ('id', 'full_name', 'email', 'phone_number', 'use_phone_as_username',
                  'password', 'user_role', 'is_active', 'last_online')
        read_only_fields = ('id', 'is_active', 'last_online')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.representation_serializer = None

    def validate(self, attrs):
        user_role = attrs['user_role']
        request_user = self.context['request'].user.user_profile

        if self.instance and self.instance.user_role != user_role:
            # Ran on update
            if not self.can_change_user_role():
                raise serializers.ValidationError({'user_role': _('Cannot change user role.')})

            allowed_role_transitions = {
                UserProfile.UserRoles.ADMINISTRATOR: [UserProfile.UserRoles.PRINCIPAL, ],
                UserProfile.UserRoles.PRINCIPAL: [UserProfile.UserRoles.ADMINISTRATOR, ],
                UserProfile.UserRoles.TEACHER: [UserProfile.UserRoles.PARENT, UserProfile.UserRoles.STUDENT],
                UserProfile.UserRoles.PARENT: [UserProfile.UserRoles.TEACHER, UserProfile.UserRoles.STUDENT],
                UserProfile.UserRoles.STUDENT: [UserProfile.UserRoles.TEACHER, UserProfile.UserRoles.PARENT],
            }
            if user_role not in allowed_role_transitions.get(self.instance.user_role, []):
                raise serializers.ValidationError({'user_role': _('Invalid role transition.')})

        if not self.is_allowed_to_edit(request_user.user_role, user_role):
            # Correct user role is enforced in the view on update, no need to check for that
            raise serializers.ValidationError({'user_role': DISALLOWED_USER_ROLE_ERROR})

        self.validate_username_required_fields(attrs)

        username = self.get_username_from_data(attrs)
        if request_user.user_role == UserProfile.UserRoles.PRINCIPAL:
            username = '{}_{}'.format(request_user.school_unit_id, username)

        exclude_profile_id = {'id': self.instance.id} if self.instance else {}
        exclude_user_id = {'id': self.instance.user.id} if self.instance else {}
        if UserProfile.objects.filter(username=username).exclude(**exclude_profile_id).exists() or \
                User.objects.filter(username=username).exclude(**exclude_user_id).exists():
            raise serializers.ValidationError({'username': USERNAME_UNIQUE_ERROR})

        # Delegate validation to other serializers, based on user_role
        serializer_class = self.get_representation_serializer_class(user_role)
        if serializer_class:
            serializer = serializer_class(instance=self.instance, data=self.initial_data, context=self.context)
            serializer.is_valid(raise_exception=True)

            # Keep this on the instance to use for representation
            self.representation_serializer = serializer
            return serializer.validated_data

        return attrs

    def create(self, validated_data):
        validated_data.pop('new_teachers', [])
        password = validated_data.pop('password', None) or self.generate_password()
        username = self.get_username_from_data(validated_data)

        request_user = self.context['request'].user.user_profile
        if request_user.user_role == UserProfile.UserRoles.PRINCIPAL:
            school_unit = request_user.school_unit
            validated_data['school_unit'] = school_unit
            username = '{}_{}'.format(school_unit.id, username)

        # Also create a user for the profile
        user = User.objects.create_user(username=username, password=password)
        validated_data['user'] = user
        validated_data['username'] = username

        return super().create(validated_data)

    def update(self, instance, validated_data):
        should_update_user = False
        new_teachers = validated_data.pop('new_teachers', [])

        password = validated_data.pop('password', None)
        if password:
            instance.user.set_password(password)
            should_update_user = True

        username = self.get_username_from_data(validated_data)
        request_user = self.context['request'].user.user_profile
        if request_user.user_role == UserProfile.UserRoles.PRINCIPAL:
            username = '{}_{}'.format(request_user.school_unit_id, username)
        if username != instance.username:
            validated_data['username'] = username
            instance.user.username = username
            should_update_user = True

        if should_update_user:
            instance.user.save()

        instance = super().update(instance, validated_data)

        if new_teachers:
            instances_to_update = []

            for teacher_class_through in new_teachers:
                teacher_class_through_instance = teacher_class_through['instance']
                teacher = teacher_class_through['teacher']
                teacher_class_through_instance.teacher = teacher
                teacher_class_through_instance.is_class_master = teacher.id == teacher_class_through_instance.study_class.class_master_id
                instances_to_update.append(teacher_class_through_instance)

                StudentCatalogPerSubject.objects.filter(study_class_id=teacher_class_through_instance.study_class_id,
                                                        subject_id=teacher_class_through_instance.subject_id) \
                    .update(teacher=teacher)
            TeacherClassThrough.objects.bulk_update(instances_to_update, ['teacher', 'is_class_master'])

        return instance

    def to_representation(self, instance):
        representation = self.representation_serializer.to_representation(instance) \
            if self.representation_serializer else super().to_representation(instance)
        return representation

    def can_change_user_role(self):
        return not (self.instance.last_online or
                    (self.instance.user_role == UserProfile.UserRoles.TEACHER and
                     self.instance.teacher_class_through.exists()) or
                    (self.instance.user_role == UserProfile.UserRoles.STUDENT and
                     (self.instance.student_in_class is not None or
                      SubjectGrade.objects.filter(student=self.instance).exists() or
                      SubjectAbsence.objects.filter(student=self.instance).exists() or
                      ExaminationGrade.objects.filter(student=self.instance).exists())))

    @staticmethod
    def is_allowed_to_edit(request_user_role, target_user_role):
        if (request_user_role == UserProfile.UserRoles.ADMINISTRATOR and target_user_role not in [
            UserProfile.UserRoles.ADMINISTRATOR, UserProfile.UserRoles.PRINCIPAL
        ]) or (request_user_role == UserProfile.UserRoles.PRINCIPAL and target_user_role not in [
            UserProfile.UserRoles.TEACHER, UserProfile.UserRoles.PARENT, UserProfile.UserRoles.STUDENT
        ]):
            return False
        return True

    @staticmethod
    def get_username_from_data(data):
        return data['phone_number'] if data.get('use_phone_as_username') else data.get('email')

    @staticmethod
    def get_representation_serializer_class(user_role):
        # Returns a serializer class to use for validation and for representation
        if user_role == UserProfile.UserRoles.PRINCIPAL:
            return SchoolPrincipalSerializer
        if user_role == UserProfile.UserRoles.TEACHER:
            return SchoolTeacherSerializer
        if user_role == UserProfile.UserRoles.PARENT:
            return ParentSerializer
        if user_role == UserProfile.UserRoles.STUDENT:
            return StudentSerializer
        return None

    @staticmethod
    def validate_username_required_fields(data):
        if data['use_phone_as_username'] and not data.get('phone_number'):
            raise serializers.ValidationError({'phone_number': _('This field is required.')})
        if not data['use_phone_as_username'] and not data.get('email'):
            raise serializers.ValidationError({'email': _('This field is required.')})

    @staticmethod
    def validate_labels_set(labels, user_role):
        if not labels:
            return

        if any([label for label in labels if label.user_role != user_role]):
            raise serializers.ValidationError({'labels': _("Labels do not correspond to the created user role.")})

    @staticmethod
    def generate_password():
        # Returns a ten-character alphanumeric password with at least one
        # lowercase character, at least one uppercase character, and at least three digits
        alphabet = string.ascii_letters + string.digits
        while True:
            password = ''.join(secrets.choice(alphabet) for i in range(10))
            if (any(c.islower() for c in password)
                    and any(c.isupper() for c in password)
                    and sum(c.isdigit() for c in password) >= 3):
                break
        return password


class SchoolPrincipalSerializer(BaseUserProfileDetailSerializer):
    labels = PrimaryKeyRelatedField(queryset=Label.objects.all(), many=True)
    school_unit = serializers.SerializerMethodField()

    class Meta(UserProfileBaseSerializer.Meta):
        extra_fields = ('labels', 'school_unit')
        fields = BaseUserProfileDetailSerializer.Meta.fields + extra_fields

    def validate(self, attrs):
        labels = attrs.get('labels')
        user_role = attrs['user_role']
        self.validate_labels_set(labels, user_role)
        return attrs

    @staticmethod
    def get_school_unit(obj):
        if obj.school_unit is None:
            return
        from edualert.schools.serializers import RegisteredSchoolUnitBaseSerializer
        return RegisteredSchoolUnitBaseSerializer(obj.school_unit).data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['labels'] = LabelSerializer(instance=instance.labels, many=True).data
        return representation


class SchoolTeacherSerializer(BaseUserProfileDetailSerializer):
    labels = PrimaryKeyRelatedField(queryset=Label.objects.all(), many=True)
    taught_subjects = PrimaryKeyRelatedField(queryset=Subject.objects.all(), many=True)
    assigned_study_classes = serializers.SerializerMethodField()
    new_teachers = TeacherClassThroughPartiallyUpdateSerializer(many=True, required=False, write_only=True)

    class Meta(UserProfileBaseSerializer.Meta):
        extra_fields = ('labels', 'taught_subjects', 'assigned_study_classes', 'new_teachers')
        fields = BaseUserProfileDetailSerializer.Meta.fields + extra_fields

    @lru_cache(maxsize=None)
    def get_current_academic_calendar(self):
        return get_current_academic_calendar()

    @lru_cache(maxsize=None)
    def get_assigned_study_classes(self, obj):
        current_academic_calendar = self.get_current_academic_calendar()
        if current_academic_calendar:
            return TeacherClassThroughAssignedStudyClassSerializer(
                obj.teacher_class_through.filter(academic_year=current_academic_calendar.academic_year)
                    .order_by('study_class__class_grade_arabic', 'class_letter', Lower('subject_name')),
                many=True
            ).data
        return []

    def validate(self, attrs):
        labels = attrs.get('labels')
        user_role = attrs['user_role']
        self.validate_labels_set(labels, user_role)
        new_teachers = attrs.get('new_teachers', [])
        new_teachers_compatible = False

        if self.instance:
            existing_subjects = set(self.instance.taught_subjects.values_list('id', flat=True))
            request_subjects = set(subject.id for subject in attrs.get('taught_subjects', []))
            removed_subjects = existing_subjects - request_subjects

            if removed_subjects:
                new_teachers_ids = [teacher_class_through['id'] for teacher_class_through in new_teachers]
                new_teachers_ids_set = set(new_teachers_ids)
                assigned_classes = self.get_assigned_study_classes(self.instance)
                subject_assigned_classes = [assigned_class for assigned_class in assigned_classes if assigned_class['subject_id'] in removed_subjects]

                if subject_assigned_classes:
                    if set(assigned_class['id'] for assigned_class in subject_assigned_classes) != new_teachers_ids_set:
                        raise serializers.ValidationError({'new_teachers': _('There must be provided teachers for all classes for this subject.')})

                    if len(new_teachers_ids) != len(new_teachers_ids_set):
                        raise serializers.ValidationError({'new_teachers': _('No duplicates allowed.')})

                    school_unit = self.context['request'].user.user_profile.school_unit
                    for teacher_class_through in new_teachers:
                        teacher = teacher_class_through['teacher']
                        if teacher.user_role != UserProfile.UserRoles.TEACHER or not teacher.is_active or teacher.school_unit_id != school_unit.id:
                            raise serializers.ValidationError({'new_teachers': _('At least one teacher is invalid.')})

                        teacher_class_through_instance = TeacherClassThrough.objects.get(id=teacher_class_through['id'])
                        subject = teacher_class_through_instance.subject
                        study_class = teacher_class_through_instance.study_class
                        if subject not in teacher.taught_subjects.all() and \
                                (study_class.class_grade_arabic in range(5, 14) or
                                 (study_class.class_grade_arabic in range(0, 5) and teacher.id != study_class.class_master_id)):
                            raise serializers.ValidationError({'new_teachers': _('Teacher {} does not teach {}.').format(teacher.full_name, subject.name)})

                        teacher_class_through['instance'] = teacher_class_through_instance

                    new_teachers_compatible = True
                    self.get_assigned_study_classes.cache_clear()

        if new_teachers and not new_teachers_compatible:
            raise serializers.ValidationError({'new_teachers': _('This field is incompatible with the request data.')})

        return attrs

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['labels'] = LabelSerializer(instance=instance.labels, many=True).data
        representation['taught_subjects'] = SubjectSerializer(instance=instance.taught_subjects, many=True).data
        return representation


class ParentSerializer(BaseUserProfileDetailSerializer):
    labels = PrimaryKeyRelatedField(queryset=Label.objects.all(), many=True)

    class Meta(UserProfileBaseSerializer.Meta):
        extra_fields = ('labels', 'address')
        fields = BaseUserProfileDetailSerializer.Meta.fields + extra_fields

    def validate(self, attrs):
        labels = attrs.get('labels')
        user_role = attrs['user_role']
        self.validate_labels_set(labels, user_role)
        return attrs

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['labels'] = LabelSerializer(instance=instance.labels, many=True).data
        return representation


class StudentSerializer(BaseUserProfileDetailSerializer):
    personal_id_number = serializers.CharField(validators=[PersonalIdNumberValidator, ], required=False, allow_null=True)
    educator_phone_number = serializers.CharField(required=False, validators=[PhoneNumberValidator, ], allow_null=True)
    parents = PrimaryKeyRelatedField(
        queryset=UserProfile.objects.filter(user_role=UserProfile.UserRoles.PARENT, ),
        many=True,
    )
    labels = PrimaryKeyRelatedField(queryset=Label.objects.all(), many=True)
    student_in_class = StudyClassNameSerializer(read_only=True)

    class Meta(UserProfileBaseSerializer.Meta):
        extra_fields = ('address', 'personal_id_number', 'birth_date', 'educator_full_name', 'educator_email',
                        'educator_phone_number', 'labels', 'parents', 'student_in_class', 'risk_description')
        fields = BaseUserProfileDetailSerializer.Meta.fields + extra_fields
        read_only_fields = ('student_in_class', 'risk_description')

    def validate(self, attrs):
        if attrs.get('educator_full_name') and not (attrs.get('educator_email') or attrs.get('educator_phone_number')):
            raise serializers.ValidationError(
                {'educator_full_name': _('Either email or phone number is required for the educator.')}
            )

        # Birth date must be in the past
        birth_date = attrs.get('birth_date')
        if birth_date and birth_date >= timezone.now().date():
            raise serializers.ValidationError({'birth_date': BIRTH_DATE_IN_THE_PAST_ERROR})

        labels = attrs.get('labels')
        user_role = attrs['user_role']
        self.validate_labels_set(labels, user_role)

        # Parents must belong to the request user's school unit
        parents = attrs.get('parents')
        if parents:
            allowed_school = self.context['request'].user.user_profile.school_unit
            for parent in parents:
                if parent.school_unit != allowed_school:
                    raise serializers.ValidationError({'parents': _("Parents must belong to the user's school unit.")})

        return attrs

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['labels'] = LabelSerializer(instance=instance.labels, many=True).data
        representation['parents'] = ParentBaseSerializer(instance=instance.parents, many=True).data
        return representation


class StudentWithRiskAlertsSerializer(StudentSerializer):
    risk_alerts = serializers.ReadOnlyField()

    class Meta(StudentSerializer.Meta):
        fields = StudentSerializer.Meta.fields + ('risk_alerts',)


class DeactivateUserSerializer(serializers.ModelSerializer):
    new_school_principal = PrimaryKeyRelatedField(
        queryset=UserProfile.objects.filter(user_role=UserProfile.UserRoles.PRINCIPAL,
                                            is_active=True, school_unit__isnull=True),
        required=False
    )
    new_teachers = TeacherClassThroughPartiallyUpdateSerializer(many=True, required=False)

    class Meta:
        model = UserProfile
        fields = ('new_school_principal', 'new_teachers')

    @lru_cache(maxsize=None)
    def get_current_academic_calendar(self):
        return get_current_academic_calendar()

    @lru_cache(maxsize=None)
    def get_user_assigned_classes(self):
        current_academic_calendar = self.get_current_academic_calendar()
        return self.instance.teacher_class_through \
            .filter(academic_year=current_academic_calendar.academic_year) if current_academic_calendar else []

    def validate(self, attrs):
        if self.instance.user_role == UserProfile.UserRoles.PRINCIPAL:
            new_school_principal = attrs.get('new_school_principal')

            if self.instance.school_unit and new_school_principal is None:
                raise serializers.ValidationError({'new_school_principal': _('This field is required.')})
        elif self.instance.user_role == UserProfile.UserRoles.TEACHER:
            new_teachers = attrs.get('new_teachers', [])
            assigned_classes = self.get_user_assigned_classes()

            if assigned_classes and not new_teachers:
                raise serializers.ValidationError({'new_teachers': _('This field is required.')})

            new_teachers_ids = [teacher_class_through['id'] for teacher_class_through in new_teachers]
            new_teachers_ids_set = set(new_teachers_ids)

            if len(new_teachers_ids) != len(new_teachers_ids_set):
                raise serializers.ValidationError({'new_teachers': _('No duplicates allowed.')})

            if set(assigned_class.id for assigned_class in assigned_classes) != new_teachers_ids_set:
                raise serializers.ValidationError({'new_teachers': _('There must be provided teachers for all classes and subjects.')})

            school_unit = self.context['request'].user.user_profile.school_unit
            current_academic_calendar = self.get_current_academic_calendar()
            for teacher_class_through in new_teachers:
                teacher = teacher_class_through['teacher']
                if teacher.user_role != UserProfile.UserRoles.TEACHER or not teacher.is_active or teacher.school_unit_id != school_unit.id:
                    raise serializers.ValidationError({'new_teachers': _('At least one teacher is invalid.')})

                teacher_class_through_instance = TeacherClassThrough.objects.get(id=teacher_class_through['id'])
                subject = teacher_class_through_instance.subject
                study_class = teacher_class_through_instance.study_class
                if not teacher_class_through_instance.is_optional_subject and not subject.is_coordination \
                        and subject not in teacher.taught_subjects.all() and \
                        (study_class.class_grade_arabic in range(5, 14) or
                         (study_class.class_grade_arabic in range(0, 5) and teacher.id != study_class.class_master_id)):
                    raise serializers.ValidationError({'new_teachers': _('Teacher {} does not teach {}.').format(teacher.full_name, subject.name)})
                if subject.is_coordination and teacher.mastering_study_classes.filter(academic_year=current_academic_calendar.academic_year).exists():
                    raise serializers.ValidationError({'new_teachers': _('Invalid class master.')})

                teacher_class_through['instance'] = teacher_class_through_instance

        return attrs

    def update(self, instance, validated_data):
        if instance.user_role == UserProfile.UserRoles.PRINCIPAL:
            school_unit = instance.school_unit
            if school_unit:
                new_school_principal = validated_data['new_school_principal']
                school_unit.school_principal = new_school_principal
                school_unit.save()
                new_school_principal.school_unit = school_unit
                new_school_principal.save()
                instance.school_unit = None
        elif instance.user_role == UserProfile.UserRoles.TEACHER:
            assigned_classes = self.get_user_assigned_classes()
            if assigned_classes:
                new_teachers = validated_data['new_teachers']
                new_class_master = None
                class_master_study_class = None
                instances_to_update = []

                for teacher_class_through in new_teachers:
                    teacher_class_through_instance = teacher_class_through['instance']
                    teacher = teacher_class_through['teacher']
                    study_class = teacher_class_through_instance.study_class
                    teacher_class_through_instance.teacher = teacher
                    teacher_class_through_instance.is_class_master = teacher.id == study_class.class_master_id
                    instances_to_update.append(teacher_class_through_instance)

                    if teacher_class_through_instance.is_coordination_subject:
                        new_class_master = teacher
                        class_master_study_class = study_class

                    # Also update catalogs for all students in this class for this subject
                    StudentCatalogPerSubject.objects.filter(study_class_id=teacher_class_through_instance.study_class_id,
                                                            subject_id=teacher_class_through_instance.subject_id) \
                        .update(teacher=teacher)

                TeacherClassThrough.objects.bulk_update(instances_to_update, ['teacher', 'is_class_master'])
                if new_class_master and class_master_study_class:
                    class_master_study_class.class_master = new_class_master
                    class_master_study_class.save()
                    TeacherClassThrough.objects.filter(study_class_id=class_master_study_class.id, teacher=new_class_master) \
                        .update(is_class_master=True)

        instance.is_active = False
        instance.save()
        instance.user.is_active = False
        instance.user.save()

        # Delete all tokens & Refresh tokens for this users
        AccessToken.objects.filter(user__user_profile=instance).delete()
        RefreshToken.objects.filter(user__user_profile=instance).delete()

        return instance

    def to_representation(self, instance):
        if instance.user_role == UserProfile.UserRoles.PRINCIPAL:
            return SchoolPrincipalSerializer(instance).data
        if instance.user_role == UserProfile.UserRoles.TEACHER:
            return SchoolTeacherSerializer(instance).data
        if instance.user_role == UserProfile.UserRoles.PARENT:
            return ParentSerializer(instance).data
        if instance.user_role == UserProfile.UserRoles.STUDENT:
            return StudentSerializer(instance).data

        return BaseUserProfileDetailSerializer(instance).data
