from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (CustomUserViewSet, IngredientViewSet, APIFavoriteCreateDestroy,  # FavoriteViewSet
                       RecipeViewSet, TagViewSet)


app_name = 'api'

router_api_01 = DefaultRouter()

router_api_01.register('users', CustomUserViewSet, basename='users')
router_api_01.register('tag', TagViewSet, basename='tag')
router_api_01.register('ingredients', IngredientViewSet, basename='ingredients')
router_api_01.register('recipes', RecipeViewSet, basename='recipes')
"""router_api_01.register(
    r'recipes/(?P<id>\d+)/favorite',
    FavoriteViewSet,
    basename='favorite'
)"""

recipe_favorite_subscribe_urlpatterns = [
    path('recipes/<int:id>/favorite/', APIFavoriteCreateDestroy.as_view()),
]


urlpatterns = [
    path('', include(router_api_01.urls)),
    path('', include(recipe_favorite_subscribe_urlpatterns)),
    path('auth/', include('djoser.urls.authtoken')),
]
