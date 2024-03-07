# Generated by Django 4.2.3 on 2023-08-26 16:59

import cap_feed.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cap_feed', '0009_alter_alertinfo_audience_alter_alertinfo_contact_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='alert',
            name='addresses',
            field=models.TextField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='alert',
            name='code',
            field=models.CharField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='alert',
            name='incidents',
            field=models.TextField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='alert',
            name='note',
            field=models.TextField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='alert',
            name='references',
            field=models.TextField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='alert',
            name='restriction',
            field=models.CharField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='alert',
            name='scope',
            field=models.CharField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='alert',
            name='source',
            field=models.CharField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='alertinfo',
            name='expires',
            field=models.DateTimeField(blank=True, default=cap_feed.models.AlertInfo.default_expire, null=True),
        ),
        migrations.AlterField(
            model_name='alertinfo',
            name='onset',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
