# Generated by Django 3.2.12 on 2022-03-10 10:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0006_alter_transaction_unique_together'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='serial',
            field=models.BigIntegerField(),
        ),
    ]