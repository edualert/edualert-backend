# Generated by Django 3.0.4 on 2020-05-04 13:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0012_auto_20200415_1238'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='address',
            field=models.CharField(blank=True, help_text='Only for students and parents.', max_length=100, null=True),
        ),
    ]
