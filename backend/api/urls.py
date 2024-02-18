from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (APIFavoriteCreateDestroy, APISubsriptionCreateDestroy,
                       APIShoppingCartCreateDestroy, CustomUserViewSet,
                       IngredientViewSet, RecipeViewSet, TagViewSet)


app_name = 'api'

router_api_01 = DefaultRouter()

router_api_01.register('users', CustomUserViewSet, basename='users')
router_api_01.register('tags', TagViewSet, basename='tag')
router_api_01.register('ingredients', IngredientViewSet,
                       basename='ingredients')
router_api_01.register('recipes', RecipeViewSet, basename='recipes')

recipe_favorite_subscribe_urlpatterns = [
    path('recipes/<int:id>/favorite/', APIFavoriteCreateDestroy.as_view()),
    path('recipes/<int:id>/shopping_cart/',
         APIShoppingCartCreateDestroy.as_view()),
    path('users/<int:id>/subscribe/', APISubsriptionCreateDestroy.as_view()),
]


urlpatterns = [
    path('', include(router_api_01.urls)),
    path('', include(recipe_favorite_subscribe_urlpatterns)),
    #path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
