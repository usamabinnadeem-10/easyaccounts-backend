# Generated by Django 3.2.11 on 2022-02-05 12:13

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('essentials', '0009_auto_20220201_1559'),
    ]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='phone_number',
            field=models.CharField(max_length=13, unique=True, validators=[django.core.validators.RegexValidator(code='nomatch', message='Phone number should look like this (+923001234567)', regex='^\\+\\d{12}$')]),
        ),
    ]