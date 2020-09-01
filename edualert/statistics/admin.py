from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html, escape

from edualert.statistics.models import SchoolUnitStats, SchoolUnitEnrollmentStats, StudentAtRiskCounts


class SchoolUnitStatsAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'school_unit_link', 'academic_year', 'avg_sem1',
        'avg_annual', 'unfounded_abs_avg_sem1', 'unfounded_abs_avg_sem2', 'unfounded_abs_avg_annual'
    )
    list_filter = ('school_unit', 'academic_year')
    search_fields = ('school_unit_name',)
    readonly_fields = ('school_unit_name',)

    def school_unit_link(self, instance):
        url = reverse("admin:schools_registeredschoolunit_change", args=(instance.school_unit.id,))
        return format_html('<a href="{}">{}</a>', url, escape(instance.school_unit))

    school_unit_link.short_description = "School Unit"

    def save_model(self, request, obj, form, change):
        obj.school_unit_name = obj.school_unit.name
        obj.save()


class SchoolUnitEnrollmentStatsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'year', 'month')
    list_filter = ('year',)


class StudentAtRiskCountsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'school_unit_link', 'study_class_link', 'year', 'month', 'by_country')
    list_filter = ('study_class', 'school_unit')

    def study_class_link(self, instance):
        study_class = getattr(instance, 'study_class', None)
        if study_class:
            url = reverse("admin:study_classes_studyclass_change", args=(study_class.id,))
            return format_html('<a href="{}">{}</a>', url, escape(instance.study_class))
        return ''
    study_class_link.short_description = "Study class"

    def school_unit_link(self, instance):
        school_unit = getattr(instance, 'school_unit', None)
        if school_unit:
            url = reverse("admin:schools_registeredschoolunit_change", args=(school_unit.id,))
            return format_html('<a href="{}">{}</a>', url, escape(instance.school_unit))
        return ''

    school_unit_link.short_description = "School Unit"


admin.site.register(SchoolUnitEnrollmentStats, SchoolUnitEnrollmentStatsAdmin)
admin.site.register(StudentAtRiskCounts, StudentAtRiskCountsAdmin)
admin.site.register(SchoolUnitStats, SchoolUnitStatsAdmin)
