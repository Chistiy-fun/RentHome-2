"""
House models — based on the existing RentHome/Tag/Gallery structure,
extended with new fields required by the spec.
"""

from django.db import models


class Tag(models.Model):
    """Amenity/convenience tag for a house (e.g. WiFi, Pool)."""

    title = models.CharField(max_length=50, verbose_name='Название удобства')
    date_created = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    def __str__(self) -> str:
        return self.title

    class Meta:
        verbose_name = 'Удобство'
        verbose_name_plural = 'Удобства'


class House(models.Model):
    """
    Rental house listing.
    Preserves original RentHome fields and adds new required ones.
    """

    title = models.CharField(max_length=100, verbose_name='Название дома')
    description = models.TextField(max_length=2000, verbose_name='Описание')
    price_per_day = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name='Цена за сутки'
    )
    price_per_month = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name='Цена за месяц'
    )
    address = models.CharField(max_length=255, verbose_name='Адрес')
    tags = models.ManyToManyField(Tag, blank=True, verbose_name='Удобства')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    date_created = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    def __str__(self) -> str:
        return self.title

    def get_tags(self) -> str:
        return ', '.join(t.title for t in self.tags.all())

    def get_photos(self) -> list:
        return [p.image.url for p in self.photos.all()]

    class Meta:
        verbose_name = 'Дом для аренды'
        verbose_name_plural = 'Дома для аренды'


class HousePhoto(models.Model):
    """Multiple photos per house (replaces old Gallery model)."""

    house = models.ForeignKey(
        House, on_delete=models.CASCADE,
        related_name='photos', verbose_name='Дом'
    )
    image = models.ImageField(upload_to='houses/', verbose_name='Фото')

    def __str__(self) -> str:
        return f'Фото к {self.house.title}'

    class Meta:
        verbose_name = 'Фото дома'
        verbose_name_plural = 'Фото домов'


class Service(models.Model):
    """Additional service tied to a specific house."""

    house = models.ForeignKey(
        House, on_delete=models.CASCADE,
        related_name='services', verbose_name='Дом'
    )
    name = models.CharField(max_length=100, verbose_name='Название услуги')
    description = models.TextField(blank=True, verbose_name='Описание')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    is_daily = models.BooleanField(
        default=False,
        verbose_name='Посуточная',
        help_text='Если True — цена умножается на кол-во дней'
    )

    def __str__(self) -> str:
        return f'{self.name} ({self.house.title})'

    class Meta:
        verbose_name = 'Услуга'
        verbose_name_plural = 'Услуги'
