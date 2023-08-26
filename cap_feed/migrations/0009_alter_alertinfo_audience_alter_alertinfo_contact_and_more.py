# Generated by Django 4.2.3 on 2023-08-26 16:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cap_feed', '0008_rename_expiredalert_processedalert'),
    ]

    operations = [
        migrations.AlterField(
            model_name='alertinfo',
            name='audience',
            field=models.CharField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='alertinfo',
            name='contact',
            field=models.CharField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='alertinfo',
            name='event_code',
            field=models.CharField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='alertinfo',
            name='headline',
            field=models.CharField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='alertinfo',
            name='onset',
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='alertinfo',
            name='parameter',
            field=models.CharField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='alertinfo',
            name='response_type',
            field=models.CharField(blank=True, choices=[('Shelter', 'Shelter'), ('Evacuate', 'Evacuate'), ('Prepare', 'Prepare'), ('Execute', 'Execute'), ('Avoid', 'Avoid'), ('Monitor', 'Monitor'), ('Assess', 'Assess'), ('AllClear', 'AllClear'), ('None', 'None')], default=None, null=True),
        ),
        migrations.AlterField(
            model_name='alertinfo',
            name='sender_name',
            field=models.CharField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='alertinfo',
            name='web',
            field=models.URLField(blank=True, default=None, null=True),
        ),
    ]
