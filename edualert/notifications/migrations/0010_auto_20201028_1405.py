# Generated by Django 3.0.4 on 2020-10-28 14:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0009_sentemailalternative_sentsms'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='sentsms',
            options={'ordering': ('-sent_at',), 'verbose_name_plural': 'sent sms'},
        ),
    ]
