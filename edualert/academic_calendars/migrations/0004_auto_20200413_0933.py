# Generated by Django 3.0.4 on 2020-04-13 09:33

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('academic_calendars', '0003_auto_20200409_0547'),
    ]

    operations = [
        migrations.AlterField(
            model_name='schoolevent',
            name='event_type',
            field=models.IntegerField(choices=[(1, 'Semester II end for VIII grade'), (2, "Semester II end for XII & XIII grade ('seral & frecvență redusă')"),
                                               (3, "Semester II end for IX-XI grades, profile 'Filieră Tehnologică'"), (4, 'I-IV grades autumn holiday'), (5, 'Winter holiday'),
                                               (6, 'Spring holiday'), (7, 'Legal/Public holiday'), (8, 'Corigente'), (9, 'Diferente')]),
        ),
    ]
