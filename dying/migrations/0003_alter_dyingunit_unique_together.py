# Generated by Django 3.2.12 on 2022-03-27 11:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0004_alter_userbranchrelation_role'),
        ('dying', '0002_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='dyingunit',
            unique_together={('name', 'branch')},
        ),
    ]