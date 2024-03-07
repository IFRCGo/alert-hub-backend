# Generated by Django 4.2.3 on 2023-08-11 14:31

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscription_dir', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='subscription',
            name='district_ids',
        ),
        migrations.AddField(
            model_name='subscription',
            name='admin1_ids',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(verbose_name='admin1_ids'), default=list, size=None),
        ),
    ]
