# Generated by Django 3.2.13 on 2023-05-27 01:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0007_alter_userbranchrelation_role'),
        ('rawtransactions', '0021_auto_20230524_0232'),
    ]

    operations = [
        migrations.AddField(
            model_name='rawtransaction',
            name='branch',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='authentication.branch'),
        ),
        migrations.AlterField(
            model_name='rawtransactionlot',
            name='raw_transaction',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='rawtransactions.rawtransaction'),
        ),
    ]
