from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.utils.translation import gettext as _
from rest_framework import serializers

from edualert.academic_calendars.models import AcademicYearCalendar, SemesterCalendar, SchoolEvent
from edualert.academic_calendars.tasks import calculate_semesters_working_weeks_task
from edualert.academic_calendars.utils import check_event_is_semester_end
from edualert.common.utils import check_date_range_overlap


def check_school_events_overlap(events):
    for index in range(0, len(events)):
        for index2 in range(index + 1, len(events)):
            if index < len(events) and check_date_range_overlap(
                    events[index]['starts_at'], events[index]['ends_at'],
                    events[index2]['starts_at'], events[index2]['ends_at']
            ):
                return True

    return False


class SchoolEventSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = SchoolEvent
        fields = ('id', 'event_type', 'starts_at', 'ends_at',)

    def validate(self, attrs):
        # TODO uncomment this after it's implemented & tested on FE
        # if attrs['starts_at'] < timezone.now().date():
        #     raise serializers.ValidationError({'starts_at': _('The start date must be in the future.')})
        # if attrs['ends_at'] < timezone.now().date():
        #     raise serializers.ValidationError({'ends_at': _('The end date must be in the future.')})
        if attrs['starts_at'] > attrs['ends_at']:
            raise serializers.ValidationError({'starts_at': _('The start date must be before the end date.')})

        return attrs


class SemesterCalendarSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    events = SchoolEventSerializer(many=True, source='school_events', required=True)

    class Meta:
        model = SemesterCalendar
        fields = ('id', 'starts_at', 'ends_at', 'events',)

    def validate(self, attrs):
        # TODO uncomment this after it's implemented & tested on FE
        # if attrs['starts_at'] < timezone.now().date():
        #     raise serializers.ValidationError({'starts_at': _('The start date must be in the future.')})
        # if attrs['ends_at'] < timezone.now().date():
        #     raise serializers.ValidationError({'ends_at': _('The end date must be in the future.')})
        if attrs['starts_at'] >= attrs['ends_at']:
            raise serializers.ValidationError({'starts_at': _('The start date must be before the end date.')})

        for event in attrs['school_events']:
            if CurrentAcademicYearCalendarSerializer.check_event_is_year_event(event['event_type']):
                raise serializers.ValidationError({'events': _('{} events cannot be inside semesters.')
                                                  .format(getattr(SchoolEvent.EventTypes, event['event_type']).label)})

        return attrs


