# Generated by Django 3.2.12 on 2022-06-07 19:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='serial',
            field=models.PositiveBigIntegerField(default=1),
            preserve_default=False,
        ),
    ]
