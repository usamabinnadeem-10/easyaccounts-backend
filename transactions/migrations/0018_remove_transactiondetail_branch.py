# Generated by Django 3.2.12 on 2022-05-30 11:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0017_auto_20220421_0208'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='transactiondetail',
            name='branch',
        ),
    ]
