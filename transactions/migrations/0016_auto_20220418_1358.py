# Generated by Django 3.2.12 on 2022-04-18 08:58

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0015_auto_20220417_1814'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='transaction',
            name='draft',
        ),
        migrations.RemoveField(
            model_name='transactiondetail',
            name='amount',
        ),
        migrations.AddField(
            model_name='transaction',
            name='builty',
            field=models.CharField(default=None, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='transactiondetail',
            name='quantity',
            field=models.FloatField(validators=[django.core.validators.MinValueValidator(0.0001)]),
        ),
        migrations.AlterField(
            model_name='transactiondetail',
            name='yards_per_piece',
            field=models.FloatField(validators=[django.core.validators.MinValueValidator(0.01)]),
        ),
    ]