# Generated by Django 3.2.11 on 2022-02-09 16:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('essentials', '0011_linkedaccount'),
        ('cheques', '0003_auto_20220209_1858'),
    ]

    operations = [
        migrations.AddField(
            model_name='cheque',
            name='person',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='essentials.person'),
        ),
    ]
