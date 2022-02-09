# Generated by Django 3.2.11 on 2022-02-09 13:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cheques', '0003_auto_20220209_1858'),
        ('ledgers', '0009_alter_ledger_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='ledger',
            name='cheque',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='cheques.cheque'),
        ),
    ]
