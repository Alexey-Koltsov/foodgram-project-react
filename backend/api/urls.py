from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import CustomUserViewSet

app_name = 'api'

router_api_01 = DefaultRouter()

router_api_01.register('users', CustomUserViewSet, basename='users')
router_api_01.register('users/me', CustomUserViewSet, basename='usersme')


urlpatterns = [
    #path('', include('djoser.urls')),
    path('', include(router_api_01.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
