# Generated by Django 3.2.13 on 2023-09-02 21:19

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0008_userbranchrelation_permissions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userbranchrelation',
            name='permissions',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=100), blank=True, default=list, size=None),
        ),
    ]
