import base64
import webcolors
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from recipes.models import (Tag, Ingredient, Recipe, RecipeIngredient,
                            RecipeTag, Favorite, ShoppingCart)
from users.models import Subscription

User = get_user_model()


class CustomUserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели User (пользователь).
    """

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        user = get_object_or_404(User, username=obj)
        return Subscription.objects.filter(user=user).exists()


class Hex2NameColor(serializers.Field):
    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        try:
            data = webcolors.hex_to_name(data)
        except ValueError:
            raise serializers.ValidationError('Для этого цвета нет имени')
        return data


class TagSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Tag (тэг).
    """

    color = Hex2NameColor()

    class Meta:
        model = Tag
        fields = (
            'name',
            'color',
            'slug',
        )


class IngredientSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Ingredient (ингредиент).
    """

    class Meta:
        model = Ingredient
        fields = (
            'name',
            'measurement_unit',
        )


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )
    name = serializers.StringRelatedField(
        source='ingredient.name'
    )
    measurement_unit = serializers.StringRelatedField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeTagSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='tag',
        queryset=Tag.objects.all()
    )
    name = serializers.StringRelatedField(
        source='tag.name'
    )
    color = serializers.StringRelatedField(
        source='tag.color'
    )
    slug = serializers.StringRelatedField(
        source='tag.slug'
    )

    class Meta:
        model = RecipeTag
        fields = ('id', 'name', 'color', 'slug')


class RecipeListSerializer(serializers.ModelSerializer):
    """Получение списка рецептов."""

    id = serializers.IntegerField(read_only=True)
    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username'
    )
    tags = serializers.SerializerMethodField()
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.BooleanField()
    is_in_shopping_cart = serializers.BooleanField()
    author = serializers.SlugRelatedField(slug_field='username',
                                          read_only=True)

    def get_ingredients(self, obj):
        return RecipeIngredientSerializer(
            RecipeIngredient.objects.filter(recipe=obj).all(), many=True
        ).data

    def get_tags(self, obj):
        return RecipeTagSerializer(
            RecipeTag.objects.filter(recipe=obj).all(), many=True
        ).data

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'author', 'tags', 'text', 'ingredients',
                  'image', 'is_favorited', 'is_in_shopping_cart',
                  'cooking_time')


class IngredientCreateInRecipeSerializer(serializers.ModelSerializer):
    recipe = serializers.PrimaryKeyRelatedField(read_only=True)
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(write_only=True, min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ('recipe', 'id', 'amount')


class TagCreateInRecipeSerializer(serializers.ModelSerializer):
    recipe = serializers.PrimaryKeyRelatedField(read_only=True)
    id = serializers.PrimaryKeyRelatedField(
        source='tag',
        queryset=Tag.objects.all()
    )

    class Meta:
        model = RecipeTag
        fields = ('recipe', 'id',)


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Сериалайзер для создания и обновления рецепта.
    """

    id = serializers.IntegerField(read_only=True)
    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username'
    )
    ingredients = IngredientCreateInRecipeSerializer(many=True)
    tags = TagCreateInRecipeSerializer(many=True)
    image = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)

    def validate_ingredients(self, value):
        if len(value) < 1:
            raise serializers.ValidationError(
                'Добавьте хотя бы один ингредиент.'
            )
        return value

    def validate_tags(self, value):
        if len(value) < 1:
            raise serializers.ValidationError(
                'Добавьте хотя бы один тэг.'
            )
        return value

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)

        create_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        ]
        RecipeIngredient.objects.bulk_create(
            create_ingredients
        )

        create_tags = [
            RecipeTag(
                recipe=recipe,
                tag=tag['tag'],
            )
            for tag in tags
        ]
        RecipeTag.objects.bulk_create(
            create_tags
        )
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients', None)
        if ingredients is not None:
            instance.ingredients.clear()
            create_ingredients = [
                RecipeIngredient(
                    recipe=instance,
                    ingredient=ingredient['ingredient'],
                    amount=ingredient['amount']
                )
                for ingredient in ingredients
            ]
            RecipeIngredient.objects.bulk_create(
                create_ingredients
            )

        tags = validated_data.pop('tags', None)
        if tags is not None:
            instance.tags.clear()
            create_tags = [
                RecipeTag(
                    recipe=instance,
                    tag=tag['tag'],
                )
                for tag in tags
            ]
            RecipeTag.objects.bulk_create(
                create_tags
            )

        return super().update(instance, validated_data)

    def to_representation(self, obj):
        """Возвращаем представление в таком же виде, как и GET-запрос."""
        self.fields.pop('ingredients')
        self.fields.pop('tags')
        representation = super().to_representation(obj)
        representation['ingredients'] = RecipeIngredientSerializer(
            RecipeIngredient.objects.filter(recipe=obj).all(), many=True
        ).data
        representation['tags'] = RecipeTagSerializer(
            RecipeTag.objects.filter(recipe=obj).all(), many=True
        ).data
        user = get_object_or_404(User, username=self.context['request'].user)
        author = get_object_or_404(User, username=representation['author'])
        representation['is_subscribed'] = Subscription.objects.filter(
            user=user, author=author,
        ).exists()
        recipe = get_object_or_404(Recipe, id=representation['id'])
        representation['is_in_shopping_cart'] = ShoppingCart.objects.filter(
            user=user, recipe=recipe,
        ).exists()
        return representation

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'name', 'ingredients', 'tags', 'text', 'image',
            'cooking_time', 'is_subscribed', 'is_in_shopping_cart',)


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с моделью Favorite."""

    user = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username'
    )
    recipe = serializers.SlugRelatedField(
        slug_field='name',
        queryset=Recipe.objects.all()
    )

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def get_queryset(self):
        return self.context['request'].user.favorite_set.all()

    def validate_recipe(self, value):
        request = self.context['request']
        recipe_list = list(self.get_queryset().values_list(
            'recipe__name', flat=True))
        if value.author.username == request.user.username:
            raise serializers.ValidationError(
                'Подписываться на свои рецепты нельзя!'
            )
        if value.name in recipe_list:
            raise serializers.ValidationError(
                f'{request.user.username} уже подписан(а)'
                f' на рецерт {value.name}!'
            )
        return value
