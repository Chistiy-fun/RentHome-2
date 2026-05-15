import apps.users.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='TelegramUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('telegram_id', models.BigIntegerField(unique=True, verbose_name='Telegram ID')),
                ('username', models.CharField(blank=True, max_length=64, verbose_name='Username')),
                ('full_name', models.CharField(max_length=128, verbose_name='Полное имя')),
                ('phone', models.CharField(blank=True, max_length=20, verbose_name='Телефон')),
                ('total_spent', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Всего потрачено')),
                ('total_bookings', models.PositiveIntegerField(default=0, verbose_name='Всего бронирований')),
                ('discount_balance', models.DecimalField(decimal_places=2, default=0, max_digits=5, verbose_name='Накопительная скидка (%)')),
                ('referral_code', models.CharField(default=apps.users.models.generate_referral_code, max_length=16, unique=True, verbose_name='Реферальный код')),
                ('new_user_discount_used', models.BooleanField(default=False, verbose_name='Использовал стартовую скидку')),
                ('auth_token', models.CharField(blank=True, max_length=64, verbose_name='API токен')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('referred_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='referrals', to='users.telegramuser', verbose_name='Приглашён пользователем')),
            ],
            options={
                'verbose_name': 'Пользователь',
                'verbose_name_plural': 'Пользователи',
            },
        ),
    ]
