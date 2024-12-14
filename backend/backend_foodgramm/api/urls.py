from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (ResipesViewSet, TagsViewSet,
                    IngredientsViewSet, CustomUserViewSet,)

router_v1 = DefaultRouter()

router_v1.register(r'recipes', ResipesViewSet, basename='recipes')
router_v1.register(r'tags', TagsViewSet, basename='tags')
router_v1.register(r'ingredients', IngredientsViewSet, basename='ingredients')
router_v1.register('users', CustomUserViewSet, basename='users')
urlpatterns = [
    path('', include(router_v1.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
