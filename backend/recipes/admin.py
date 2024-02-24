from django.contrib import admin
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Настройка админзоны для модели рецептов."""

    list_display = (
        'author',
        'name',
    )
    search_fields = ('name',)
    list_filter = ('author__username', 'name', 'tags__name',)
    readonly_fields = ('quantity_in_favorites',)

    def quantity_in_favorites(self, obj):
        return Favorite.objects.filter(recipe=obj).count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Настройка админзоны для модели тэгов."""

    list_display = (
        'name',
        'color',
        'slug',
    )
    search_fields = ('name',)
    list_filter = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Настройка админзоны для модели ингредиентов."""

    list_display = (
        'name',
        'measurement_unit',
    )
    search_fields = ('name',)
    list_filter = ('name',)


@admin.register(Favorite, ShoppingCart)
class FavoriteAdmin(admin.ModelAdmin):
    """Настройка админзоны для моделей подписки и корзины."""

    list_display = (
        'user',
        'recipe',
    )
    search_fields = ('user',)
    list_filter = ('user',)


admin.site.empty_value_display = 'Не задано'
