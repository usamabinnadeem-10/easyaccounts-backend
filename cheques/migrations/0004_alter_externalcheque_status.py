# Generated by Django 3.2.12 on 2022-03-08 16:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cheques', '0003_alter_externalcheque_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='externalcheque',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('transferred', 'Transferred'), ('cleared', 'Cleared'), ('returned', 'Returned'), ('completed_history', 'Completed History'), ('completed_transfer', 'Completed Transfer')], default='pending', max_length=20),
        ),
    ]