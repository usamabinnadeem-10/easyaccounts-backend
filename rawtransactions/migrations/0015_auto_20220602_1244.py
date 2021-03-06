# Generated by Django 3.2.12 on 2022-06-02 07:44

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rawtransactions', '0014_auto_20220415_2322'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='rawdebitlot',
            name='branch',
        ),
        migrations.RemoveField(
            model_name='rawdebitlotdetail',
            name='branch',
        ),
        migrations.RemoveField(
            model_name='rawlotdetail',
            name='branch',
        ),
        migrations.RemoveField(
            model_name='rawtransactionlot',
            name='branch',
        ),
        migrations.AlterField(
            model_name='rawdebitlotdetail',
            name='quantity',
            field=models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1e-05)]),
        ),
        migrations.AlterField(
            model_name='rawlotdetail',
            name='quantity',
            field=models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1e-05)]),
        ),
    ]
