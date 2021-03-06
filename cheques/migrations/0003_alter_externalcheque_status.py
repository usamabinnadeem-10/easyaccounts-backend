# Generated by Django 3.2.12 on 2022-03-06 19:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cheques', '0002_auto_20220305_1709'),
    ]

    operations = [
        migrations.AlterField(
            model_name='externalcheque',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('transferred', 'Transferred'), ('cleared', 'Cleared'), ('returned', 'Returned'), ('complete_history', 'Complete History')], default='pending', max_length=20),
        ),
    ]
