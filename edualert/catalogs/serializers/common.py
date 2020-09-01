from django.db.models.functions import Lower
from django.utils import timezone
from django.utils.translation import gettext as _
from methodtools import lru_cache
from rest_framework import serializers

from edualert.academic_calendars.utils import get_current_academic_calendar
from edualert.catalogs.models import StudentCatalogPerSubject
from edualert.catalogs.serializers import StudentCatalogPerSubjectSerializer
from edualert.catalogs.utils import get_avg_limit_for_subject, has_technological_category, get_working_weeks_count, get_weekly_hours_count


def validate_and_get_semester(taken_at):
    today = timezone.now().date()
    current_calendar = get_current_academic_calendar()

    if taken_at > today:
        raise serializers.ValidationError({'taken_at': _('The date cannot be in the future.')})

    second_sem_start = current_calendar.second_semester.starts_at
    if taken_at < second_sem_start <= today:
        raise serializers.ValidationError({'taken_at': _('The date cannot be in the first semester.')})

    return 2 if today >= second_sem_start else 1


class SubjectGradeAbsenceCreateBulkBaseSerializer(serializers.ModelSerializer):
    @lru_cache(maxsize=None)
    def get_catalog(self, student_id):
        return StudentCatalogPerSubject.objects.filter(study_class_id=self.context['study_class'].id, is_enrolled=True, student__is_active=True,
                                                       subject_id=self.context['subject'].id, student_id=student_id).first()

    def validate_related_objects(self, objects, check_is_exempted=False):
        for instance in objects:
            student = instance['student']
            catalog = self.get_catalog(student.id)
            if catalog is None:
                raise serializers.ValidationError({'student': _(f'Invalid pk "{student.id}" - object does not exist.')})
            if check_is_exempted and catalog.is_exempted:
                raise serializers.ValidationError({'student': _(f'Invalid pk "{student.id}" - student is exempted and cannot have grades.')})

            instance['catalog_per_subject'] = catalog
            instance['academic_year'] = catalog.academic_year

    def validate(self, attrs):
        attrs['semester'] = validate_and_get_semester(attrs['taken_at'])
        return attrs

    def to_representation(self, instance):
        study_class = self.context['study_class']
        subject = self.context['subject']
        calendar = get_current_academic_calendar()

        is_technological_school = has_technological_category(study_class.school_unit)
        working_weeks_count_sem1 = get_working_weeks_count(calendar, 1, study_class, is_technological_school)
        working_weeks_count_sem2 = get_working_weeks_count(calendar, 2, study_class, is_technological_school)
        weekly_hours_count = get_weekly_hours_count(study_class, subject.id)

        third_of_hours_count_sem1 = (working_weeks_count_sem1 * weekly_hours_count) // 3
        third_of_hours_count_sem2 = (working_weeks_count_sem2 * weekly_hours_count) // 3

        self.context.update({
            'avg_limit': get_avg_limit_for_subject(study_class, subject.is_coordination, subject.id),
            'third_of_hours_count_sem1': third_of_hours_count_sem1,
            'third_of_hours_count_sem2': third_of_hours_count_sem2,
            'third_of_hours_count_annual': third_of_hours_count_sem1 + third_of_hours_count_sem2,
        })

        catalogs = StudentCatalogPerSubjectSerializer(
            instance=StudentCatalogPerSubject.objects
                .filter(study_class_id=self.context['study_class'].id, subject_id=self.context['subject'].id,
                        teacher_id=self.context['request'].user.user_profile.id, is_enrolled=True)
                .prefetch_related('grades', 'absences', 'examination_grades')
                .order_by(Lower('student__full_name')),
            many=True,
            context=self.context
        ).data

        # Convert response data to dictionary
        return {
            "catalogs": catalogs
        }
