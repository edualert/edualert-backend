from django.db.models.functions import Lower
from django.utils.translation import gettext as _
from django.db.models import Q
from rest_framework import serializers

from edualert.academic_programs.models import GenericAcademicProgram, AcademicProgram
from edualert.common.fields import PrimaryKeyRelatedField
from edualert.schools.constants import PROFILES_WITH_CORE_SUBJECTS
from edualert.study_classes.constants import CLASS_GRADE_MAPPING
from edualert.subjects.models import ProgramSubjectThrough, Subject
from edualert.subjects.serializers import ProgramSubjectThroughSerializer, OptionalProgramSubjectThroughSerializer


class GenericAcademicProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = GenericAcademicProgram
        fields = ('id', 'name')


class GenericAcademicProgramDetailSerializer(serializers.ModelSerializer):
    subjects = serializers.SerializerMethodField()

    class Meta:
        model = GenericAcademicProgram
        fields = ('id', 'subjects', 'optional_subjects_weekly_hours')

    @staticmethod
    def get_subjects(obj):
        mandatory_subjects_through = obj.program_subjects_through.order_by('class_grade_arabic', Lower('subject_name'))
        subjects = {}

        for subject_through in mandatory_subjects_through:
            subject_through_data = ProgramSubjectThroughSerializer(subject_through).data
            if subject_through.class_grade in subjects:
                subjects[subject_through.class_grade].append(
                    subject_through_data
                )
            else:
                subjects[subject_through.class_grade] = [subject_through_data]

        return subjects


class AcademicProgramListSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicProgram
        fields = ('id', 'name', 'classes_count',)


class AcademicProgramCreateSerializer(serializers.ModelSerializer):
    generic_academic_program = PrimaryKeyRelatedField(queryset=GenericAcademicProgram.objects.all())
    optional_subjects = OptionalProgramSubjectThroughSerializer(many=True, allow_null=False)

    class Meta:
        model = AcademicProgram
        fields = ('id', 'name', 'classes_count', 'academic_year', 'generic_academic_program', 'core_subject', 'optional_subjects')
        read_only_fields = ('id', 'name', 'classes_count', 'academic_year')

    def validate(self, attrs):
        generic_academic_program = attrs['generic_academic_program']
        school_unit = self.context['school_unit']
        if not self.context.get('is_update') and \
                AcademicProgram.objects.filter(generic_academic_program=generic_academic_program,
                                               school_unit=school_unit, academic_year=self.context['academic_year']).exists():
            raise serializers.ValidationError({'generic_academic_program': _('You already defined this program this year.')})

        academic_profile = generic_academic_program.academic_profile
        if generic_academic_program.category_id not in school_unit.categories.values_list('id', flat=True) or \
                academic_profile != school_unit.academic_profile:
            raise serializers.ValidationError({'generic_academic_program': _('Invalid generic academic program.')})

        core_subject = attrs.get('core_subject')
        if academic_profile and academic_profile.name in PROFILES_WITH_CORE_SUBJECTS:
            if core_subject is None:
                raise serializers.ValidationError({'core_subject': _('This academic program must have a core subject.')})
            if not ProgramSubjectThrough.objects.filter(generic_academic_program=generic_academic_program, subject=core_subject).exists():
                raise serializers.ValidationError({'core_subject': _('Invalid core subject.')})
        else:
            if core_subject is not None:
                raise serializers.ValidationError({'core_subject': _('This academic program does not have a core subject.')})

        subjects_class_grades = {}
        unique_errors = {}
        hours_errors = {}
        program_max_optional_weekly_hours = generic_academic_program.optional_subjects_weekly_hours

        for subject in attrs['optional_subjects']:
            class_grade = subject['class_grade']
            subject_name = subject['subject']
            if class_grade in subjects_class_grades:
                if subject_name in subjects_class_grades[class_grade]:
                    unique_errors[class_grade] = _('Subjects must be unique per class grade.')
                else:
                    subjects_class_grades[class_grade].append(subject_name)
            else:
                subjects_class_grades[class_grade] = [subject_name]

            max_hours = program_max_optional_weekly_hours.get(class_grade, 0)
            if max_hours == 0:
                hours_errors[class_grade] = _("This program does not accept optionals for this class grade.")
            elif subject['weekly_hours_count'] > max_hours:
                hours_errors[class_grade] = _("Each optional's weekly hours should not be greater than {}.") \
                    .format(program_max_optional_weekly_hours.get(class_grade, 0))

        if unique_errors:
            raise serializers.ValidationError({'optional_subjects': unique_errors})
        if hours_errors:
            raise serializers.ValidationError({'optional_subjects': hours_errors})

        return attrs

    def create(self, validated_data):
        optional_subjects = validated_data.pop('optional_subjects')

        validated_data.update({
            'academic_year': self.context['academic_year'],
            'school_unit': self.context['school_unit'],
            'name': validated_data['generic_academic_program'].name
        })

        academic_program = super().create(validated_data)
        self.create_program_subject_through_set(optional_subjects, academic_program)

        return academic_program

    @staticmethod
    def create_program_subject_through_set(optional_subjects, academic_program):
        program_subject_through_set = []
        for subject_through_data in optional_subjects:
            subject_name = subject_through_data.pop('subject')
            subject, created = Subject.objects.get_or_create(name=subject_name)
            if created:
                subject.should_be_in_taught_subjects = False
                subject.save()

            subject_through_data['subject'] = subject
            subject_through_data['subject_name'] = subject_name
            subject_through_data['is_mandatory'] = False
            subject_through_data['academic_program'] = academic_program
            subject_through_data['class_grade_arabic'] = CLASS_GRADE_MAPPING[subject_through_data['class_grade']]
            program_subject_through_set.append(
                ProgramSubjectThrough(**subject_through_data)
            )

        ProgramSubjectThrough.objects.bulk_create(program_subject_through_set)

    def to_representation(self, instance):
        serializer = AcademicProgramDetailSerializer(instance=instance)
        return serializer.data


