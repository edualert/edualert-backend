from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from edualert.study_classes.constants import CLASS_GRADE_MAPPING
from edualert.subjects.models import Subject, ProgramSubjectThrough


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ('id', 'name')


class OptionalProgramSubjectThroughSerializer(serializers.ModelSerializer):
    subject = serializers.CharField(max_length=100)

    def validate(self, attrs):
        if attrs['class_grade'] not in CLASS_GRADE_MAPPING:
            raise serializers.ValidationError({'class_grade': _('Invalid class grade.')})

        if attrs['weekly_hours_count'] == 0:
            raise serializers.ValidationError({'weekly_hours_count': _('The number of hours must be greater than 0.')})

        return attrs

    class Meta:
        model = ProgramSubjectThrough
        fields = ('class_grade', 'subject', 'weekly_hours_count')


class SimpleProgramSubjectThroughSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramSubjectThrough
        fields = ('subject_id', 'subject_name', 'is_mandatory')


class ProgramSubjectThroughSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramSubjectThrough
        fields = ('subject_id', 'subject_name', 'id', 'weekly_hours_count')


class TaughtSubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ('id', 'name', 'is_coordination', 'allows_exemption')
