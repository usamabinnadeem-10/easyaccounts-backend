# Generated by Django 3.2.12 on 2022-07-08 19:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('essentials', '0027_auto_20220708_0506'),
    ]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='person_type',
            field=models.CharField(choices=[('S', 'Supplier'), ('C', 'Customer'), ('E', 'Equity'), ('EXA', 'Advance Expense')], max_length=3),
        ),
    ]