from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from recipes.models import Recipe

User = get_user_model()


class CustomCreateDestroyMixin(generics.CreateAPIView,
                               generics.DestroyAPIView):
    """
    Миксин для создания и удаления объектов избранного и корзины.
    """

    permission_classes = (IsAuthenticated,)
    lookup_field = 'recipe__id'
    lookup_url_kwarg = 'id'

    def check(self):
        if not Recipe.objects.filter(
            id=self.kwargs['id']
        ).exists():
            return Response(
                'Такого объекта не существует!',
                status=status.HTTP_400_BAD_REQUEST
            )

    def create(self, request, *args, **kwargs):
        self.check()
        request.data['author'] = self.kwargs['id']
        request.data['recipe'] = self.kwargs['id']
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        if not self.get_queryset().exists():
            return Response(
                'Такого объекта не существует!',
                status=status.HTTP_400_BAD_REQUEST
            )
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
