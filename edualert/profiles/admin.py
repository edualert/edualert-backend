from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html, escape

from edualert.profiles.models import UserProfile, Label


class UserProfileAdmin(admin.ModelAdmin):
    exclude = ()
    list_display = ('__str__', 'full_name', 'user_role', 'user_link')
    list_filter = ('user_role',)
    search_fields = ('username', 'full_name')

    def user_link(self, instance):
        # Link to django admin user profile
        url = reverse("admin:auth_user_change", args=(instance.user.id,))
        return format_html('<a href="{}">{}</a>', url, escape(instance.user))

    user_link.short_description = "User"


class LabelAdmin(admin.ModelAdmin):
    exclude = ()
    list_display = ('__str__', 'user_role',)
    list_filter = ('user_role',)


admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Label, LabelAdmin)
