# Generated by Django 3.0.4 on 2020-05-14 14:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalogs', '0004_auto_20200513_0919'),
    ]

    operations = [
        migrations.AddField(
            model_name='examinationgrade',
            name='grade_type',
            field=models.IntegerField(choices=[(1, 'Second examination'), (2, 'Difference')], default=1),
            preserve_default=False,
        ),
    ]