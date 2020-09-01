from django.utils import timezone
from django.utils.translation import gettext as _
from rest_framework import serializers

from edualert.catalogs.models import ExaminationGrade
from edualert.catalogs.serializers import StudentCatalogPerSubjectSerializer
from edualert.catalogs.utils import update_last_change_in_catalog, can_update_examination_grades, \
    change_averages_after_examination_grade_operation


class ExaminationGradeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExaminationGrade
        fields = ('taken_at', 'grade1', 'grade2', 'examination_type', 'grade_type', 'semester')

    def validate(self, attrs):
        catalog = self.context['catalog']
        grade_type = attrs['grade_type']
        examination_type = attrs['examination_type']
        semester = attrs.get('semester')

        if not can_update_examination_grades(catalog.study_class, grade_type):
            raise serializers.ValidationError({'general_errors': _("Can't create grades at this time.")})

        if grade_type == ExaminationGrade.GradeTypes.DIFFERENCE:
            if semester is not None:
                if any([grade.semester == semester for grade in catalog.grades.all()]):
                    raise serializers.ValidationError({'general_errors': _("Can't add difference grades in semesters where there are regular grades.")})
            else:
                if len(catalog.grades.all()) > 0:
                    raise serializers.ValidationError({'general_errors': _("Can't add difference grades in catalogs where there are regular grades.")})

        if attrs['taken_at'] > timezone.now().date():
            raise serializers.ValidationError({'taken_at': _("Can't add grades in the future.")})

        for key, value in zip(['grade1', 'grade2'], [attrs['grade1'], attrs['grade2']]):
            if not 0 < value <= 10:
                raise serializers.ValidationError({key: _('Grade must be between 1 and 10.')})

        if grade_type == ExaminationGrade.GradeTypes.SECOND_EXAMINATION and attrs.get('semester') is not None:
            raise serializers.ValidationError({'semester': _("This field can be added only to difference grades.")})

        if grade_type == ExaminationGrade.GradeTypes.SECOND_EXAMINATION:
            # For 'Corigente' we allow max 1 pair (oral-written) of grades per catalog
            if catalog.examination_grades.filter(examination_type=examination_type).exists():
                raise serializers.ValidationError({'examination_type': _("You already added a grade with this examination type.")})
        else:
            # For 'Diferente' we allow max 1 pair (oral-written) of grades per year OR per semester
            existing_grades = catalog.examination_grades.all()

            if semester is not None:
                # Difference grade for a semester
                if semester not in [1, 2]:
                    raise serializers.ValidationError({'semester': _("Invalid value.")})

                for grade in existing_grades:
                    if grade.semester is None:
                        raise serializers.ValidationError({'semester': _("You cannot add difference grades for a semester because "
                                                                         "you have difference grades for the whole year in this catalog.")})
                    if grade.examination_type == examination_type and grade.semester == semester:
                        raise serializers.ValidationError({'examination_type': _("You already added a grade with this examination type.")})
            else:
                # Difference grade for entire year
                for grade in existing_grades:
                    if grade.semester is not None:
                        raise serializers.ValidationError({'semester': _("You cannot add difference grades for the whole year because "
                                                                         "you have difference grades for a semester in this catalog.")})
                    if grade.examination_type == examination_type:
                        raise serializers.ValidationError({'examination_type': _("You already added a grade with this examination type.")})

        return attrs

    def create(self, validated_data):
        catalog = self.context['catalog']
        instance = ExaminationGrade.objects.create(
            catalog_per_subject=catalog,
            student_id=catalog.student_id,
            subject_name=catalog.subject_name,
            academic_year=catalog.academic_year,
            **validated_data
        )

        change_averages_after_examination_grade_operation([catalog], instance.grade_type, instance.semester)
        update_last_change_in_catalog(self.context['request'].user.user_profile)
        return instance

    def to_representation(self, instance):
        return StudentCatalogPerSubjectSerializer(self.context['catalog']).data


class ExaminationGradeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExaminationGrade
        fields = ('taken_at', 'grade1', 'grade2')

    def validate(self, attrs):

        if attrs['taken_at'] > timezone.now().date():
            raise serializers.ValidationError({'taken_at': _("Can't set grade dates in the future.")})

        for key, value in zip(['grade1', 'grade2'], [attrs['grade1'], attrs['grade2']]):
            if not 0 < value <= 10:
                raise serializers.ValidationError({key: _('Grade must be between 1 and 10.')})

        return attrs

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)

        change_averages_after_examination_grade_operation([instance.catalog_per_subject], instance.grade_type, instance.semester)
        update_last_change_in_catalog(self.context['request'].user.user_profile)

        return instance

    def to_representation(self, instance):
        return StudentCatalogPerSubjectSerializer(instance.catalog_per_subject).data