class CurrentAcademicYearCalendarSerializer(serializers.ModelSerializer):
    first_semester = SemesterCalendarSerializer()
    second_semester = SemesterCalendarSerializer()
    events = SchoolEventSerializer(many=True, source='school_events', required=True)

    class Meta:
        model = AcademicYearCalendar
        fields = ('first_semester', 'second_semester', 'academic_year', 'events')
        read_only_fields = ('academic_year',)

    @staticmethod
    def check_event_inside_semester(semester_data, event_data, semester_final_date, calendar_end_date):
        if event_data['event_type'] == SchoolEvent.EventTypes.SECOND_SEMESTER_END_IX_XI_FILIERA_TEHNOLOGICA and \
                not semester_data['starts_at'] < event_data['starts_at'] <= event_data['ends_at'] < calendar_end_date:
            raise serializers.ValidationError(
                {'events': {
                    'starts_at': _("Second semester end for Filiera Tehnologica must be between the second semester's start and the end of the current academic year.")
                }}
            )
        elif not semester_data['starts_at'] <= event_data['starts_at'] <= event_data['ends_at'] <= semester_final_date:
            return False

        return True

    @staticmethod
    def get_calendar_end_date(starts_at):
        one_year_today = starts_at + relativedelta(years=1)
        return one_year_today - relativedelta(days=1)

    @staticmethod
    def check_event_is_year_event(event_type):
        return event_type in [
            SchoolEvent.EventTypes.CORIGENTE,
            SchoolEvent.EventTypes.DIFERENTE
        ]

    @staticmethod
    def get_semester_final_date(semester_name, semester_data):
        if semester_name == 'second_semester':
            semester_events = semester_data['school_events']
            for event in semester_events:
                if event['event_type'] == SchoolEvent.EventTypes.SECOND_SEMESTER_END_IX_XI_FILIERA_TEHNOLOGICA and event['ends_at'] > semester_data['ends_at']:
                    return event['ends_at']

        return semester_data['ends_at']

    def validate(self, attrs):
        if not self.instance:
            return

        first_semester = attrs['first_semester']
        second_semester = attrs['second_semester']
        calendar_end_date = self.get_calendar_end_date(first_semester['starts_at'])
        events = attrs['school_events'] + first_semester['school_events'] + second_semester['school_events']
        actual_events = {
            event['id']: SchoolEvent.objects.filter(id=event['id'])
            for event in events if event.get('id')
        }

        if second_semester['starts_at'] < first_semester['ends_at']:
            raise serializers.ValidationError(
                {'second_semester': _('Second semester must start after the end of the first semester.')}
            )

        # Semester dates must not overlap
        if check_date_range_overlap(first_semester['starts_at'], first_semester['ends_at'],
                                    second_semester['starts_at'], second_semester['ends_at']):
            raise serializers.ValidationError({'general_errors': _('Semester dates cannot overlap.')})

        event_does_not_exist_error = _('The events must belong to this academic year.')

        # Events must exist and must have valid ranges
        for event in attrs['school_events']:
            if event.get('id') is not None:
                actual_event = actual_events.get(event['id'])
                if not actual_event or actual_event.first().academic_year_calendar_id != self.instance.id:
                    raise serializers.ValidationError({'events': {'id': event_does_not_exist_error}})

                # Save the querysets here so we don't need to refetch them on update
                event['actual_event'] = actual_event

            if not self.check_event_is_year_event(event['event_type']):
                raise serializers.ValidationError(
                    {'events': {'event_type': _("{} must belong to a semester.")
                        .format(getattr(SchoolEvent.EventTypes, event['event_type']).label)}}
                )

            if not second_semester['ends_at'] < event['starts_at'] <= event['ends_at'] <= calendar_end_date:
                raise serializers.ValidationError({'events': {'starts_at': _('{} must be between the second semester end date and the end of the current year.')
                                                  .format(getattr(SchoolEvent.EventTypes, event['event_type']).label)}})

        for semester in ['first_semester', 'second_semester']:
            semester_id = attrs[semester]['id']

            if semester_id != getattr(self.instance, semester).id:
                raise serializers.ValidationError({semester: _('The semester must belong to the academic year.')})

            semester_final_date = self.get_semester_final_date(semester, attrs[semester])
            for event in attrs[semester]['school_events']:
                if semester == 'first_semester' and check_event_is_semester_end(event['event_type']):
                    raise serializers.ValidationError(
                        {semester: {'events': {'event_type': _("{} must belong to the second semester.")
                            .format(getattr(SchoolEvent.EventTypes, event['event_type']).label)}}}
                    )

                if event.get('id') is not None:
                    actual_event = actual_events.get(event['id'])
                    if not actual_event or actual_event.first().semester_id != semester_id:
                        raise serializers.ValidationError({semester: {'events': {'id': event_does_not_exist_error}}})
                    event['actual_event'] = actual_event

                if not self.check_event_inside_semester(attrs[semester], event, semester_final_date, calendar_end_date):
                    raise serializers.ValidationError(
                        {semester: {'events': {'starts_at': _("All events must be between the semester's start and end dates.")}}}
                    )

        if check_school_events_overlap(events):
            raise serializers.ValidationError({'events': _('Events cannot overlap.')})

        return attrs

    @staticmethod
    def update_events(instance, events):
        actual_events = []
        actual_events_ids = []
        for event in events:
            if event.get('actual_event'):
                actual_event = event.pop('actual_event')
                actual_event.update(**event)
                actual_event = actual_event.first()
            else:
                if isinstance(instance, SemesterCalendar):
                    fk_name = 'semester'
                else:
                    fk_name = 'academic_year_calendar'
                actual_event = SchoolEvent.objects.create(**{fk_name: instance}, **event)
            actual_events.append(actual_event)
            actual_events_ids.append(actual_event.id)

        instance.school_events.exclude(id__in=actual_events_ids).delete()
        instance.school_events.set(actual_events)

    def update(self, instance, validated_data):
        academic_year_events = validated_data.pop('school_events')
        self.update_events(instance, academic_year_events)

        first_semester_events = validated_data['first_semester'].pop('school_events')
        second_semester_events = validated_data['second_semester'].pop('school_events')
        self.update_events(instance.first_semester, first_semester_events)
        self.update_events(instance.second_semester, second_semester_events)

        first_semester = validated_data.pop('first_semester')
        second_semester = validated_data.pop('second_semester')
        SemesterCalendar.objects.filter(id=first_semester['id']).update(**first_semester)
        SemesterCalendar.objects.filter(id=second_semester['id']).update(**second_semester)

        calculate_semesters_working_weeks_task.delay(instance.id)
        return instance
