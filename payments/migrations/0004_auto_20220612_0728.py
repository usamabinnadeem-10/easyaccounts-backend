# Generated by Django 3.2.12 on 2022-06-12 07:28

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('essentials', '0021_auto_20220602_2203'),
        ('payments', '0003_payment_account_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='paymentimage',
            name='payment',
        ),
        migrations.AlterField(
            model_name='payment',
            name='account_type',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.PROTECT, to='essentials.accounttype'),
        ),
        migrations.CreateModel(
            name='PaymentAndImage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('image', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='payments.paymentimage')),
                ('payment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='payments.payment')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
