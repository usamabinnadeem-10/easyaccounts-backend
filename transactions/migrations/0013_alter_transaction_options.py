# Generated by Django 3.2.11 on 2022-02-01 10:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0012_auto_20220123_1908'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='transaction',
            options={'ordering': ['-date', '-serial']},
        ),
    ]
