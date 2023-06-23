from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Alert',
            fields=[
                ('id', models.CharField(max_length=255, primary_key=True, serialize=False)),
                ('identifier', models.CharField(max_length=255)),
                ('sender', models.CharField(max_length=255)),
                ('sent', models.DateTimeField()),
                ('status', models.CharField(max_length=255)),
                ('msg_type', models.CharField(max_length=255)),
                ('scope', models.CharField(max_length=255)),
                ('urgency', models.CharField(max_length=255)),
                ('severity', models.CharField(max_length=255)),
                ('certainty', models.CharField(max_length=255)),
                ('expires', models.DateTimeField()),
                ('area_desc', models.CharField(max_length=255)),
                ('event', models.CharField(max_length=255)),
                ('geocode_name', models.CharField(blank=True, default='', max_length=255)),
                ('geocode_value', models.CharField(blank=True, default='', max_length=255)),
                ('polygon', models.TextField(blank=True, default='', max_length=16383)),
            ],
        ),
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.CharField(max_length=255, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('iso', models.CharField(blank=True, default='', max_length=255)),
                ('iso3', models.CharField(blank=True, default='', max_length=255)),
                ('polygon', models.TextField(blank=True, default='', max_length=16383)),
                ('centroid', models.CharField(blank=True, default='', max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.CharField(max_length=255, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('polygon', models.TextField(blank=True, default='', max_length=16383)),
                ('centroid', models.CharField(blank=True, default='', max_length=255)),
            ],
        ),
    ]
