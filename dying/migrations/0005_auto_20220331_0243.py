# Generated by Django 3.2.12 on 2022-03-30 21:43

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('rawtransactions', '0011_auto_20220331_0211'),
        ('authentication', '0004_alter_userbranchrelation_role'),
        ('dying', '0004_auto_20220331_0211'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dyingissue',
            name='lot_number',
        ),
        migrations.CreateModel(
            name='DyingIssueLot',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('branch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dyingissuelot', to='authentication.branch')),
                ('dying_lot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dying_issue_lot', to='dying.dyingissue')),
                ('lot_number', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='rawtransactions.rawtransactionlot')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterField(
            model_name='dyingissuedetail',
            name='dying_lot_number',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dying_issue_lot_number', to='dying.dyingissuelot'),
        ),
    ]
