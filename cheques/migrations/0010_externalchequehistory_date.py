# Generated by Django 3.2.11 on 2022-02-21 14:00

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cheques', '0009_alter_externalchequetransfer_cheque'),
    ]

    operations = [
        migrations.AddField(
            model_name='externalchequehistory',
            name='date',
            field=models.DateField(default=datetime.date.today),
        ),
    ]
