# Generated by Django 3.2.12 on 2022-06-22 23:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0023_auto_20220620_1621'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='manual_serial',
            field=models.BigIntegerField(null=True),
        ),
    ]