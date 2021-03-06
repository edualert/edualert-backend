# Generated by Django 3.0.4 on 2020-03-31 11:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SemesterCalendar',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('starts_at', models.DateField()),
                ('ends_at', models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name='SchoolEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.IntegerField(choices=[(1, 'Holiday for primary schools'), (2, 'Spring break'), (3, 'Easter')])),
                ('starts_at', models.DateField()),
                ('ends_at', models.DateField()),
                ('semester', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='school_events', to='academic_calendars.SemesterCalendar')),
            ],
        ),
        migrations.CreateModel(
            name='AcademicYearCalendar',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('academic_year', models.PositiveSmallIntegerField()),
                ('first_semester', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='first_semester_academic_year_calendar', to='academic_calendars.SemesterCalendar')),
                ('second_semester', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='second_semester_academic_year_calendar', to='academic_calendars.SemesterCalendar')),
            ],
        ),
    ]
