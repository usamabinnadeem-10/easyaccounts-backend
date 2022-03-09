# Generated by Django 3.2.12 on 2022-03-09 15:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0001_initial'),
        ('essentials', '0007_auto_20220308_2254'),
    ]

    operations = [
        migrations.AddField(
            model_name='accounttype',
            name='branch',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='accounttype', to='authentication.branch'),
        ),
        migrations.AddField(
            model_name='area',
            name='branch',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='area', to='authentication.branch'),
        ),
        migrations.AddField(
            model_name='linkedaccount',
            name='branch',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='linkedaccount', to='authentication.branch'),
        ),
        migrations.AddField(
            model_name='person',
            name='branch',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='person', to='authentication.branch'),
        ),
        migrations.AddField(
            model_name='product',
            name='branch',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='product', to='authentication.branch'),
        ),
        migrations.AddField(
            model_name='stock',
            name='branch',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='stock', to='authentication.branch'),
        ),
        migrations.AddField(
            model_name='warehouse',
            name='branch',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='warehouse', to='authentication.branch'),
        ),
    ]