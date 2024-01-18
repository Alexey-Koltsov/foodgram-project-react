from django.urls import include, path
from rest_framework.routers import DefaultRouter

#from api.views import

app_name = 'api'

router_api_01 = DefaultRouter()

#router_api_01.register('users', UserViewSet, basename='users')
#router_api_01.register('genres', GenreViewSet, basename='genres')
#router_api_01.register('categories', CategoryViewSet, basename='categories')
#router_api_01.register('titles', TitleViewSet, basename='titles')
#router_api_01.register(
#    r'titles/(?P<title_id>\d+)/reviews',
#    ReviewViewSet,
#    basename='reviews'
#)
#router_api_01.register(
#    r'titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments',
#    CommentViewSet,
#    basename='comments'
#)

#auth_urlpatterns = [
#    path('signup/', signup, name='signup'),
#    path('token/', get_token, name='token'),
#]

urlpatterns = [
    path('', include(router_api_01.urls)),
]
