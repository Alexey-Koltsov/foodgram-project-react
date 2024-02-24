import aspose.words as aw
from django.db.models import Sum
from django.db.models.functions import Lower
from django.contrib.auth import get_user_model
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from api.pagination import CustomPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (CustomUserSerializer, CustomUserCreateSerializer,
                             FavoriteSerializer, IngredientSerializer,
                             RecipeCreateUpdateSerializer,
                             RecipeSerializer, ShoppingCartSerializer,
                             SubscriptionSerializer,
                             SubscriptionToRepresentationSerializer,
                             TagSerializer)
from djoser.serializers import SetPasswordSerializer
from recipes.models import (Ingredient, Favorite, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Subscription


User = get_user_model()


class CustomUserViewSet(viewsets.ModelViewSet):
    """
    Cоздаем нового пользователя, получаем список всех пользователей,
    получаем страницу пользователя по id,
    получаем страницу текущего пользователя.
    """

    http_method_names = ('get', 'post')
    queryset = User.objects.all()
    permission_classes = [AllowAny,]
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if ('me') in self.request.path:
            return CustomUserSerializer

        if ('set_password') in self.request.path:
            return SetPasswordSerializer

        if ('subscriptions') in self.request.path:
            return SubscriptionToRepresentationSerializer

        if self.action in ('create'):
            return CustomUserCreateSerializer

        return CustomUserSerializer

    @action(
        methods=['get',],
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
        methods=['post',],
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
        methods=['get',],
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
    permission_classes = [AllowAny,]


class IngredientViewSet(viewsets.ModelViewSet):
    """
    Получаем список всех ингредиентов, получаем ингредиент по id.
    """

    http_method_names = ('get',)
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny,]

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
        methods=['get',],
        serializer_class=SubscriptionToRepresentationSerializer,
        permission_classes=[IsAuthenticated],
        detail=False,
        url_path='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        recipes = ShoppingCart.objects.filter(user=self.request.user)
        recipes_list = recipes.values('recipe')
        queryset = RecipeIngredient.objects.filter(recipe__in=recipes_list)
        ingredient_amount = list(queryset.values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(sum_amount=Sum('amount')))
        doc = aw.Document()
        builder = aw.DocumentBuilder(doc)
        builder.list_format.apply_number_default()
        for obj in ingredient_amount:
            row = ''
            for value in obj.values():
                row += str(value) + ','
            row = row[:-1]
            builder.writeln(row)
        builder.list_format.remove_numbers()
        doc.save('shopping_cart.docx')
        return FileResponse(open('shopping_cart.docx', 'rb'),
                            as_attachment=True)

    def check_ingreds(self, request):
        ingredients_id = [
            ingredient['id'] for ingredient in request.data['ingredients']
        ]
        return len(ingredients_id) != len(set(ingredients_id))

    def check_tags(self, request):
        return len(request.data['tags']) != len(set(request.data['tags']))

    def create(self, request, *args, **kwargs):
        if 'tags' not in request.data or self.check_tags(request):
            return Response({'detail': 'В запросе отсутствует поле tags'
                             ' или тэги повторяются'},
                            status=status.HTTP_400_BAD_REQUEST)
        if 'ingredients' not in request.data or self.check_ingreds(request):
            return Response({'detail': 'В запросе отсутствует поле'
                             ' ingredients или повторяются ингредиенты'},
                            status=status.HTTP_400_BAD_REQUEST)
        request.data['tags'] = [
            {'id': tag_id} for tag_id in request.data['tags']
        ]
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED,
                        headers=headers)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def update(self, request, *args, **kwargs):
        if 'tags' not in request.data or self.check_tags(request):
            return Response({'detail': 'В запросе отсутствует поле tags'
                             ' или тэги повторяются'},
                            status=status.HTTP_400_BAD_REQUEST)
        if 'ingredients' not in request.data or self.check_ingreds(request):
            return Response({'detail': 'В запросе отсутствует поле'
                             ' ingredients или повторяются ингредиенты'},
                            status=status.HTTP_400_BAD_REQUEST)
        partial = kwargs.pop('partial', False)
        request.data['tags'] = [
            {'id': tag_id} for tag_id in request.data['tags']
        ]
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data,
                                         partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

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


