# Generated by Django 3.0.4 on 2020-03-31 12:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subjects', '0001_initial'),
        ('profiles', '0005_auto_20200324_1217'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='taught_subjects',
            field=models.ManyToManyField(blank=True, help_text='Only for teachers and school principals.', related_name='teachers', to='subjects.Subject'),
        ),
    ]
