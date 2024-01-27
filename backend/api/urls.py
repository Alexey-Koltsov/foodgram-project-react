from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (CustomUserViewSet, IngredientViewSet, RecipeViewSet,
                       TagViewSet)


app_name = 'api'

router_api_01 = DefaultRouter()

router_api_01.register('users', CustomUserViewSet, basename='users')
router_api_01.register('tag', TagViewSet, basename='tag')
router_api_01.register('ingredients', IngredientViewSet, basename='ingredients')
router_api_01.register('recipes', RecipeViewSet, basename='recipes')


urlpatterns = [
    path('', include(router_api_01.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
