from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from api.filters import RecipeFilter
from api.permissions import AuthorOrReadOnly
from api.render import render_shopping_list
from recipes.models import (Favorite, Follow, Ingredient, IngredientToRecipe,
                            Recipe, ShoppingCart, Tag, User)
from .serializers import (AvatarSerializer, FollowReadSerializer,
                          IngredientsSerializer, RecipeShortReadSerializer,
                          ResipeWriteSerializer, ResipesReadSerializer,
                          TagSerializer)


class PaginationReadBaseModel(viewsets.ReadOnlyModelViewSet):
    pagination_class = None


class IngredientsViewSet(PaginationReadBaseModel):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientsSerializer
    filter_backends = (SearchFilter,)
    search_fields = ('^name',)


class TagsViewSet(PaginationReadBaseModel):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class ResipesViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly, AuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return ResipesReadSerializer
        return ResipeWriteSerializer

    @staticmethod
    def add_or_remove_favorite_or_shopping_cart(model, recipe_id, request):
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        user = request.user
        if request.method == 'POST':
            if model.objects.filter(user=user, recipe=recipe).exists():
                raise ValidationError('Рецепт уже добавлен в список')
            model.objects.create(user=user, recipe=recipe)
            return Response(
                RecipeShortReadSerializer(recipe).data,
                status=status.HTTP_201_CREATED
            )
        if not model.objects.filter(user=user, recipe=recipe).exists():
            raise ValidationError('Рецепт отсутствует в списке')
        model.objects.filter(user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,),
        url_path=r'favorite',
    )
    def favorite(self, request, pk):
        return self.add_or_remove_favorite_or_shopping_cart(
            model=Favorite,
            recipe_id=pk,
            request=request,
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,),
        url_path=r'shopping_cart',
    )
    def shopping_cart(self, request, pk):
        return self.add_or_remove_favorite_or_shopping_cart(
            model=ShoppingCart,
            recipe_id=pk,
            request=request,
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,),
        url_path='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        return FileResponse(
            render_shopping_list(
                IngredientToRecipe.objects.filter(
                    recipe__shopping_carts__user=request.user
                ).values('ingredient__name', 'ingredient__measurement_unit')
                .annotate(ingredient_amount=Sum('amount')).order_by(
                    'ingredient'),
                request.user.shopping_carts.all()
            ),
            content_type='text/plain',
            filename='shopping_cart.txt'
        )

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link',
        permission_classes=[
            AllowAny,
        ],
    )
    def get_link(self, request, pk):
        return Response(
            {'short-link': f'{request.META["DNS"]}'
                           f'/s/{get_object_or_404(Recipe, pk=pk).id}'},
            status=status.HTTP_200_OK
        )


class FoodGramUserViewSet(UserViewSet):

    def get_permissions(self):
        if self.action == 'me':
            return (IsAuthenticated(),)
        return super().get_permissions()

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,),
        url_path='subscriptions',
    )
    def subscriptions(self, request):
        pages = self.paginate_queryset(
            User.objects.filter(follow_followers__user=self.request.user)
        )
        serializer = FollowReadSerializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['delete', 'post'],
        permission_classes=(IsAuthenticated,),
        url_path=r'subscribe',
    )
    def subscribe(self, request, id):
        following = get_object_or_404(User, id=id)
        user = request.user
        if following == user:
            raise serializers.ValidationError(
                'Вы не можете подписаться на себя'
            )
        if request.method == 'DELETE':
            if not user.follow_users.filter(
                    following_id=following.id
            ).exists():
                raise serializers.ValidationError(
                    'Вы не подписаны на этого пользователя'
                )
            get_object_or_404(
                Follow,
                user=user,
                following_id=following.id
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        if user.follow_users.filter(following=following):
            raise ValidationError('Вы уже подписаны на этого пользователя')
        Follow.objects.create(user=user, following=following)
        serializer = FollowReadSerializer(
            following,
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid()
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    @action(
        detail=False,
        methods=['delete', 'put'],
        permission_classes=(IsAuthenticated,),
        serializer_class=AvatarSerializer,
        url_path='me/avatar',
    )
    def avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            serializer = self.get_serializer(
                user, data=request.data, context={'request': request}
            )
            if 'avatar' not in request.data:
                raise serializers.ValidationError(
                    'Отсутствует поле "avatar"'
                )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
