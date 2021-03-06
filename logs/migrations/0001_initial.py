# Generated by Django 3.2.12 on 2022-04-20 13:03

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('authentication', '0004_alter_userbranchrelation_role'),
    ]

    operations = [
        migrations.CreateModel(
            name='Log',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('time_stamp', models.DateTimeField(default=datetime.datetime.now)),
                ('type', models.CharField(choices=[('C', 'Created'), ('E', 'Edited'), ('D', 'Deleted')], max_length=1)),
                ('category', models.CharField(choices=[('transaction', 'Transaction'), ('cancelled_transaction', 'Cancelled Transaction'), ('expense', 'Expense'), ('ledger_entry', 'Ledger entry'), ('external_cheque', 'External cheque'), ('external_cheque_history', 'External cheque history'), ('personal_cheque', 'External cheque'), ('personal_cheque_history', 'Personal cheque history'), ('essentials', 'Essentials'), ('stock_transfer', 'Stock transfer'), ('cancelled_stock_transfer', 'Cancelled stock transfer')], max_length=32)),
                ('detail', models.CharField(max_length=128)),
                ('branch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='log', to='authentication.branch')),
                ('user', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='log', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
