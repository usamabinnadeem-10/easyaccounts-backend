# Generated by Django 3.2.12 on 2022-06-15 22:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ledgers', '0023_alter_ledgerandtransactionandpayment_transaction'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ledgerandtransactionandpayment',
            name='ledger_entry',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ledger_transaction_payment', to='ledgers.ledger'),
        ),
    ]
