# Generated by Django 3.2.12 on 2022-03-30 21:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rawtransactions', '0010_alter_rawdebit_unique_together'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rawlotdetail',
            name='lot_number',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='raw_lot_detail', to='rawtransactions.rawtransactionlot'),
        ),
        migrations.AlterField(
            model_name='rawtransactionlot',
            name='raw_transaction',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transaction_lot', to='rawtransactions.rawtransaction'),
        ),
    ]