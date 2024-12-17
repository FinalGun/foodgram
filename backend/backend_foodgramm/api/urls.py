from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ResipesViewSet, TagsViewSet, IngredientsViewSet, FoodGramUserViewSet
)

router_api = DefaultRouter()

router_api.register(r'recipes', ResipesViewSet, basename='recipes')
router_api.register(r'tags', TagsViewSet, basename='tags')
router_api.register(
    r'ingredients', IngredientsViewSet, basename='ingredients'
)
router_api.register('users', FoodGramUserViewSet, basename='users')
urlpatterns = [
    path('', include(router_api.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
