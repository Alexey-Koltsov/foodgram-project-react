from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin

from api.pagination import CustomPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (CustomUserSerializer, FavoriteSerializer,
                             IngredientSerializer,
                             RecipeCreateUpdateSerializer,
                             RecipeListSerializer, ShoppingCartSerializer,
                             SubscriptionSerializer,
                             SubscriptionToRepresentationSerializer,
                             TagSerializer)
from recipes.models import (Tag, Ingredient, Recipe, RecipeIngredient,
                            RecipeTag, Favorite, ShoppingCart)
from users.models import Subscription


User = get_user_model()


class CustomUserViewSet(viewsets.ModelViewSet):
    """
    Получаем список всех пользователей, создаем нового пользователя.
    Получаем пользователя по id.
    """

    http_method_names = ('get', 'post')
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [AllowAny,]
    pagination_class = CustomPagination

    @action(
        methods=['get',],
        serializer_class=CustomUserSerializer,
        permission_classes=[IsAuthenticated],
        detail=False,
        url_path='me',
    )
    def user_profile(self, request):
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=['get',],
        serializer_class=SubscriptionToRepresentationSerializer,
        permission_classes=[IsAuthenticated],
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
    permission_classes = [AllowAny,]
    pagination_class = LimitOffsetPagination


class IngredientViewSet(viewsets.ModelViewSet):
    """
    Получаем список всех ингредиентов, получаем ингредиент по id.
    """

    http_method_names = ('get',)
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny,]
    pagination_class = CustomPagination


class RecipeViewSet(viewsets.ModelViewSet):
    """
    Получаем список всех рецептов, создаем рецепт,
    получаем рецепт, изменяем рецепт, удаляем рецепт.
    """

    http_method_names = ('get', 'post', 'patch', 'delete')
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticated, IsAuthorOrReadOnly)
    pagination_class = CustomPagination

    def create(self, request, *args, **kwargs):
        request.data['tags'] = [
            {'id': tag_id} for tag_id in request.data['tags']
        ]
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        request.data['tags'] = [
            {'id': tag_id} for tag_id in request.data['tags']
        ]
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateUpdateSerializer
        return RecipeListSerializer

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


class APIFavoriteCreateDestroy(generics.CreateAPIView,
                               generics.DestroyAPIView):
    """
    Добавляем рецепт в избранное и удаляем рецепт из избранного.
    """

    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user,
                        recipe=get_object_or_404(Recipe, id=self.kwargs['id']))

    def destroy(self, request, *args, **kwargs):
        instance = get_object_or_404(
            Favorite,
            user=self.request.user,
            recipe=get_object_or_404(Recipe, id=self.kwargs['id'])
        )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class APISubsriptionCreateDestroy(generics.CreateAPIView,
                                  generics.DestroyAPIView):
    """
    Добавляем автора в подписки и удаляем автора из подписок.
    """

    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    pagination_class = LimitOffsetPagination

    def perform_create(self, serializer):
        serializer.save(user=self.request.user,
                        author=get_object_or_404(User, id=self.kwargs['id']))

    def destroy(self, request, *args, **kwargs):
        instance = get_object_or_404(
            Subscription,
            user=self.request.user,
            author=get_object_or_404(User, id=self.kwargs['id'])
        )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class APIShoppingCartCreateDestroy(generics.CreateAPIView,
                                   generics.DestroyAPIView):
    """
    Добавляем рецепт в список покупок и удаляем рецепт из списка покупок.
    """

    queryset = ShoppingCart.objects.all()
    serializer_class = ShoppingCartSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user,
                        recipe=get_object_or_404(Recipe, id=self.kwargs['id']))

    def destroy(self, request, *args, **kwargs):
        instance = get_object_or_404(
            ShoppingCart,
            user=self.request.user,
            recipe=get_object_or_404(Recipe, id=self.kwargs['id'])
        )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
