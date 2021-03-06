# Generated by Django 3.2.12 on 2022-04-15 16:37

import datetime
import uuid

import django.core.validators
import django.db.models.deletion
import rawtransactions.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0004_alter_userbranchrelation_role"),
        ("essentials", "0017_alter_person_unique_together"),
        ("transactions", "0011_alter_transactiondetail_product"),
    ]

    operations = [
        migrations.CreateModel(
            name="StockTransfer",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("date", models.DateField(default=datetime.date.today)),
                ("serial", models.PositiveBigIntegerField()),
                ("manual_invoice_serial", models.PositiveBigIntegerField()),
                (
                    "branch",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="stocktransfer",
                        to="authentication.branch",
                    ),
                ),
                (
                    "from_warehouse",
                    models.ForeignKey(
                        default=None,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="from_warehouse",
                        to="essentials.warehouse",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Stock transfers",
            },
            bases=(models.Model, rawtransactions.models.NextSerial),
        ),
        migrations.CreateModel(
            name="StockTransferDetail",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "yards_per_piece",
                    models.FloatField(
                        validators=[django.core.validators.MinValueValidator(0.0)]
                    ),
                ),
                (
                    "quantity",
                    models.FloatField(
                        validators=[django.core.validators.MinValueValidator(0.0)]
                    ),
                ),
                (
                    "branch",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="stocktransferdetail",
                        to="authentication.branch",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="essentials.product",
                    ),
                ),
                (
                    "to_warehouse",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="to_warehouse",
                        to="essentials.warehouse",
                    ),
                ),
                (
                    "transfer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="transfer_detail",
                        to="transactions.stocktransfer",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.AlterField(
            model_name="cancelledinvoice",
            name="manual_serial_type",
            field=models.CharField(
                choices=[
                    ("INV", "Sale Invoice"),
                    ("SUP", "Purchase"),
                    ("MWS", "Maal Wapsi Supplier"),
                    ("MWC", "Maal Wapsi Customer"),
                ],
                max_length=3,
            ),
        ),
        migrations.AlterField(
            model_name="transaction",
            name="manual_serial_type",
            field=models.CharField(
                choices=[
                    ("INV", "Sale Invoice"),
                    ("SUP", "Purchase"),
                    ("MWS", "Maal Wapsi Supplier"),
                    ("MWC", "Maal Wapsi Customer"),
                ],
                max_length=3,
            ),
        ),
    ]
