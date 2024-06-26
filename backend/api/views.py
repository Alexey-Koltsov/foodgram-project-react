from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.db.models.functions import Lower
from django.http import FileResponse
from django.shortcuts import get_object_or_404, render
from djoser.serializers import SetPasswordSerializer
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from api.mixins import CustomCreateDestroyMixin
from api.pagination import CustomPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (CustomUserCreateSerializer, CustomUserSerializer,
                             FavoriteSerializer, IngredientSerializer,
                             RecipeCreateUpdateSerializer, RecipeSerializer,
                             ShoppingCartSerializer, SubscriptionSerializer,
                             SubscriptionToRepresentationSerializer,
                             TagSerializer)
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Subscription

User = get_user_model()


def page_not_found(request, exception):
    """Страница не найдена."""
    return render(request, 'static/404.html', status=status.HTTP_404_NOT_FOUND)


class CustomUserViewSet(viewsets.ModelViewSet):
    """
    Cоздаем нового пользователя, получаем список всех пользователей,
    получаем страницу пользователя по id,
    получаем страницу текущего пользователя.
    """

    http_method_names = ('get', 'post')
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if 'me' in self.request.path:
            return CustomUserSerializer

        if 'set_password' in self.request.path:
            return SetPasswordSerializer

        if 'subscriptions' in self.request.path:
            return SubscriptionToRepresentationSerializer

        if self.action in ('create'):
            return CustomUserCreateSerializer

        return CustomUserSerializer

    @action(
        methods=['get'],
        serializer_class=CustomUserSerializer,
        permission_classes=[IsAuthenticated],
        detail=False,
        url_path='me',
    )
    def user_profile(self, request):
        user = self.request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=['post'],
        serializer_class=SetPasswordSerializer,
        permission_classes=[IsAuthenticated],
        detail=False,
        url_path='set_password',
    )
    def change_password(self, request):
        user = self.request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['get'],
        serializer_class=SubscriptionToRepresentationSerializer,
        permission_classes=[IsAuthenticated],
        pagination_class=CustomPagination,
        detail=False,
        url_path='subscriptions',
    )
    def subscriptions_list(self, request):
        subscriptions = Subscription.objects.filter(user=self.request.user)
        author_list = list(subscriptions.values_list('author__id', flat=True))
        queryset = User.objects.filter(id__in=author_list)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TagViewSet(viewsets.ModelViewSet):
    """
    Получаем список всех тэгов, получаем тэг по id.
    """

    http_method_names = ('get')
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]


class IngredientViewSet(viewsets.ModelViewSet):
    """
    Получаем список всех ингредиентов, получаем ингредиент по id.
    """

    http_method_names = ('get',)
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Ingredient.objects.all()
        search = self.request.query_params.get('name', None)
        if search is not None:
            queryset = Ingredient.objects.annotate(
                lower_name=Lower("name")
            ).filter(lower_name__startswith=search.lower())
            return queryset
        return Ingredient.objects.all()


class RecipeViewSet(viewsets.ModelViewSet):
    """
    Получаем список всех рецептов, создаем рецепт,
    получаем рецепт, изменяем рецепт, удаляем рецепт.
    """

    http_method_names = ('get', 'post', 'patch', 'delete')
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    pagination_class = CustomPagination

    @action(
        methods=['get'],
        serializer_class=SubscriptionToRepresentationSerializer,
        permission_classes=[IsAuthenticated],
        detail=False,
        url_path='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        recipes = ShoppingCart.objects.all()
        recipes_list = recipes.values('recipe')
        queryset = RecipeIngredient.objects.filter(recipe__in=recipes_list)
        ingredient_amount = list(queryset.values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(sum_amount=Sum('amount')))
        file_name = 'shopping_cart.txt'
        row = ''
        for obj in ingredient_amount:
            for value in obj.values():
                row += str(value) + ', '
            row = row[:-2]
            row += ';\n'
        response = FileResponse(row, content_type="text/plain,charset=utf8")
        response['Content-Disposition'] = 'attachment; filename={0}'.format(
            file_name
        )
        return response

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

    def get_queryset(self):
        queryset = Recipe.objects.add_user_annotations(self.request.user.pk)
        author = self.request.query_params.get('author', None)
        is_favorited = self.request.query_params.get('is_favorited', None)
        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart', None
        )
        tags = self.request.query_params.get('tags', None)
        if author is not None:
            queryset = queryset.filter(author=author)
        if is_favorited is not None:
            queryset = queryset.filter(is_favorited=is_favorited)
        if is_in_shopping_cart is not None:
            queryset = queryset.filter(is_in_shopping_cart=is_in_shopping_cart)
        if tags is not None:
            tags_slug = dict(self.request.query_params)['tags']
            queryset = queryset.filter(tags__slug__in=tags_slug).distinct()
        return queryset


class APIFavoriteCreateDestroy(CustomCreateDestroyMixin):
    """
    Добавляем рецепт в избранное и удаляем рецепт из избранного.
    """

    def get_queryset(self):
        get_object_or_404(Recipe, id=self.kwargs['id'])
        return Favorite.objects.filter(
            user=self.request.user,
            recipe=self.kwargs['id']
        )

    serializer_class = FavoriteSerializer


class APISubscriptionCreateDestroy(CustomCreateDestroyMixin):
    """
    Добавляем автора в подписки и удаляем автора из подписок.
    """

    def get_queryset(self):
        get_object_or_404(User, id=self.kwargs['id'])
        return Subscription.objects.filter(
            user=self.request.user,
            author__id=self.kwargs['id']
        )

    def check(self):
        return get_object_or_404(User, id=self.kwargs['id'])

    serializer_class = SubscriptionSerializer
    lookup_field = 'author__id'


class APIShoppingCartCreateDestroy(CustomCreateDestroyMixin):
    """
    Добавляем рецепт в список покупок и удаляем рецепт из списка покупок.
    """

    def get_queryset(self):
        get_object_or_404(Recipe, id=self.kwargs['id'])
        return ShoppingCart.objects.filter(
            user=self.request.user,
            recipe__id=self.kwargs['id']
        )
    serializer_class = ShoppingCartSerializer
