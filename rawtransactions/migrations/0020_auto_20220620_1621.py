# Generated by Django 3.2.12 on 2022-06-20 16:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rawtransactions', '0019_auto_20220616_2017'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='rawtransaction',
            name='manual_invoice_serial',
        ),
        migrations.AlterUniqueTogether(
            name='rawdebit',
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name='rawdebit',
            name='manual_invoice_serial',
        ),
    ]