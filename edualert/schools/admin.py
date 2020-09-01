from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html, escape

from edualert.schools.models import SchoolUnit, SchoolUnitCategory, RegisteredSchoolUnit, SchoolUnitProfile


class SchoolUnitAdmin(admin.ModelAdmin):
    exclude = ()
    list_display = ('__str__', 'district', 'city',)
    list_filter = ('city', 'district', )
    search_fields = ('name',)
    ordering = ('district', 'city', 'name',)


class SchoolUnitCategoryAdmin(admin.ModelAdmin):
    exclude = ()
    list_display = ('__str__', 'category_level')
    list_filter = ('category_level', )
    search_fields = ('name',)


class SchoolUnitProfileAdmin(admin.ModelAdmin):
    exclude = ()
    list_display = ('__str__',)
    search_fields = ('name',)


class RegisteredSchoolUnitAdmin(admin.ModelAdmin):
    exclude = ()
    list_display = ('__str__', 'district', 'city', 'academic_profile', 'school_principal_link', 'students_at_risk_count',)
    list_filter = ('district', 'city', 'academic_profile',)
    search_fields = ('name',)

    def school_principal_link(self, instance):
        url = reverse("admin:profiles_userprofile_change", args=(instance.school_principal.id,))
        return format_html('<a href="{}">{}</a>', url, escape(instance.school_principal))

    school_principal_link.short_description = "School principal"


admin.site.register(SchoolUnit, SchoolUnitAdmin)
admin.site.register(SchoolUnitCategory, SchoolUnitCategoryAdmin)
admin.site.register(SchoolUnitProfile, SchoolUnitProfileAdmin)
admin.site.register(RegisteredSchoolUnit, RegisteredSchoolUnitAdmin)
