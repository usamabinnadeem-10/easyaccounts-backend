# Generated by Django 3.2.11 on 2022-01-23 14:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ledgers', '0008_alter_ledger_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ledger',
            options={'ordering': ['date']},
        ),
    ]