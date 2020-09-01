from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html, escape

from edualert.study_classes.models import StudyClass, TeacherClassThrough


class StudyClassAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'id', 'school_unit_link', 'academic_program_link',
                    'class_master_link', 'students_at_risk_count')
    list_filter = ('class_grade',)
    readonly_fields = ('academic_program_name',)

    def school_unit_link(self, instance):
        url = reverse("admin:schools_registeredschoolunit_change", args=(instance.school_unit.id,))
        return format_html('<a href="{}">{}</a>', url, escape(instance.school_unit))

    school_unit_link.short_description = "School unit"

    def academic_program_link(self, instance):
        if instance.academic_program:
            url = reverse("admin:academic_programs_academicprogram_change", args=(instance.academic_program.id,))
            return format_html('<a href="{}">{}</a>', url, escape(instance.academic_program))
        return '-'

    academic_program_link.short_description = "Academic program"

    def class_master_link(self, instance):
        url = reverse("admin:profiles_userprofile_change", args=(instance.class_master.id,))
        return format_html('<a href="{}">{}</a>', url, escape(instance.class_master))

    class_master_link.short_description = "Class master"

    def save_model(self, request, obj, form, change):
        if obj.academic_program:
            obj.academic_program_name = obj.academic_program.name
        obj.save()


class TeacherClassThroughAdmin(admin.ModelAdmin):
    list_display = ('id', 'study_class_link', 'teacher_link', 'subject_link', 'is_class_master')
    readonly_fields = ('academic_program_name', 'subject_name', 'is_coordination_subject')

    def study_class_link(self, instance):
        url = reverse("admin:study_classes_studyclass_change", args=(instance.study_class.id,))
        return format_html('<a href="{}">{}</a>', url, escape(instance.study_class))

    study_class_link.short_description = "Study class"

    def teacher_link(self, instance):
        url = reverse("admin:profiles_userprofile_change", args=(instance.teacher.id,))
        return format_html('<a href="{}">{}</a>', url, escape(instance.teacher))

    teacher_link.short_description = "Teacher"

    def subject_link(self, instance):
        url = reverse("admin:subjects_subject_change", args=(instance.subject.id,))
        return format_html('<a href="{}">{}</a>', url, escape(instance.subject))

    subject_link.short_description = "Subject"

    def save_model(self, request, obj, form, change):
        if obj.study_class.academic_program:
            obj.academic_program_name = obj.study_class.academic_program.name
        obj.subject_name = obj.subject.name
        obj.is_coordination_subject = obj.subject.is_coordination
        obj.save()


admin.site.register(StudyClass, StudyClassAdmin)
admin.site.register(TeacherClassThrough, TeacherClassThroughAdmin)
