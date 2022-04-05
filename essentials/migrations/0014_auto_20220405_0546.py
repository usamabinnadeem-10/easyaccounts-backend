# Generated by Django 3.2.12 on 2022-04-05 00:46

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0004_alter_userbranchrelation_role'),
        ('essentials', '0013_auto_20220405_0053'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductCategory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('branch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='productcategory', to='authentication.branch')),
            ],
            options={
                'verbose_name': 'Product Categories',
            },
        ),
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.PROTECT, to='essentials.productcategory'),
        ),
    ]
