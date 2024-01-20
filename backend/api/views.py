from django.contrib.auth import get_user_model
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.serializers import CustomUserSerializer


User = get_user_model()


class CustomUserViewSet(viewsets.ModelViewSet):
    """
    Получаем список всех пользователей, создаем нового пользователя.
    Получаем id.
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
