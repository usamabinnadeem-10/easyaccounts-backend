# Generated by Django 3.2.12 on 2022-03-30 09:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rawtransactions', '0007_rename_bill_num_rawreturn_bill_number'),
        ('ledgers', '0005_ledger_raw_transaction'),
    ]

    operations = [
        migrations.AddField(
            model_name='ledger',
            name='raw_return',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='rawtransactions.rawreturn'),
        ),
    ]
