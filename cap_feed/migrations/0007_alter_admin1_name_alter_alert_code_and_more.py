# Generated by Django 4.2.3 on 2023-08-25 19:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cap_feed', '0006_expiredalert'),
    ]

    operations = [
        migrations.AlterField(
            model_name='admin1',
            name='name',
            field=models.CharField(),
        ),
        migrations.AlterField(
            model_name='alert',
            name='code',
            field=models.CharField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='alert',
            name='identifier',
            field=models.CharField(),
        ),
        migrations.AlterField(
            model_name='alert',
            name='restriction',
            field=models.CharField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='alert',
            name='sender',
            field=models.CharField(),
        ),
        migrations.AlterField(
            model_name='alert',
            name='source',
            field=models.CharField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='alert',
            name='url',
            field=models.CharField(unique=True),
        ),
        migrations.AlterField(
            model_name='alertinfo',
            name='contact',
            field=models.CharField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='alertinfo',
            name='event',
            field=models.CharField(),
        ),
        migrations.AlterField(
            model_name='alertinfo',
            name='event_code',
            field=models.CharField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='alertinfo',
            name='headline',
            field=models.CharField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='alertinfo',
            name='language',
            field=models.CharField(blank=True, default='en-US'),
        ),
        migrations.AlterField(
            model_name='alertinfo',
            name='parameter',
            field=models.CharField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='alertinfo',
            name='sender_name',
            field=models.CharField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='alertinfoareageocode',
            name='value',
            field=models.CharField(),
        ),
        migrations.AlterField(
            model_name='alertinfoareageocode',
            name='value_name',
            field=models.CharField(),
        ),
        migrations.AlterField(
            model_name='alertinfoparameter',
            name='value_name',
            field=models.CharField(),
        ),
        migrations.AlterField(
            model_name='continent',
            name='name',
            field=models.CharField(),
        ),
        migrations.AlterField(
            model_name='country',
            name='centroid',
            field=models.CharField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='country',
            name='name',
            field=models.CharField(),
        ),
        migrations.AlterField(
            model_name='expiredalert',
            name='url',
            field=models.CharField(unique=True),
        ),
        migrations.AlterField(
            model_name='feed',
            name='url',
            field=models.CharField(unique=True),
        ),
        migrations.AlterField(
            model_name='feedlog',
            name='alert_url',
            field=models.CharField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='feedlog',
            name='exception',
            field=models.CharField(default='exception'),
        ),
        migrations.AlterField(
            model_name='languageinfo',
            name='logo',
            field=models.CharField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='languageinfo',
            name='name',
            field=models.CharField(),
        ),
        migrations.AlterField(
            model_name='region',
            name='centroid',
            field=models.CharField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='region',
            name='name',
            field=models.CharField(),
        ),
    ]
