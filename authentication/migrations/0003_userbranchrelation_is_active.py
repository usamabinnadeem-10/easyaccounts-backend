# Generated by Django 3.2.12 on 2022-03-10 19:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0002_alter_branch_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='userbranchrelation',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
