from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html, escape

from edualert.subjects.models import Subject, ProgramSubjectThrough


class SubjectAdmin(admin.ModelAdmin):
    list_display = ('__str__',)
    search_fields = ('name',)
    ordering = ('name',)


class ProgramSubjectThroughAdmin(admin.ModelAdmin):
    list_display = ('id', 'generic_academic_program_link', 'academic_program_link',
                    'subject_link', 'class_grade', 'weekly_hours_count', 'is_mandatory')
    readonly_fields = ('subject_name',)
    search_fields = ('subject_name',)
    list_filter = ('is_mandatory', 'class_grade')

    def generic_academic_program_link(self, instance):
        if instance.generic_academic_program:
            url = reverse("admin:academic_programs_genericacademicprogram_change", args=(instance.generic_academic_program.id,))
            return format_html('<a href="{}">{}</a>', url, escape(instance.generic_academic_program))
        return '-'

    generic_academic_program_link.short_description = "Generic academic program"

    def academic_program_link(self, instance):
        if instance.academic_program:
            url = reverse("admin:academic_programs_academicprogram_change", args=(instance.academic_program.id,))
            return format_html('<a href="{}">{}</a>', url, escape(instance.academic_program))
        return '-'

    academic_program_link.short_description = "Academic program"

    def subject_link(self, instance):
        url = reverse("admin:subjects_subject_change", args=(instance.subject.id,))
        return format_html('<a href="{}">{}</a>', url, escape(instance.subject))

    subject_link.short_description = "Subject"

    def save_model(self, request, obj, form, change):
        obj.subject_name = obj.subject.name
        obj.save()


admin.site.register(Subject, SubjectAdmin)
admin.site.register(ProgramSubjectThrough, ProgramSubjectThroughAdmin)
