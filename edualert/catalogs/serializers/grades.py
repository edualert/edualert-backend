from django.utils import timezone
from django.utils.translation import gettext as _
from rest_framework import serializers

from edualert.academic_calendars.utils import get_current_academic_calendar
from edualert.catalogs.models import SubjectGrade
from edualert.catalogs.serializers import StudentCatalogPerSubjectSerializer
from edualert.catalogs.serializers.common import SubjectGradeAbsenceCreateBulkBaseSerializer
from edualert.catalogs.utils import update_last_change_in_catalog, compute_averages
from edualert.catalogs.tasks import update_behavior_grades_task


class SubjectGradeCreateUpdateBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubjectGrade

    def validate(self, attrs):
        today = timezone.now().date()
        if not 0 < attrs['grade'] <= 10:
            raise serializers.ValidationError({'grade': _('Grade must be between 1 and 10.')})

        if attrs['taken_at'] > today:
            raise serializers.ValidationError({'taken_at': _("Can't set grade date in the future.")})

        current_calendar = get_current_academic_calendar()
        semester = 2 if today >= current_calendar.second_semester.starts_at else 1
        if attrs['taken_at'] < current_calendar.second_semester.starts_at <= today:
            raise serializers.ValidationError({'taken_at': _("Can't set date in the first semester.")})

        if not self.instance:
            attrs['semester'] = semester
        return attrs

    def to_representation(self, instance):
        catalog = self.context.get('catalog') or self.instance.catalog_per_subject
        return StudentCatalogPerSubjectSerializer(catalog).data


class SubjectGradeCreateSerializer(SubjectGradeCreateUpdateBaseSerializer):
    class Meta:
        model = SubjectGrade
        fields = ('grade', 'taken_at', 'grade_type')

    def validate(self, attrs):
        attrs = super().validate(attrs)
        catalog = self.context['catalog']
        semester = attrs['semester']

        if attrs['grade_type'] == SubjectGrade.GradeTypes.THESIS:
            if not catalog.wants_thesis:
                raise serializers.ValidationError(
                    {'grade_type': _("You cannot add a thesis grade for this student.")}
                )

            if catalog.grades.filter(
                grade_type=SubjectGrade.GradeTypes.THESIS, semester=semester
            ).exists():
                raise serializers.ValidationError(
                    {'grade_type': _("There can be only one thesis grade per subject per semester.")}
                )

        return attrs

    def create(self, validated_data):
        catalog = self.context['catalog']
        instance = super().create({
            'catalog_per_subject': catalog,
            'student_id': catalog.student_id,
            'subject_name': catalog.subject_name,
            'academic_year': catalog.academic_year,
            **validated_data
        })

        compute_averages([catalog], instance.semester)
        update_last_change_in_catalog(self.context['request'].user.user_profile)
        return instance


class SubjectGradeUpdateSerializer(SubjectGradeCreateUpdateBaseSerializer):
    class Meta:
        model = SubjectGrade
        fields = ('grade', 'taken_at')

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        catalog = instance.catalog_per_subject

        if instance.catalog_per_subject.is_coordination_subject:
            if instance.semester == 1:
                catalog.avg_sem1 = instance.grade
            else:
                catalog.avg_sem2 = instance.grade
                catalog.avg_annual = (catalog.avg_sem1 + catalog.avg_sem2) / 2
                catalog.avg_final = catalog.avg_annual
            catalog.save()
            update_behavior_grades_task.delay(instance.student_id, instance.semester, instance.grade)
        else:
            compute_averages([catalog], instance.semester)

        update_last_change_in_catalog(self.context['request'].user.user_profile)
        return instance


class StudentGrade(serializers.ModelSerializer):
    class Meta:
        model = SubjectGrade
        fields = ('student', 'grade')

    def validate(self, attrs):
        if not 0 < attrs['grade'] <= 10:
            raise serializers.ValidationError({'grade': _('Grade must be between 1 and 10.')})

        return attrs


class SubjectGradeCreateBulkSerializer(SubjectGradeAbsenceCreateBulkBaseSerializer):
    student_grades = StudentGrade(many=True)

    class Meta:
        model = SubjectGrade
        fields = ('taken_at', 'student_grades')

    def validate(self, attrs):
        attrs = super().validate(attrs)
        self.validate_related_objects(attrs['student_grades'], True)
        return attrs

    def create(self, validated_data):
        taken_at = validated_data['taken_at']
        semester = validated_data['semester']
        student_grades = validated_data['student_grades']

        instances_to_create = []
        for student_grade in student_grades:
            instances_to_create.append(
                SubjectGrade(
                    subject_name=self.context['subject'].name,
                    semester=semester,
                    taken_at=taken_at,
                    grade_type=SubjectGrade.GradeTypes.REGULAR,
                    **student_grade
                )
            )

        instances = SubjectGrade.objects.bulk_create(instances_to_create)

        compute_averages(list(set(instance.catalog_per_subject for instance in instances)), semester)
        update_last_change_in_catalog(self.context['request'].user.user_profile)
        return instances
