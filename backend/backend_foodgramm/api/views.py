import os

from dotenv import load_dotenv
from django.db.models import Sum
from django.shortcuts import HttpResponse, get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from api.filters import RecipeFilter
from api.permissions import AdminAuthorOrReadOnly
from .serializers import (
	AvatarSerializer, FavoriteSerializer, FollowReadSerializer,
	FollowWriteSerializer, IngredientsSerializer, ResipeWriteSerializer,
	ResipesReadSerializer, ShoppingCartSerializer, TagSerializer
)
from recipes.models import (
	Favorite, Follow, Ingredient, IngredientToRecipe,
	Recipe, ShoppingCart, Tag, User
)
from .utils import add_or_remove_favorite_or_shopping_cart

load_dotenv()


class IngredientsViewSet(viewsets.ModelViewSet):
	queryset = Ingredient.objects.all()
	serializer_class = IngredientsSerializer
	http_method_names = ('get',)
	filter_backends = (SearchFilter,)
	search_fields = ('^name',)
	pagination_class = None


class TagsViewSet(viewsets.ModelViewSet):
	queryset = Tag.objects.all()
	serializer_class = TagSerializer
	http_method_names = ('get',)
	pagination_class = None


class ResipesViewSet(viewsets.ModelViewSet):
	queryset = Recipe.objects.all()
	permission_classes = [AdminAuthorOrReadOnly]
	filter_backends = [DjangoFilterBackend]
	filterset_class = RecipeFilter
	http_method_names = ['get', 'post', 'patch', 'delete']

	def get_serializer_class(self):
		if self.action in ('list', 'retrieve'):
			return ResipesReadSerializer
		return ResipeWriteSerializer

	@action(
		detail=True,
		methods=['post', 'delete'],
		permission_classes=(IsAuthenticated,),
		serializer_class=FavoriteSerializer,
		url_path=r'favorite'
	)
	def favorite(self, request, pk):
		return add_or_remove_favorite_or_shopping_cart(
			model=Favorite,
			recipe_id=pk,
			serializer_class=FavoriteSerializer,
			request=request,
		)

	@action(
		detail=True,
		methods=['post', 'delete'],
		permission_classes=(IsAuthenticated,),
		serializer_class=ShoppingCartSerializer,
		url_path=r'shopping_cart'
	)
	def shopping_cart(self, request, pk):
		return add_or_remove_favorite_or_shopping_cart(
			model=ShoppingCart,
			recipe_id=pk,
			serializer_class=ShoppingCartSerializer,
			request=request,
		)

	@action(
		detail=False,
		methods=['get'],
		permission_classes=(IsAuthenticated,),
		url_path='download_shopping_cart'
	)
	def download_shopping_cart(self, request):
		ingredients = IngredientToRecipe.objects.filter(
			recipe__shoppingCart__user=request.user
		).values(
			'ingredient__name', 'ingredient__measurement_unit'
		).annotate(ingredient_amount=Sum('amount'))
		shopping_list = ['Список покупок:\n']
		for ingredient in ingredients:
			name = ingredient['ingredient__name']
			unit = ingredient['ingredient__measurement_unit']
			amount = ingredient['ingredient_amount']
			shopping_list.append(f'\n{name} - {amount}, {unit}')
		response = HttpResponse(shopping_list, content_type='text/plain')
		response['Content-Disposition'] = \
			'attachment; filename="shopping_cart.txt"'
		return response

	@action(
		detail=True,
		methods=['get'],
		url_path=r'get-link',
		permission_classes=[AllowAny, ]
	)
	def get_link(self, request, pk):
		dns = os.getenv('DNS')
		data = {
			'short-link': f'foodgramfinal.ddns.net/recipes/{pk.id}'
		}
		return Response(data, status=status.HTTP_200_OK)





class FollowWriteViewSet(viewsets.ModelViewSet):
	queryset = Follow.objects.all()
	serializer_class = FollowWriteSerializer
	http_method_names = ['post', 'delete']

	def perform_create(self, serializer):
		serializer.save(
			user=self.request.user,
			following=User.objects.get(pk=self.kwargs['user_id'])
		)

	@action(detail=True, methods=['delete'])
	def destroy(self):
		follow = get_object_or_404(
			Follow, user=self.request.user,
			following_id=self.kwargs['user_id']
		)
		follow.delete()
		return Response(status=status.HTTP_204_NO_CONTENT)


class CustomUserViewSet(UserViewSet):

	def get_permissions(self):
		if self.action == 'me':
			return (IsAuthenticated(),)
		return super().get_permissions()

	@action(
		detail=False,
		methods=['get'],
		permission_classes=(IsAuthenticated,),
		url_path='subscriptions'
	)
	def subscriptions(self, request):
		pages = self.paginate_queryset(
			User.objects.filter(following__user=self.request.user)
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
		url_path=r'subscribe'
	)
	def subscribe(self, request, pk):
		get_object_or_404(User, id=pk)
		if request.method == 'DELETE':
			if not request.user.follower.filter(
					following_id=pk).exists():
				return Response(
					{'error': 'Вы не подписаны на этого пользователя'},
					status=status.HTTP_400_BAD_REQUEST
				)
			following = get_object_or_404(
				Follow,
				user=request.user, following_id=pk
			)
			following.delete()
			return Response(status=status.HTTP_204_NO_CONTENT)
		serializer = FollowWriteSerializer(
			data={
				'user': request.user.id,
				'following': pk
			},
			context={'request': request}
		)
		serializer.is_valid(raise_exception=True)
		serializer.save()
		return Response(serializer.data, status=status.HTTP_201_CREATED)

	@action(
		detail=False,
		methods=['delete', 'put'],
		permission_classes=(IsAuthenticated,),
		serializer_class=AvatarSerializer,
		url_path='me/avatar'
	)
	def avatar(self, request):
		user = request.user
		if request.method == 'PUT':
			serializer = self.get_serializer(
				user,
				data=request.data,
				context={'request': request}
			)
			if 'avatar' not in request.data:
				return Response(
					{'error': 'Отсутствует поле "avatar"'},
					status=status.HTTP_400_BAD_REQUEST
				)
			serializer.is_valid(raise_exception=True)
			serializer.save()
			return Response(serializer.data, status=status.HTTP_200_OK)
		user.avatar.delete()
		return Response(status=status.HTTP_204_NO_CONTENT)