class APIFavoriteCreateDestroy(generics.CreateAPIView,
                               generics.DestroyAPIView):
    """
    Добавляем рецепт в избранное и удаляем рецепт из избранного.
    """

    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer
    permission_classes = (IsAuthenticated, IsAuthorOrReadOnly)

    def create(self, request, *args, **kwargs):
        recipes_list = list(Recipe.objects.values_list('id', flat=True))
        recipes_in_favorite_list = list(self.get_queryset().filter(
            user=request.user
        ).values_list('recipe__id', flat=True))
        if not self.kwargs['id'] in recipes_list:
            return Response(
                'Добавлять в избранное не существующие рецепты нельзя!',
                status=status.HTTP_400_BAD_REQUEST
            )
        if self.kwargs['id'] in recipes_in_favorite_list:
            return Response(
                f'Рецерт уже в избранном {request.user.username}!',
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED,
                        headers=headers)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user,
                        recipe=get_object_or_404(Recipe, id=self.kwargs['id']))

    def destroy(self, request, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=self.kwargs['id'])
        recipes_in_favorite_list = list(self.get_queryset().filter(
            user=request.user
        ).values_list('recipe__id', flat=True))
        if self.kwargs['id'] not in recipes_in_favorite_list:
            return Response(
                'В избранном нет такого рецепта!',
                status=status.HTTP_400_BAD_REQUEST
            )
        instance = get_object_or_404(
            Favorite,
            user=self.request.user,
            recipe=recipe
        )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class APISubscriptionCreateDestroy(generics.CreateAPIView,
                                   generics.DestroyAPIView):
    """
    Добавляем автора в подписки и удаляем автора из подписок.
    """

    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = (IsAuthenticated, IsAuthorOrReadOnly)

    def create(self, request, *args, **kwargs):
        authors_list = list(self.get_queryset().values_list(
            'author__id', flat=True))
        if self.kwargs['id'] == request.user.id:
            return Response('Подписываться на самого себя нельзя!',
                            status=status.HTTP_400_BAD_REQUEST)
        if self.kwargs['id'] in authors_list:
            return Response(
                f'{self.request.user.username} уже подписан(а)'
                f' на этого автора!',
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED,
                        headers=headers)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user,
                        author=get_object_or_404(User, id=self.kwargs['id']))

    def destroy(self, request, *args, **kwargs):
        author = get_object_or_404(User, id=self.kwargs['id'])
        subscriptions_id_list = list(self.get_queryset().filter(
            user=self.request.user
        ).values_list('author__id', flat=True))
        if self.kwargs['id'] not in subscriptions_id_list:
            return Response(
                'Такой подписки не существует!',
                status=status.HTTP_400_BAD_REQUEST
            )
        instance = get_object_or_404(
            Subscription,
            user=self.request.user,
            author=author
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
    permission_classes = (IsAuthenticated, IsAuthorOrReadOnly)

    def create(self, request, *args, **kwargs):
        recipes_list = list(Recipe.objects.values_list('id', flat=True))
        recipes_in_shoppingcart_list = list(self.get_queryset().filter(
            user=request.user
        ).values_list('recipe__id', flat=True))
        if not self.kwargs['id'] in recipes_list:
            return Response(
                'Добавлять в список покупок не существующие рецепты нельзя!',
                status=status.HTTP_400_BAD_REQUEST
            )
        if self.kwargs['id'] in recipes_in_shoppingcart_list:
            return Response(
                f'Рецерт уже в списке покупок {request.user.username}!',
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED,
                        headers=headers)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user,
                        recipe=get_object_or_404(Recipe, id=self.kwargs['id']))

    def destroy(self, request, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=self.kwargs['id'])
        recipes_in_shoppingcart_list = list(self.get_queryset().filter(
            user=request.user
        ).values_list('recipe__id', flat=True))
        if self.kwargs['id'] not in recipes_in_shoppingcart_list:
            return Response(
                'В корзине нет такого рецепта!',
                status=status.HTTP_400_BAD_REQUEST
            )
        instance = get_object_or_404(
            ShoppingCart,
            user=self.request.user,
            recipe=recipe
        )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
