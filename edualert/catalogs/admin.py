from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html, escape

from edualert.catalogs.models import StudentCatalogPerSubject, SubjectGrade, SubjectAbsence, \
    ExaminationGrade, StudentCatalogPerYear


class StudentCatalogPerSubjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'student_link', 'study_class_link', 'subject_link', 'is_enrolled',
                    'is_at_risk', 'wants_level_testing_grade', 'wants_thesis', 'wants_simulation', 'is_exempted')
    readonly_fields = ('subject_name', 'is_coordination_subject')
    search_fields = ('student__full_name', 'student__id')
    list_filter = ('study_class__class_grade',)

    def student_link(self, instance):
        url = reverse("admin:profiles_userprofile_change", args=(instance.student.id,))
        return format_html('<a href="{}">{}</a>', url, escape(instance.student))

    student_link.short_description = "Student"

    def study_class_link(self, instance):
        url = reverse("admin:study_classes_studyclass_change", args=(instance.study_class.id,))
        return format_html('<a href="{}">{}</a>', url, escape(instance.study_class))

    study_class_link.short_description = "Study class"

    def subject_link(self, instance):
        url = reverse("admin:subjects_subject_change", args=(instance.subject.id,))
        return format_html('<a href="{}">{}</a>', url, escape(instance.subject))

    subject_link.short_description = "Subject"

    def save_model(self, request, obj, form, change):
        obj.subject_name = obj.subject.name
        obj.is_coordination_subject = obj.subject.is_coordination
        obj.save()


class SubjectGradeAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'student_link', 'subject_name', 'grade', 'grade_type',
                    'academic_year', 'semester', 'taken_at')
    readonly_fields = ('subject_name',)

    def student_link(self, instance):
        url = reverse("admin:profiles_userprofile_change", args=(instance.student.id,))
        return format_html('<a href="{}">{}</a>', url, escape(instance.student))

    student_link.short_description = "Student"

    def save_model(self, request, obj, form, change):
        obj.subject_name = obj.catalog_per_subject.subject.name
        obj.save()


class SubjectAbsenceAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'student_link', 'subject_name', 'taken_at', 'is_founded',
                    'academic_year', 'semester')
    readonly_fields = ('subject_name',)

    def student_link(self, instance):
        url = reverse("admin:profiles_userprofile_change", args=(instance.student.id,))
        return format_html('<a href="{}">{}</a>', url, escape(instance.student))

    student_link.short_description = "Student"

    def save_model(self, request, obj, form, change):
        obj.subject_name = obj.catalog_per_subject.subject.name
        obj.save()


class ExaminationGradeAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'student_link', 'subject_name', 'grade1', 'grade2', 'examination_type',
                    'academic_year', 'taken_at')
    readonly_fields = ('subject_name',)

    def student_link(self, instance):
        url = reverse("admin:profiles_userprofile_change", args=(instance.student.id,))
        return format_html('<a href="{}">{}</a>', url, escape(instance.student))

    student_link.short_description = "Student"

    def save_model(self, request, obj, form, change):
        obj.subject_name = obj.catalog_per_subject.subject.name
        obj.save()


class StudentCatalogPerYearAdmin(admin.ModelAdmin):
    list_display = ('id', 'student_link', 'study_class_link')
    search_fields = ('student__full_name', 'student__id')

    def student_link(self, instance):
        url = reverse("admin:profiles_userprofile_change", args=(instance.student.id,))
        return format_html('<a href="{}">{}</a>', url, escape(instance.student))

    student_link.short_description = "Student"

    def study_class_link(self, instance):
        url = reverse("admin:study_classes_studyclass_change", args=(instance.study_class.id,))
        return format_html('<a href="{}">{}</a>', url, escape(instance.study_class))

    study_class_link.short_description = "Study class"


admin.site.register(StudentCatalogPerSubject, StudentCatalogPerSubjectAdmin)
admin.site.register(SubjectGrade, SubjectGradeAdmin)
admin.site.register(SubjectAbsence, SubjectAbsenceAdmin)
admin.site.register(ExaminationGrade, ExaminationGradeAdmin)
admin.site.register(StudentCatalogPerYear, StudentCatalogPerYearAdmin)
