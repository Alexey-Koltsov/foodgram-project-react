from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.permissions import IsAuthorOrReadOnly
from recipes.models import Recipe

User = get_user_model()


class CustomCreateDestroyMixin(generics.CreateAPIView,
                               generics.DestroyAPIView):
    """
    Миксин для создания и удаления объектов избранного и корзины.
    """

    permission_classes = (IsAuthenticated, IsAuthorOrReadOnly)

    def create(self, request, *args, **kwargs):
        if 'subscribe' in request.path_info:
            get_object_or_404(User, id=self.kwargs['id'])
            request.data['author'] = self.kwargs['id']
        else:
            request.data['recipe'] = self.kwargs['id']
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED,
                        headers=headers)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        if 'subscribe' in request.path_info:
            author = get_object_or_404(User, id=self.kwargs['id'])
            if not self.get_queryset().filter(
                user=request.user,
                author__id=self.kwargs['id']
            ).exists():
                return Response(
                    'Такой подписки не существует!',
                    status=status.HTTP_400_BAD_REQUEST
                )
            instance = get_object_or_404(
                self.get_queryset(),
                user=self.request.user,
                author=author
            )
        else:
            recipe = get_object_or_404(Recipe, id=self.kwargs['id'])
            if not self.get_queryset().filter(
                user=request.user,
                recipe__id=self.kwargs['id']
            ).exists():
                return Response(
                    'Этот рецепт не добавлен!',
                    status=status.HTTP_400_BAD_REQUEST
                )
            instance = get_object_or_404(
                self.get_queryset(),
                user=self.request.user,
                recipe=recipe
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
