# Generated by Django 3.2.11 on 2022-02-01 10:59

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('essentials', '0008_merge_20220123_1907'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='address',
            field=models.CharField(max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='person',
            name='city',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='person',
            name='phone_number',
            field=models.CharField(default=923120798798, max_length=13, validators=[django.core.validators.MinLengthValidator(13, 'Phone number not complete'), django.core.validators.RegexValidator(code='nomatch', message='Phone number not complete', regex='/^\\+[0-9]{12}$/')]),
            preserve_default=False,
        ),
    ]
