# Generated by Django 3.2.12 on 2022-06-12 16:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0004_auto_20220612_0728'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paymentandimage',
            name='image',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payment_image', to='payments.paymentimage'),
        ),
    ]
