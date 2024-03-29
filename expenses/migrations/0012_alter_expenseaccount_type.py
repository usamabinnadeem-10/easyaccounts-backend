# Generated by Django 3.2.12 on 2022-07-26 18:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('expenses', '0011_alter_expenseaccount_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expenseaccount',
            name='type',
            field=models.CharField(choices=[('rent', 'Rent'), ('electricity', 'Electricity'), ('maintenance', 'Maintenance'), ('salary', 'Salary'), ('transportation', 'Transportation'), ('administrative', 'Administrative'), ('marketing', 'Marketing'), ('refreshments', 'Refreshments'), ('food', 'Food'), ('special', 'Special'), ('commission', 'Commission'), ('printing', 'Printing'), ('legal', 'Legal'), ('communication', 'Communication'), ('taxation', 'Taxation'), ('software', 'Software'), ('other', 'Other'), ('nagh_mazdoori', 'Nagh Mazdoori'), ('construction', 'Construction')], default='other', max_length=14),
        ),
    ]
