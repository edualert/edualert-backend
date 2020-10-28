# Generated by Django 3.0.4 on 2020-10-28 11:05

from django.db import migrations, models
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0008_auto_20200504_1339'),
    ]

    operations = [
        migrations.CreateModel(
            name='SentEmailAlternative',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('from_email', models.TextField()),
                ('subject', models.TextField()),
                ('cc', models.TextField()),
                ('bcc', models.TextField()),
                ('mime_type', models.TextField()),
                ('content', models.TextField()),
                ('sent_at', models.DateTimeField()),
            ],
            options={
                'ordering': ('-sent_at',),
            },
        ),
        migrations.CreateModel(
            name='SentSms',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('recipient', models.TextField()),
                ('message', models.TextField()),
                ('nonce', models.TextField()),
                ('sent_at', models.DateTimeField()),
            ],
            options={
                'ordering': ('-sent_at',),
            },
        ),
    ]
