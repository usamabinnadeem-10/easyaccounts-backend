# Generated by Django 3.2.12 on 2022-03-09 15:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='branch',
            options={'verbose_name': 'Branch', 'verbose_name_plural': 'Branches'},
        ),
    ]