class AcademicProgramUpdateSerializer(serializers.ModelSerializer):
    optional_subjects = OptionalProgramSubjectThroughSerializer(many=True, allow_null=False)

    class Meta:
        model = AcademicProgram
        fields = ('core_subject', 'optional_subjects')

    def validate(self, attrs):
        self.initial_data['generic_academic_program'] = self.context['generic_academic_program_id']
        self.context.update({'is_update': True})
        serializer = AcademicProgramCreateSerializer(data=self.initial_data, context=self.context)
        serializer.is_valid(raise_exception=True)

        return attrs

    def update(self, instance, validated_data):
        optional_subjects = validated_data.pop('optional_subjects')
        instance = super().update(instance, validated_data)

        ProgramSubjectThrough.objects.filter(academic_program=instance).delete()
        AcademicProgramCreateSerializer.create_program_subject_through_set(optional_subjects, instance)

        return instance

    def to_representation(self, instance):
        serializer = AcademicProgramDetailSerializer(instance=instance)
        return serializer.to_representation(instance)


class AcademicProgramDetailSerializer(serializers.ModelSerializer):
    subjects = serializers.SerializerMethodField()
    optional_subjects_weekly_hours = serializers.JSONField(source='generic_academic_program.optional_subjects_weekly_hours')

    class Meta:
        model = AcademicProgram
        fields = ('id', 'name', 'classes_count', 'academic_year', 'core_subject', 'optional_subjects_weekly_hours', 'subjects')

    @staticmethod
    def get_subjects(obj):
        subject_through_set = ProgramSubjectThrough.objects.filter(
            Q(academic_program_id=obj.id) | Q(generic_academic_program_id=obj.generic_academic_program_id)
        ).order_by('class_grade_arabic', Lower('subject_name'))
        subjects = {}

        for subject_through in subject_through_set:
            subject_data = ProgramSubjectThroughSerializer(subject_through).data
            class_grade = subject_through.class_grade

            if not subjects.get(class_grade):
                subjects[class_grade] = {'optional_subjects': [], 'mandatory_subjects': []}

            if subject_through.is_mandatory:
                key = 'mandatory_subjects'
            else:
                key = 'optional_subjects'

            subjects[class_grade][key].append(subject_data)

        return subjects
