# Generated by Django 3.2.12 on 2022-06-07 19:50

import datetime
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import payments.utils
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('essentials', '0021_auto_20220602_2203'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('date', models.DateTimeField(default=datetime.datetime.now)),
                ('time_stamp', models.DateTimeField(default=datetime.datetime.now)),
                ('amount', models.FloatField(validators=[django.core.validators.MinValueValidator(1.0)])),
                ('nature', models.CharField(choices=[('C', 'Credit'), ('D', 'Debit')], max_length=1)),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='essentials.person')),
                ('user', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='payment', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PaymentImage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('image', models.ImageField(upload_to=payments.utils.get_image_upload_path)),
                ('payment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='payments.payment')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
