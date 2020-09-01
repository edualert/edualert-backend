from rest_framework import serializers

from edualert.catalogs.models import SubjectAbsence
from edualert.catalogs.serializers import StudentCatalogPerSubjectSerializer
from edualert.catalogs.serializers.common import SubjectGradeAbsenceCreateBulkBaseSerializer, validate_and_get_semester
from edualert.catalogs.utils import update_last_change_in_catalog, change_absences_counts_on_add, change_absence_counts_on_bulk_add


class SubjectAbsenceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubjectAbsence
        fields = ('taken_at', 'is_founded')

    def validate(self, attrs):
        attrs['semester'] = validate_and_get_semester(attrs['taken_at'])
        return attrs

    def create(self, validated_data):
        catalog = self.context['catalog']

        instance = SubjectAbsence.objects.create(catalog_per_subject=catalog, student=catalog.student, subject_name=catalog.subject_name,
                                                 academic_year=catalog.academic_year, **validated_data)
        change_absences_counts_on_add(catalog, instance)

        update_last_change_in_catalog(self.context['request'].user.user_profile)
        return instance

    def to_representation(self, instance):
        catalog = self.context['catalog']
        return StudentCatalogPerSubjectSerializer(catalog).data


class StudentAbsence(serializers.ModelSerializer):
    class Meta:
        model = SubjectAbsence
        fields = ('student', 'is_founded')


class SubjectAbsenceCreateBulkSerializer(SubjectGradeAbsenceCreateBulkBaseSerializer):
    student_absences = StudentAbsence(many=True)

    class Meta:
        model = SubjectAbsence
        fields = ('taken_at', 'student_absences')

    def validate(self, attrs):
        attrs = super().validate(attrs)
        self.validate_related_objects(attrs['student_absences'])
        return attrs

    def create(self, validated_data):
        taken_at = validated_data['taken_at']
        semester = validated_data['semester']
        student_absences = validated_data['student_absences']

        instances_to_create = []
        for student_absence in student_absences:
            instances_to_create.append(
                SubjectAbsence(subject_name=self.context['subject'].name, semester=semester, taken_at=taken_at, **student_absence)
            )

        instances = SubjectAbsence.objects.bulk_create(instances_to_create)
        change_absence_counts_on_bulk_add(instances, semester)

        update_last_change_in_catalog(self.context['request'].user.user_profile)
        return instances
