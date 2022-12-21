# Generated by Django 3.2.13 on 2022-12-21 23:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cheques', '0015_auto_20220808_2008'),
    ]

    operations = [
        migrations.AlterField(
            model_name='externalcheque',
            name='bank',
            field=models.CharField(choices=[('meezan', 'Meezan Bank'), ('al_baraka', 'Al Baraka Bank'), ('habib_metro', 'Habib Metropolitan Bank'), ('askari', 'Askari Bank'), ('allied', 'Allied Bank'), ('alfalah', 'Bank Alfalah'), ('al_habib', 'Bank Al-Habib'), ('dubai_islami', 'Dubai Bank Islami'), ('citi', 'Citi Bank'), ('islami', 'Bank Islami'), ('faysal', 'Faysal Bank'), ('first_woman', 'First Women Bank'), ('hbl', 'Habib Bank Limited'), ('standard_chartered', 'Standard Chartered Bank'), ('js', 'JS Bank Limited'), ('mcb', 'MCB Bank Limited'), ('mcb_islamic', 'MCB Islamic Bank Limited'), ('national', 'National Bank of Pakistan'), ('ubl', 'UBL'), ('ubank', 'U Microfinance Bank'), ('soneri', 'Soneri Bank Limited')], max_length=20),
        ),
        migrations.AlterField(
            model_name='personalcheque',
            name='bank',
            field=models.CharField(choices=[('meezan', 'Meezan Bank'), ('al_baraka', 'Al Baraka Bank'), ('habib_metro', 'Habib Metropolitan Bank'), ('askari', 'Askari Bank'), ('allied', 'Allied Bank'), ('alfalah', 'Bank Alfalah'), ('al_habib', 'Bank Al-Habib'), ('dubai_islami', 'Dubai Bank Islami'), ('citi', 'Citi Bank'), ('islami', 'Bank Islami'), ('faysal', 'Faysal Bank'), ('first_woman', 'First Women Bank'), ('hbl', 'Habib Bank Limited'), ('standard_chartered', 'Standard Chartered Bank'), ('js', 'JS Bank Limited'), ('mcb', 'MCB Bank Limited'), ('mcb_islamic', 'MCB Islamic Bank Limited'), ('national', 'National Bank of Pakistan'), ('ubl', 'UBL'), ('ubank', 'U Microfinance Bank'), ('soneri', 'Soneri Bank Limited')], max_length=20),
        ),
    ]
