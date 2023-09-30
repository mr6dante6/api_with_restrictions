from django.conf import settings
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.response import Response


class AdvertisementStatusChoices(models.TextChoices):
    """Статусы объявления."""

    OPEN = "OPEN", "Открыто"
    CLOSED = "CLOSED", "Закрыто"
    DRAFT = "DRAFT", "Черновик"


class Advertisement(models.Model):
    """Объявление."""

    title = models.TextField()
    description = models.TextField(default='')
    status = models.CharField(
        max_length=6,
        choices=AdvertisementStatusChoices.choices,
        default=AdvertisementStatusChoices.OPEN
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )

    favorites = models.ManyToManyField('FavoriteAdvertisement', related_name='favorited_by', blank=True)

    def set_draft(self):
        self.status = AdvertisementStatusChoices.DRAFT
        self.save()

    def set_open(self):
        self.status = AdvertisementStatusChoices.OPEN
        self.save()


class FavoriteAdvertisement(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    advertisement = models.ForeignKey(Advertisement, on_delete=models.CASCADE)


class UserSerializer(serializers.ModelSerializer):
    """Serializer для пользователя."""

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name',)


class AdvertisementSerializer(serializers.ModelSerializer):
    """Serializer для объявления."""

    creator = UserSerializer(
        read_only=True,
    )

    class Meta:
        model = Advertisement
        fields = ('id', 'title', 'description', 'creator', 'status', 'created_at',)

    def create(self, validated_data):
        """Метод для создания."""
        validated_data["creator"] = self.context["request"].user
        return super().create(validated_data)

    def validate(self, data):
        """Метод для валидации. Вызывается при создании и обновлении."""
        user = self.context["request"].user
        if data.get("status") == AdvertisementStatusChoices.DRAFT:
            # Пользователь может создавать объявления в статусе "DRAFT"
            # Остальные пользователи не видят эти объявления
            return data
        if user and user.is_authenticated:
            # Проверяем, что пользователь не создает более 10 открытых объявлений
            open_advertisements_count = Advertisement.objects.filter(
                creator=user, status=AdvertisementStatusChoices.OPEN
            ).count()
            if open_advertisements_count >= 10:
                raise serializers.ValidationError("Превышено количество открытых объявлений.")
        return data


class FavoriteAdvertisementSerializer(serializers.ModelSerializer):
    """Serializer для избранных объявлений."""

    class Meta:
        model = FavoriteAdvertisement
        fields = ('user', 'advertisement',)
