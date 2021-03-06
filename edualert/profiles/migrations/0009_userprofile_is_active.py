# Generated by Django 3.0.4 on 2020-04-01 15:23

from django.db import migrations, models


def update_is_active_for_user_profiles(apps, schema_editor):
    UserProfile = apps.get_model('profiles', 'UserProfile')
    for profile in UserProfile.objects.all():
        profile.is_active = profile.user.is_active
        profile.save()


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0008_auto_20200401_1124'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.RunPython(code=update_is_active_for_user_profiles, reverse_code=migrations.RunPython.noop)
    ]
