# Generated by Django 4.2.2 on 2023-07-04 21:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user_dir', '0005_customuser_email_reset_token_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='email_reset_token',
        ),
        migrations.RemoveField(
            model_name='customuser',
            name='email_reset_token_expires_at',
        ),
        migrations.RemoveField(
            model_name='customuser',
            name='email_verification_token',
        ),
        migrations.RemoveField(
            model_name='customuser',
            name='email_verification_token_expires_at',
        ),
        migrations.RemoveField(
            model_name='customuser',
            name='verified',
        ),
    ]
