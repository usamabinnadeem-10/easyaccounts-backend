# Generated by Django 3.2.8 on 2021-11-01 14:41

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('expenses', '0002_alter_expensedetail_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expensedetail',
            name='date',
            field=models.DateField(default=datetime.date.today),
        ),
    ]
