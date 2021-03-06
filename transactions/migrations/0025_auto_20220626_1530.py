# Generated by Django 3.2.12 on 2022-06-26 15:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('essentials', '0022_remove_product_minimum_rate'),
        ('transactions', '0024_transaction_manual_serial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='account_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='essentials.accounttype'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='builty',
            field=models.CharField(blank=True, default=None, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='manual_serial',
            field=models.BigIntegerField(blank=True, null=True),
        ),
    ]
