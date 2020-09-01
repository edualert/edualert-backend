from django.http import Http404
from rest_framework.generics import RetrieveUpdateAPIView

from edualert.academic_calendars.permissions import AcademicCalendarPermissionClass
from edualert.academic_calendars.serializers import CurrentAcademicYearCalendarSerializer
from edualert.academic_calendars.utils import get_current_academic_calendar
from edualert.common.constants import GET, PUT, OPTIONS, HEAD


class CurrentAcademicYearCalendar(RetrieveUpdateAPIView):
    permission_classes = (AcademicCalendarPermissionClass,)
    serializer_class = CurrentAcademicYearCalendarSerializer
    http_method_names = [GET.lower(), PUT.lower(), OPTIONS.lower(), HEAD.lower()]

    def get_object(self):
        calendar = get_current_academic_calendar()
        if not calendar:
            raise Http404()

        return calendar
