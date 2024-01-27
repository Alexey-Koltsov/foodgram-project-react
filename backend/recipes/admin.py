from django.contrib import admin

from recipes.models import Recipe, Tag


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Настройка админзоны для модели рецептов."""

    list_display = (
        'author',
        'name',
        'text',
        'cooking_time',
    )
    filter_horizontal = ('ingredients', 'tags',)
    search_fields = ('name',)
    list_filter = ('name',)



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


admin.site.empty_value_display = 'Не задано'
