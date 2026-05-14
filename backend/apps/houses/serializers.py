from rest_framework import serializers
from .models import House, HousePhoto, Service, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'title']


class HousePhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = HousePhoto
        fields = ['id', 'image']


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'house', 'name', 'description', 'price', 'is_daily']


class HouseListSerializer(serializers.ModelSerializer):
    """Compact serializer for list view."""
    tags = TagSerializer(many=True, read_only=True)
    first_photo = serializers.SerializerMethodField()

    class Meta:
        model = House
        fields = ['id', 'title', 'price_per_day', 'price_per_month',
                  'address', 'tags', 'first_photo', 'is_active']

    def get_first_photo(self, obj: House):
        photo = obj.photos.first()
        if photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(photo.image.url)
            return photo.image.url
        return None


class HouseDetailSerializer(serializers.ModelSerializer):
    """Full house card with all photos and services."""
    tags = TagSerializer(many=True, read_only=True)
    photos = HousePhotoSerializer(many=True, read_only=True)
    services = ServiceSerializer(many=True, read_only=True)

    class Meta:
        model = House
        fields = ['id', 'title', 'description', 'price_per_day', 'price_per_month',
                  'address', 'tags', 'photos', 'services', 'is_active', 'date_created']
