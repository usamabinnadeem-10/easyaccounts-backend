# Generated by Django 3.2.12 on 2022-03-09 15:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0002_alter_branch_options'),
        ('expenses', '0003_auto_20220309_2053'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expenseaccount',
            name='branch',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='expenseaccount', to='authentication.branch'),
        ),
        migrations.AlterField(
            model_name='expensedetail',
            name='branch',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='expensedetail', to='authentication.branch'),
        ),
    ]
