# Generated by Django 3.2.12 on 2022-06-02 07:46

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cheques', '0009_auto_20220602_1244'),
    ]

    operations = [
        migrations.AddField(
            model_name='externalcheque',
            name='time_stamp',
            field=models.DateTimeField(default=datetime.datetime.now),
        ),
        migrations.AddField(
            model_name='personalcheque',
            name='time_stamp',
            field=models.DateTimeField(default=datetime.datetime.now),
        ),
    ]
