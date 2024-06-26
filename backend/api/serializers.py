from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import MaxLengthValidator, RegexValidator
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers

from api.fields import Base64ImageField
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            RecipeTag, ShoppingCart, Tag)
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
                self.context['request'].user.is_authenticated
                and Subscription.objects.filter(
                    user=self.context['request'].user,
                    author=obj
                ).exists())
        return False


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
    tags = TagSerializer(read_only=True, many=True)
    image = serializers.SerializerMethodField()
    author = CustomUserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredient', read_only=True, many=True
    )
    is_favorited = serializers.BooleanField()
    is_in_shopping_cart = serializers.BooleanField()

    def get_image(self, obj):
        if obj.image:
            return obj.image.url
        return None

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

    def validate_ingredients(self, value):
        if len(value) < 1:
            raise serializers.ValidationError(
                'Добавьте хотя бы один ингредиент.'
            )
        ingredients_id = [
            ingr['id'] for ingr in self.context['request'].data['ingredients']
        ]
        if len(ingredients_id) != len(set(ingredients_id)):
            raise serializers.ValidationError(
                'В ингредиентах есть дубли!'
            )
        return value

    def validate_tags(self, value):
        if len(value) < 1:
            raise serializers.ValidationError(
                'Добавьте хотя бы один тэг.'
            )
        tags = [tag['id'] for tag in self.context['request'].data['tags']]
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                'В тэгах есть дубли!'
            )
        return value

    def validate_cooking_time(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Должно быть не меньше 1.'
            )
        return value

    def validate(self, attrs):
        if 'ingredients' not in attrs:
            raise serializers.ValidationError(
                'В запросе отсутствует поле ingredients'
            )

        if 'tags' not in attrs:
            raise serializers.ValidationError(
                'В запросе отсутствует поле tags'
            )
        return attrs

    def get_create_ingredients(self, recipe, ingredients):
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

    def get_create_tags(self, recipe, tags):
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

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        self.get_create_ingredients(recipe, ingredients)
        self.get_create_tags(recipe, tags)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients', None)
        instance.ingredients.clear()
        self.get_create_ingredients(instance, ingredients)
        tags = validated_data.pop('tags', None)
        instance.tags.clear()
        self.get_create_tags(instance, tags)
        return super().update(instance, validated_data)

    def to_internal_value(self, data):
        if 'tags' in data:
            data['tags'] = [{'id': tag} for tag in data['tags']]
        return super().to_internal_value(data)

    def to_representation(self, obj):
        """Возвращаем представление в таком же виде, как и GET-запрос."""

        queryset = Recipe.objects.add_user_annotations(
            self.context['request'].user.pk)
        obj = queryset.get(id=obj.id)
        return RecipeSerializer(obj).data

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'name', 'image',
                  'text', 'cooking_time')


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

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def get_queryset(self):
        return self.context['request'].user.favorite.all()

    def to_representation(self, instance):
        return RecipeMinifieldSerializer(instance.recipe).data

    def validate_recipe(self, value):
        if self.context['request'].method == 'POST':
            if self.get_queryset().filter(user=self.context['request'].user,
                                          recipe=value).exists():
                raise serializers.ValidationError(
                    'Рецерт уже добавлен!'
                )
        return value


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
        read_only_fields = ('user',)

    def get_queryset(self):
        return self.context['request'].user.subscription_user.all()

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

    def validate_author(self, value):
        if self.context['request'].method == 'POST':
            if value == self.context['request'].user:
                raise serializers.ValidationError(
                    'Подписываться на самого себя нельзя!'
                )
            if self.get_queryset().filter(user=self.context['request'].user,
                                          author=value).exists():
                raise serializers.ValidationError(
                    'Уже подписан(а) на этого автора!',
                )
        return value


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с моделью ShoppingCart."""

    user = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username'
    )

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def get_queryset(self):
        return self.context['request'].user.shopping_cart.all()

    def to_representation(self, instance):
        return RecipeMinifieldSerializer(instance.recipe).data

    def validate_recipe(self, value):
        if self.context['request'].method == 'POST':
            if self.get_queryset().filter(user=self.context['request'].user,
                                          recipe=value).exists():
                raise serializers.ValidationError(
                    'Рецерт уже добавлен!'
                )
        return value
