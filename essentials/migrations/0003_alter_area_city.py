# Generated by Django 3.2.12 on 2022-03-05 12:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('essentials', '0002_alter_person_city'),
    ]

    operations = [
        migrations.AlterField(
            model_name='area',
            name='city',
            field=models.IntegerField(),
        ),
    ]
