from django.contrib.auth import get_user_model
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.pagination import CustomPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (CustomUserSerializer, IngredientSerializer,
                             RecipeCreateUpdateSerializer,
                             RecipeListSerializer, TagSerializer)
from recipes.models import (Tag, Ingredient, Recipe, RecipeIngredient,
                            RecipeTag, Favorite, ShoppingCart)


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
    pagination_class = LimitOffsetPagination

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

    queryset = Recipe.objects.all()
    http_method_names = ('get', 'post', 'patch', 'delete')
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

    """def get_queryset(self):
        qs = Recipe.objects.add_user_annotations(self.request.user.pk)

        # Фильтры из GET-параметров запроса, например.
        author = self.request.query_params.get('author', None)
        if author:
            qs = qs.filter(author=author)

        return qs"""
