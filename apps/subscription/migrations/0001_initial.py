# Generated by Django 5.0.3 on 2024-03-11 12:14

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('subscription_name', models.CharField(default='', max_length=512, verbose_name='subscription_name')),
                ('user_id', models.IntegerField(default=0, verbose_name='user_id')),
                ('country_ids', django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(verbose_name='country_ids'), default=list, size=None)),
                ('admin1_ids', django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(verbose_name='admin1_ids'), default=list, size=None)),
                ('urgency_array', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(verbose_name='urgency_array'), default=list, size=None)),
                ('severity_array', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(verbose_name='severity_array'), default=list, size=None)),
                ('certainty_array', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(verbose_name='certainty_array'), default=list, size=None)),
                ('subscribe_by', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(verbose_name='subscribe_by'), default=list, size=None)),
                ('sent_flag', models.IntegerField(default=0, verbose_name='sent_flag')),
            ],
        ),
    ]