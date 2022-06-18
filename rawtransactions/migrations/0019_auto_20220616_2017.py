# Generated by Django 3.2.12 on 2022-06-16 20:17

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rawtransactions', '0018_auto_20220616_2008'),
    ]

    operations = [
        migrations.AddField(
            model_name='rawdebit',
            name='time_stamp',
            field=models.DateTimeField(default=datetime.datetime.now),
        ),
        migrations.AlterField(
            model_name='rawdebit',
            name='date',
            field=models.DateTimeField(default=datetime.datetime.now),
        ),
    ]