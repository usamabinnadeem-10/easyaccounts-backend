# Generated by Django 3.2.12 on 2022-03-30 12:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0004_alter_userbranchrelation_role'),
        ('rawtransactions', '0009_auto_20220330_1701'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='rawdebit',
            unique_together={('manual_invoice_serial', 'branch', 'debit_type')},
        ),
    ]
