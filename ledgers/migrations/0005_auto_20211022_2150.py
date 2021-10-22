# Generated by Django 3.2.8 on 2021-10-22 21:50

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('essentials', '0001_initial'),
        ('ledgers', '0004_auto_20211022_1332'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ledger',
            name='date',
            field=models.DateField(default=datetime.date.today),
        ),
        migrations.AlterField(
            model_name='ledger',
            name='person',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='essentials.person'),
        ),
    ]
