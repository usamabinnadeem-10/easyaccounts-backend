# Generated by Django 3.2.12 on 2022-03-06 14:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='transaction',
            options={'ordering': ['serial']},
        ),
    ]
