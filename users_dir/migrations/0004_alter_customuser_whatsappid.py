# Generated by Django 4.2.2 on 2023-06-22 23:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users_dir', '0003_alter_customuser_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='whatsAppId',
            field=models.CharField(max_length=254, null=True, verbose_name='whatsAppId'),
        ),
    ]
