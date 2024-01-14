from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from api.constants import SYMBOLS_QUANTITY


class User(AbstractUser):
    """Модель User (пользователь)"""

    ADMIN = 'admin'
    USER = 'user'

    ROLE_CHOICES = [
        (ADMIN, 'Администратор'),
        (USER, 'Пользователь'),
    ]
    username = models.CharField(
        max_length=settings.MAX_LEN_USERNAME,
        unique=True,
        verbose_name='Юзернэйм',
        validators=[RegexValidator(
            r'^[\w.@+-]+\z$', 'Недопустимый символ.'
        )],
    )
    firstname = models.CharField(
        max_length=settings.MAX_LEN_USERNAME,
        unique=True,
        verbose_name='Имя',
    )
    lastname = models.CharField(
        max_length=settings.MAX_LEN_USERNAME,
        unique=True,
        verbose_name='Фамилия',
    )
    email = models.EmailField(
        max_length=settings.MAX_LEN_EMAIL,
        unique=True,
        verbose_name='Адрес электронной почты'
    )
    is_subscribed = models.BooleanField(
        default=False,
        verbose_name='Подписан ли текущий пользователь на этого'
    )
    role = models.CharField(
        max_length=settings.MAX_LEN_ROLE,
        choices=ROLE_CHOICES,
        default=USER,
        verbose_name='Роль',
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username[:SYMBOLS_QUANTITY]

    @property
    def is_admin(self):
        return self.role == self.ADMIN


class Subscription(models.Model):
    user = models.ForeignKey(
        User, related_name='subscription_user', on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User, related_name='subscription_author', on_delete=models.CASCADE
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique-in-module'
            ),
            models.CheckConstraint(
                name='user_prevent_self_author',
                check=~models.Q(user=models.F('author')),
            ),
        ]

    def __str__(self):
        return (f'{self.user.username[:SYMBOLS_QUANTITY]} подписан на'
                f'{self.follow.author[:SYMBOLS_QUANTITY]}')
