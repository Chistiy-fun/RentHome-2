from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PromoCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=32, unique=True, verbose_name='Код')),
                ('discount_type', models.CharField(choices=[('percent', 'Процент'), ('fixed', 'Фиксированная сумма')], max_length=10, verbose_name='Тип скидки')),
                ('value', models.DecimalField(decimal_places=2, max_digits=8, verbose_name='Значение скидки')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активен')),
                ('usage_limit', models.PositiveIntegerField(blank=True, null=True, verbose_name='Лимит использований')),
                ('used_count', models.PositiveIntegerField(default=0, verbose_name='Использован раз')),
                ('valid_from', models.DateTimeField(blank=True, null=True, verbose_name='Действует с')),
                ('valid_to', models.DateTimeField(blank=True, null=True, verbose_name='Действует до')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Промокод',
                'verbose_name_plural': 'Промокоды',
            },
        ),
    ]
