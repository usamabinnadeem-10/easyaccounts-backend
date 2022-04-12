# Generated by Django 3.2.12 on 2022-04-10 13:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0012_auto_20220408_2125'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='stocktransfer',
            options={'verbose_name_plural': 'Stock transfers'},
        ),
        migrations.AlterField(
            model_name='stocktransferdetail',
            name='transfer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transfer_detail', to='transactions.stocktransfer'),
        ),
    ]
