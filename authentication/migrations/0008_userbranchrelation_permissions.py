# Generated by Django 3.2.13 on 2023-08-13 14:05

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0007_alter_userbranchrelation_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='userbranchrelation',
            name='permissions',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=100), default=list, size=None),
        ),
    ]
