# Generated by Django 3.2.11 on 2022-02-18 13:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cheques', '0006_auto_20220218_1833'),
        ('ledgers', '0011_alter_ledger_cheque'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ledger',
            name='cheque',
        ),
        migrations.AddField(
            model_name='ledger',
            name='external_cheque',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='cheques.externalcheque'),
        ),
    ]