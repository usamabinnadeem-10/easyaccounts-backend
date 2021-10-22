# Generated by Django 3.2.8 on 2021-10-22 12:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ledgers', '0002_remove_ledger_transaction'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ledgerandaccounttype',
            name='ledger',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='ledgers.ledger'),
        ),
        migrations.AlterField(
            model_name='transactionandledger',
            name='ledger',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='ledgers.ledger'),
        ),
    ]
