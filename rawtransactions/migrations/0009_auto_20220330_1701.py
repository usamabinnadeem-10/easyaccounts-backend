# Generated by Django 3.2.12 on 2022-03-30 12:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('essentials', '0012_auto_20220319_2025'),
        ('authentication', '0004_alter_userbranchrelation_role'),
        ('ledgers', '0007_alter_ledger_raw_return'),
        ('rawtransactions', '0008_auto_20220330_1701'),
    ]

    operations = [
        migrations.DeleteModel(
            name='RawReturn',
        ),
        migrations.DeleteModel(
            name='RawReturnLot',
        ),
        migrations.DeleteModel(
            name='RawReturnLotDetail',
        ),
        migrations.AddField(
            model_name='rawdebitlotdetail',
            name='branch',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rawdebitlotdetail', to='authentication.branch'),
        ),
        migrations.AddField(
            model_name='rawdebitlotdetail',
            name='formula',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='rawtransactions.formula'),
        ),
        migrations.AddField(
            model_name='rawdebitlotdetail',
            name='return_lot',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='rawtransactions.rawdebitlot'),
        ),
        migrations.AddField(
            model_name='rawdebitlotdetail',
            name='warehouse',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='essentials.warehouse'),
        ),
        migrations.AddField(
            model_name='rawdebitlot',
            name='bill_number',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='rawtransactions.rawdebit'),
        ),
        migrations.AddField(
            model_name='rawdebitlot',
            name='branch',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rawdebitlot', to='authentication.branch'),
        ),
        migrations.AddField(
            model_name='rawdebitlot',
            name='lot_number',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='rawtransactions.rawtransactionlot'),
        ),
        migrations.AddField(
            model_name='rawdebit',
            name='branch',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rawdebit', to='authentication.branch'),
        ),
        migrations.AddField(
            model_name='rawdebit',
            name='person',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='essentials.person'),
        ),
        migrations.AlterUniqueTogether(
            name='rawdebit',
            unique_together={('manual_invoice_serial', 'bill_number', 'branch', 'debit_type')},
        ),
    ]
