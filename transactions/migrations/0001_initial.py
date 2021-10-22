# Generated by Django 3.2.8 on 2021-10-21 15:15

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('essentials', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('date', models.DateField(auto_now_add=True)),
                ('nature', models.CharField(choices=[('C', 'Credit'), ('D', 'Debit')], max_length=1)),
                ('discount', models.FloatField(validators=[django.core.validators.MinValueValidator(0.0)])),
                ('draft', models.BooleanField(default=False)),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='essentials.person')),
            ],
        ),
        migrations.CreateModel(
            name='TransactionDetail',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('rate', models.FloatField(validators=[django.core.validators.MinValueValidator(0.0)])),
                ('quantity', models.FloatField(validators=[django.core.validators.MinValueValidator(1.0)])),
                ('amount', models.FloatField(validators=[django.core.validators.MinValueValidator(0.0)])),
                ('product', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='essentials.product')),
                ('transaction', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transaction_detail', to='transactions.transaction')),
                ('warehouse', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='essentials.warehouse')),
            ],
        ),
    ]
