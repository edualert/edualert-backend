from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html, escape

from edualert.academic_programs.models import GenericAcademicProgram, AcademicProgram


class GenericAcademicProgramAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'academic_profile')
    list_filter = ('academic_profile',)
    search_fields = ('name',)
    ordering = ('name',)


class AcademicProgramAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'academic_year', 'generic_academic_program_link',
                    'classes_count', 'students_at_risk_count')
    readonly_fields = ('name',)
    search_fields = ('name',)
    ordering = ('name',)

    def generic_academic_program_link(self, instance):
        url = reverse("admin:academic_programs_genericacademicprogram_change", args=(instance.generic_academic_program.id,))
        return format_html('<a href="{}">{}</a>', url, escape(instance.generic_academic_program))

    generic_academic_program_link.short_description = "Generic academic program"

    def save_model(self, request, obj, form, change):
        obj.name = obj.generic_academic_program.name
        obj.save()


admin.site.register(GenericAcademicProgram, GenericAcademicProgramAdmin)
admin.site.register(AcademicProgram, AcademicProgramAdmin)
