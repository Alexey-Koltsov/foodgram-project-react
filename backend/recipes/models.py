from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from api.constants import SYMBOLS_QUANTITY

User = get_user_model()


class Tag(models.Model):
    """Модель тегов"""

    name = models.CharField(
        max_length=settings.MAX_LEN_NAME,
        verbose_name='Название',
        unique=True,
    )
    color = models.CharField(
        max_length=settings.MAX_LEN_COLOR,
        verbose_name='Цвет в НЕХ',
        unique=True,
    )
    slug = models.SlugField(
        max_length=settings.MAX_LEN_SLUG,
        unique=True,
        verbose_name='Уникальный слаг',
        validators=[RegexValidator(
            r'^[-a-zA-Z0-9_]+$', 'Недопустимый символ.'
        )],
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name[:SYMBOLS_QUANTITY]


class Ingredient(models.Model):
    """Модель ингредиентов"""

    name = models.CharField(
        max_length=settings.MAX_LEN_NAME,
        verbose_name='Название',
    )
    measurement_unit = models.CharField(
        max_length=settings.MAX_LEN_NAME,
        verbose_name='Единица измерения',
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    """Модель рецептов"""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes_author',
        verbose_name='Автор',
    )
    name = models.CharField(
        max_length=settings.MAX_LEN_NAME,
        verbose_name='Название рецепта',
    )
    text = models.TextField(verbose_name='Текст')
    image = models.ImageField(
        upload_to='recipes/images/',
        null=True,
        default=None,
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(
        Tag,
        through='RecipeTag',
        verbose_name='Тэги',
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=(
            MinValueValidator(1, message='Минимальное значение: 1'),
        ),
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
    )

    class Meta:
        ordering = ('-pub_date', )
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name[:SYMBOLS_QUANTITY]


class RecipeIngredient(models.Model):
    """Модель связи рецептов и ингредиентов"""

    ingredient = models.ForeignKey(
        Ingredient,
        related_name='recipeingredient',
        verbose_name='Ингредиент',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='recipeingredient',
        verbose_name='Рецепт',
        on_delete=models.CASCADE
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['ingredient', 'recipe'],
                name='unique-in-recipeingredient'
            ),
        ]

    def __str__(self):
        return (f'{self.ingredient.name[:SYMBOLS_QUANTITY]} входит в'
                f'состав {self.recipe.name[:SYMBOLS_QUANTITY]}')


class RecipeTag(models.Model):
    """Модель связи рецептов и тэгов"""

    tag = models.ForeignKey(
        Tag,
        related_name='recipetag',
        verbose_name='Тэг',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='recipetag',
        verbose_name='Рецепт',
        on_delete=models.CASCADE
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['tag', 'recipe'],
                name='unique-in-recipetag'
            ),
        ]

    def __str__(self):
        return (f'{self.recipe.name[:SYMBOLS_QUANTITY]} отмечен'
                f'тэгом {self.tag.name[:SYMBOLS_QUANTITY]}')


class Favorite(models.Model):
    """Модель избранного"""

    user = models.ForeignKey(
        User,
        related_name='favorite',
        verbose_name='Пользователь',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='favorite',
        verbose_name='Рецепт',
        on_delete=models.CASCADE
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique-in-favorite'
            ),
        ]

    def __str__(self):
        return (f'{self.user.username[:SYMBOLS_QUANTITY]} добавил в'
                f'избранное {self.recipe.name[:SYMBOLS_QUANTITY]}')


class ShoppingCart(models.Model):
    """Модель корзины покупок"""

    user = models.ForeignKey(
        User,
        related_name='shoppingcart',
        verbose_name='Пользователь',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='shoppingcart',
        verbose_name='Рецепт',
        on_delete=models.CASCADE
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique-in-shoppingcart'
            ),
        ]

    def __str__(self):
        return (f'{self.user.username[:SYMBOLS_QUANTITY]} добавил в'
                f'корзину {self.recipe.name[:SYMBOLS_QUANTITY]}')
