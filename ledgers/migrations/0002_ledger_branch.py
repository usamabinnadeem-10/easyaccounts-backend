# Generated by Django 3.2.12 on 2022-03-09 15:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0001_initial'),
        ('ledgers', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='ledger',
            name='branch',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='ledger', to='authentication.branch'),
        ),
    ]
