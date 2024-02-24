from django.contrib import admin
from users.models import Subscription, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Настройка админзоны для модели пользователей."""

    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
    )
    search_fields = ('username',)
    list_filter = ('email', 'username',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Настройка админзоны для модели подписок."""

    list_display = (
        'user',
        'author'
    )
    search_fields = ('user__username',)
    list_filter = ('user__username',)
