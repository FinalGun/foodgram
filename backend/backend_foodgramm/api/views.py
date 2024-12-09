from django.db.models import Sum
from django.shortcuts import HttpResponse, get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from api.permissions import AdminAuthorOrReadOnly
from recipes.models import (Favorite, Follow, Ingredient, IngredientToRecipe,
                            Recipe, ShoppingCart, Tag, User)
from .utils import add_or_remove_favorite_or_shopping_cart
from .serializers import (AvatarSerializer, FavoriteSerializer,
                          FollowReadSerializer, FollowWriteSerializer,
                          IngredientsSerializer, ResipeWriteSerializer,
                          ResipesReadSerializer, ShoppingCartSerializer,
                          TagSerializer)


class IngredientsViewSet(viewsets.ModelViewSet):
	queryset = Ingredient.objects.all()
	serializer_class = IngredientsSerializer
	http_method_names = ('get',)
	filter_backends = (DjangoFilterBackend,)


class TagsViewSet(viewsets.ModelViewSet):
	queryset = Tag.objects.all()
	serializer_class = TagSerializer
	http_method_names = ('get',)


class ResipesViewSet(viewsets.ModelViewSet):
	queryset = Recipe.objects.all()
	permission_classes = [AdminAuthorOrReadOnly]
	filter_backends = [DjangoFilterBackend]
	http_method_names = ['get', 'post', 'patch', 'delete']

	def get_serializer_class(self):
		if self.action in ('list', 'retrieve'):
			return ResipesReadSerializer
		return ResipeWriteSerializer

	@action(
		detail=False,
		methods=['post', 'delete'],
		permission_classes=(IsAuthenticated,),
		serializer_class=FavoriteSerializer,
		url_path=r'(?P<recipe_id>\d+)/favorite'
	)
	def favorite(self, request, recipe_id):
		return add_or_remove_favorite_or_shopping_cart(
			model=Favorite,
			recipe_id=recipe_id,
			serializer_class=FavoriteSerializer,
			request=request,
		)

	@action(
		detail=False,
		methods=['post', 'delete'],
		permission_classes=(IsAuthenticated,),
		serializer_class=ShoppingCartSerializer,
		url_path=r'(?P<recipe_id>\d+)/shopping_cart'
	)
	def shopping_cart(self, request, recipe_id):
		return add_or_remove_favorite_or_shopping_cart(
			model=ShoppingCart,
			recipe_id=recipe_id,
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
			recipe__carts__user=request.user
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
		serializer = FollowReadSerializer(
			User.objects.filter(following__user=self.request.user),
			many=True,
			context={'request': request}
		)
		return Response(serializer.data)


	@action(
		detail=False,
		methods=['delete', 'post'],
		permission_classes=(IsAuthenticated,),
		url_path=r'(?P<user_id>\d+)/subscribe'
	)
	def subscribe(self, request, user_id):
		if request.method == 'DELETE':
			following = Follow.objects.filter(
				user=request.user, following_id=self.kwargs['user_id']
			)
			following.delete()
			return Response(status=status.HTTP_204_NO_CONTENT)
		serializer = FollowWriteSerializer(
			data={
				'user': request.user.id,
				'following': self.kwargs['user_id']
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
