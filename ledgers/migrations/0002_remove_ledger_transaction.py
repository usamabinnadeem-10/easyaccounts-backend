# Generated by Django 3.2.8 on 2021-10-21 16:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ledgers', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ledger',
            name='transaction',
        ),
    ]
