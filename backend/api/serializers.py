import base64
import collections
import webcolors
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.files.base import ContentFile
from django.core.validators import MaxLengthValidator, RegexValidator
from django.shortcuts import get_object_or_404
from djoser.serializers import SetPasswordSerializer, UserCreateSerializer, UserSerializer
from rest_framework import serializers

from recipes.models import (Tag, Ingredient, Recipe, RecipeIngredient,
                            RecipeTag, Favorite, ShoppingCart)
from users.models import Subscription

User = get_user_model()


class CustomUserCreateSerializer(UserCreateSerializer):
    """
    Сериализатор для создания пользователя.
    """

    id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField(
        required=True,
        validators=[
            MaxLengthValidator(settings.MAX_LEN_EMAIL),
        ]
    )
    username = serializers.CharField(
        required=True,
        validators=[
            UnicodeUsernameValidator,
            MaxLengthValidator(settings.MAX_LEN_USERNAME),
            RegexValidator(
                r'^[\w.@+-]+$',
                'Недопустимый символ.'
            )
        ]
    )
    first_name = serializers.CharField(
        required=True,
        validators=[
            MaxLengthValidator(settings.MAX_LEN_USERNAME),
        ]
    )
    last_name = serializers.CharField(
        required=True,
        validators=[
            MaxLengthValidator(settings.MAX_LEN_USERNAME),
        ]
    )
    password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[
            MaxLengthValidator(settings.MAX_LEN_PASSWORD),
        ]
    )

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )


class CustomUserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели User (пользователь).
    """

    id = serializers.IntegerField(read_only=True)
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
        if 'request' in self.context:
            return (
                self.context['request'].user.is_authenticated and
                Subscription.objects.filter(
                    user=self.context['request'].user,
                    author=obj
                ).exists())
        else:
            return (
                Subscription.objects.filter(
                    user=obj,
                    author=obj
                ).exists())


class TagSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Tag (тэг).
    """

    class Meta:
        model = Tag
        fields = (
            'id',
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
            'id',
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


class RecipeSerializer(serializers.ModelSerializer):
    """
    Получение списка рецептов и рецепта по id.
    """

    id = serializers.IntegerField(read_only=True)
    tags = serializers.SerializerMethodField()
    author = CustomUserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.BooleanField()
    is_in_shopping_cart = serializers.BooleanField()

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
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
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
    ingredients = IngredientCreateInRecipeSerializer(required=True, many=True)
    tags = TagCreateInRecipeSerializer(required=True, many=True)
    image = Base64ImageField(required=True)
    name = serializers.CharField(
        required=True,
        validators=[
            MaxLengthValidator(settings.MAX_LEN_NAME),
        ]
        )
    text = serializers.CharField(required=True)
    cooking_time = serializers.IntegerField(required=True)
    is_favorited = serializers.BooleanField(read_only=True)
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

    def validate_cooking_time(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Должно быть не меньше 1.'
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
        recipe = get_object_or_404(Recipe, id=representation['id'])
        representation['is_favorited'] = Favorite.objects.filter(
            user=user, recipe=recipe,
        ).exists()
        representation['is_in_shopping_cart'] = ShoppingCart.objects.filter(
            user=user, recipe=recipe,
        ).exists()
        self.fields.pop('author')
        representation['author'] = CustomUserSerializer(author).data
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time')
        data = collections.OrderedDict()
        for field in fields:
            data[field] = representation[field]
        return data

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time')


class RecipeMinifieldSerializer(serializers.ModelSerializer):
    """Получение мини списка рецептов."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с моделью Favorite."""

    user = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username'
    )
    recipe = RecipeMinifieldSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def get_queryset(self):
        return self.context['request'].user.favorite_set.all()

    """def validate_recipe(self, value):
        request = self.context['request']
        recipe_list = list(self.get_queryset().values_list(
            'recipe__name', flat=True))
        if value.author.username == request.user.username:
            raise serializers.ValidationError(
                'Добавлять в избранное свои рецепты нельзя!'
            )
        if value.name in recipe_list:
            raise serializers.ValidationError(
                f'Рецерт {value.name} уже в избранном'
                f' пользователя {request.user.username}!'
            )
        return value"""

    def to_representation(self, instance):
        return RecipeMinifieldSerializer(instance.recipe).data


class SubscriptionToRepresentationSerializer(CustomUserSerializer):
    """Сериализатор для отображения списка подписок и отдельной подписки."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = CustomUserSerializer.Meta.fields + ('recipes',
                                                     'recipes_count',)
        read_only_fields = ('__all__',)

    def get_recipes(self, obj):
        recipes = RecipeMinifieldSerializer(
            Recipe.objects.filter(author=obj),
            many=True
        ).data
        if self.context:
            recipes_limit = self.context['request'].query_params.get(
                'recipes_limit', None)
            if recipes_limit is not None:
                recipes = recipes[0:int(recipes_limit)]
        return recipes

    def get_recipes_count(self, obj):
        recipes_count = Recipe.objects.filter(author=obj).count()
        return recipes_count


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с моделью Subscription."""

    class Meta:
        model = Subscription
        fields = ('user', 'author')
        read_only_fields = ('user', 'author')

    def get_queryset(self):
        return self.context['request'].user.subscription_user.all()

    """def validate_author(self, value):
        request = self.context['request']
        author_list = list(self.get_queryset().values_list(
            'author__id', flat=True))
        print(author_list)
        if value.id == request.user.id:
            raise serializers.ValidationError(
                'Подписываться на самого себя нельзя!'
            )
        if value.id in author_list:
            raise serializers.ValidationError(
                f'{request.user.username} уже подписан(а)'
                f' на {value.username}!'
            )
        return value"""

    def to_representation(self, instance):
        representation = SubscriptionToRepresentationSerializer(
            instance.author
        ).data
        recipes_limit = self.context['request'].query_params.get(
            'recipes_limit', None)
        if recipes_limit is not None:
            recipes_limit = int(recipes_limit)
            representation['recipes'] = representation[
                'recipes'
            ][0:recipes_limit]
        return representation


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с моделью Favorite."""

    user = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username'
    )
    recipe = RecipeMinifieldSerializer(read_only=True)

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def get_queryset(self):
        return self.context['request'].user.shoppingcart_set.all()

    """def validate_recipe(self, value):
        request = self.context['request']
        shoppingcart_list = list(self.get_queryset().values_list(
            'recipe__name', flat=True))
        if value.author.username == request.user.username:
            raise serializers.ValidationError(
                'Добавлять в избранное свои рецепты нельзя!'
            )
        if value.name in shoppingcart_list:
            raise serializers.ValidationError(
                f'Рецерт {value.name} уже в списке'
                f' покупок {request.user.username}!'
            )
        return value"""

    def to_representation(self, instance):
        return RecipeMinifieldSerializer(instance.recipe).data
