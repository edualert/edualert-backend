from django.utils import timezone
from django.utils.translation import gettext as _
from rest_framework import serializers

from edualert.academic_calendars.utils import get_current_academic_calendar
from edualert.catalogs.models import StudentCatalogPerSubject
from edualert.catalogs.utils import compute_averages
from edualert.profiles.constants import EXEMPTED_SPORT_LABEL, EXEMPTED_RELIGION_LABEL
from edualert.profiles.models import Label
from edualert.profiles.serializers import UserProfileBaseSerializer
from edualert.study_classes.models import TeacherClassThrough


class CatalogSettingsListSerializer(serializers.ListSerializer):
    def validate(self, attrs):
        subject = self.context['subject']
        study_class = self.context['study_class']
        user_profile = self.context['request'].user.user_profile

        is_optional_subject = TeacherClassThrough.objects \
            .filter(teacher_id=user_profile.id, study_class_id=study_class.id, subject_id=subject.id) \
            .first().is_optional_subject

        catalog_mapping = {catalog.id: catalog for catalog in self.instance}
        data_mapping = {item['id']: item for item in attrs}

        for catalog_id, data in data_mapping.items():
            catalog = catalog_mapping.get(catalog_id)
            if catalog is None:
                raise serializers.ValidationError({'general_errors': _(f'Invalid pk "{catalog_id}" - object does not exist.')})
            data['catalog'] = catalog

            if data.get('is_exempted', False) and not subject.allows_exemption:
                raise serializers.ValidationError({'is_exempted': _("This subject doesn't allow exemption.")})
            if not data.get('is_enrolled', True) and not is_optional_subject:
                raise serializers.ValidationError({'is_enrolled': _("This subject is not optional.")})

        return attrs

    def update(self, instance, validated_data):
        instances_to_update = []

        for data in validated_data:
            catalog = data['catalog']
            for attr, value in data.items():
                setattr(catalog, attr, value)
            instances_to_update.append(catalog)

        if instances_to_update:
            StudentCatalogPerSubject.objects.bulk_update(instances_to_update, ['wants_level_testing_grade', 'wants_thesis',
                                                                               'wants_simulation', 'is_exempted', 'is_enrolled'])
            current_calendar = get_current_academic_calendar()
            if not current_calendar:
                semester = 1
            else:
                semester = 2 if timezone.now().date() >= current_calendar.second_semester.starts_at else 1

            compute_averages(list(set(instances_to_update)), semester)

            subject = instances_to_update[0].subject
            if subject.allows_exemption:
                if subject.name == 'Religie':
                    label = Label.objects.filter(text=EXEMPTED_RELIGION_LABEL).first()
                else:
                    label = Label.objects.filter(text=EXEMPTED_SPORT_LABEL).first()

                for catalog in instances_to_update:
                    if catalog.is_exempted:
                        catalog.student.labels.add(label)
                    else:
                        catalog.student.labels.remove(label)

        return instance


class CatalogSettingsSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=True)
    student = UserProfileBaseSerializer(read_only=True)
    wants_level_testing_grade = serializers.BooleanField(required=True)
    wants_thesis = serializers.BooleanField(required=True)
    wants_simulation = serializers.BooleanField(required=True)

    class Meta:
        model = StudentCatalogPerSubject
        list_serializer_class = CatalogSettingsListSerializer
        fields = ('id', 'student', 'wants_level_testing_grade', 'wants_thesis',
                  'wants_simulation', 'is_exempted', 'is_enrolled')
