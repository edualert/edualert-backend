from django.contrib import admin

from edualert.academic_calendars.models import SemesterCalendar, SchoolEvent, AcademicYearCalendar


class SemesterCalendarAdmin(admin.ModelAdmin):
    exclude = ()
    list_display = ('__str__', 'starts_at', 'ends_at')


class SchoolEventAdmin(admin.ModelAdmin):
    exclude = ()
    list_display = ('__str__', 'event_type', 'starts_at', 'ends_at', 'semester')
    list_filter = ('semester', 'event_type')


class AcademicYearCalendarAdmin(admin.ModelAdmin):
    exclude = ()
    list_display = ('__str__',)


admin.site.register(SemesterCalendar, SemesterCalendarAdmin)
admin.site.register(SchoolEvent, SchoolEventAdmin)
admin.site.register(AcademicYearCalendar, AcademicYearCalendarAdmin)
