# Generated by Django 3.2.12 on 2022-04-08 16:25

import datetime
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import rawtransactions.models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0004_alter_userbranchrelation_role'),
        ('essentials', '0016_product_minimum_rate'),
        ('transactions', '0011_alter_transactiondetail_product'),
    ]

    operations = [
        migrations.CreateModel(
            name='StockTransfer',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('date', models.DateField(default=datetime.date.today)),
                ('serial', models.PositiveBigIntegerField()),
                ('branch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stocktransfer', to='authentication.branch')),
            ],
            options={
                'verbose_name_plural': 'Transfer entries',
            },
            bases=(models.Model, rawtransactions.models.NextSerial),
        ),
        migrations.CreateModel(
            name='StockTransferDetail',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('yards_per_piece', models.FloatField(validators=[django.core.validators.MinValueValidator(0.0)])),
                ('quantity', models.FloatField(validators=[django.core.validators.MinValueValidator(0.0)])),
                ('branch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stocktransferdetail', to='authentication.branch')),
                ('from_warehouse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='from_warehouse', to='essentials.warehouse')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='essentials.product')),
                ('to_warehouse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='to_warehouse', to='essentials.warehouse')),
                ('transfer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='transactions.stocktransfer')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.DeleteModel(
            name='TransferEntry',
        ),
    ]
