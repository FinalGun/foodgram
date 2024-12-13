import base64
from django.core.files.base import ContentFile
from rest_framework import serializers, validators
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404
from rest_framework.validators import UniqueTogetherValidator
from django.db import transaction

from recipes.models import (
	Recipe, Tag, Ingredient, User, validate_username, MAX_LENGTH_USERNAME,
	MAX_LENGTH_EMAIL, Follow, Favorite, IngredientToRecipe, ShoppingCart
)


class UserSerializer(serializers.ModelSerializer):
	is_subscribed = serializers.SerializerMethodField()
	avatar = serializers.SerializerMethodField()

	def get_is_subscribed(self, following):
		request = self.context.get('request')
		if request.user.is_authenticated:
			return Follow.objects.filter(
				user=request.user, following=following
			).exists()
		return False

	def get_avatar(self, user):
		if user.avatar:
			return user.avatar.url
		return None

	class Meta:
		model = User
		fields = (
			'email', 'id', 'username', 'first_name', 'last_name',
			'is_subscribed', 'avatar'
		)


class Base64imageField(serializers.ImageField):
	def to_internal_value(self, data):
		if isinstance(data, str) and data.startswith('data:image/'):
			format, imgstr = data.split(';base64,')
			ext = format.split('/')[-1]
			data = ContentFile(base64.b64decode(imgstr), name=f'avatar.{ext}')
		return super().to_internal_value(data)


class AvatarSerializer(serializers.ModelSerializer):
	avatar = Base64imageField(allow_null=True)

	class Meta:
		model = User
		fields = ('avatar',)


class IngredientsSerializer(serializers.ModelSerializer):
	class Meta:
		model = Ingredient
		fields = ('id', 'name', 'measurement_unit',)


class IngredientToRecipeSerializer(serializers.ModelSerializer):
	id = serializers.IntegerField(read_only=True, source='ingredient.id')
	name = serializers.CharField(read_only=True, source='ingredient.name')
	measurement_unit = serializers.CharField(
		read_only=True,
		source='ingredient.measurement_unit'
	)

	class Meta:
		model = IngredientToRecipe
		fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientWriteSerializer(serializers.ModelSerializer):
	id = serializers.IntegerField(source='ingredient.id')
	amount = serializers.IntegerField()

	class Meta:
		model = IngredientToRecipe
		fields = ('id', 'amount')


class TagSerializer(serializers.ModelSerializer):
	class Meta:
		model = Tag
		fields = ('id', 'name', 'slug')


class ResipesReadSerializer(serializers.ModelSerializer):
	author = UserSerializer()
	ingredients = IngredientToRecipeSerializer(
		many=True,
		read_only=True,
		source='ingredient_to_recipes'
	)
	tags = TagSerializer(many=True)
	is_favorited = serializers.SerializerMethodField()
	is_in_shopping_cart = serializers.SerializerMethodField()

	class Meta:
		model = Recipe
		fields = (
			'id', 'tags', 'image', 'author', 'ingredients', 'name',
			'text', 'cooking_time', 'is_favorited', 'is_in_shopping_cart'
		)

	def get_is_favorited(self, obj):
		request = self.context.get('request')
		return (
				request and request.user.is_authenticated
				and Favorite.objects.filter(
			user=request.user, recipe=obj
		).exists()
		)

	def get_is_in_shopping_cart(self, obj):
		request = self.context.get('request')
		return (
				request and request.user.is_authenticated
				and ShoppingCart.objects.filter(
			user=request.user, recipe=obj
		).exists()
		)


class RecipeShortReadSerializer(serializers.ModelSerializer):
	class Meta:
		model = Recipe
		fields = ('id', 'name', 'cooking_time', 'image')


class ResipeWriteSerializer(serializers.ModelSerializer):
	ingredients = IngredientWriteSerializer(
		many=True,
	)
	tags = serializers.PrimaryKeyRelatedField(
		queryset=Tag.objects.all(),
		many=True
	)
	image = Base64imageField()

	class Meta:
		model = Recipe
		fields = (
			'ingredients', 'tags', 'name',
			'text', 'cooking_time', 'image'
		)

	def validate(self, data):
		cooking_time = data.get('cooking_time')
		if cooking_time <= 0:
			raise serializers.ValidationError(
				'Время приготовления должно быть положительным'
			)
		ingredients = data.get('ingredients')
		if not ingredients:
			raise serializers.ValidationError('Ингредиенты не указаны')
		if len(ingredients) != len(
				set(
					[ingredient_id[
							'ingredient'
							]['id'] for ingredient_id in ingredients]
				)
		):
			raise serializers.ValidationError(
				'Ингредиенты не должны повторяться'
			)
		tags = data.get('tags')
		if not tags:
			raise serializers.ValidationError('Теги не указаны')
		if len(tags) != len(set(tags)):
			raise serializers.ValidationError('Теги не должны повторяться')
		return data

	def create(self, validated_data):
		ingredients = validated_data.pop('ingredients')
		tags = validated_data.pop('tags')
		recipe = Recipe.objects.create(
			author=self.context.get('request').user, **validated_data
		)
		recipe.tags.set(tags)
		self.create_ingredients(recipe, ingredients)
		return recipe

	def create_ingredients(self, recipe, ingredients):
		ingredient_list = []
		for ingredient in ingredients:
			ingredient_id = ingredient.get('ingredient').get('id')
			if not Ingredient.objects.filter(id=ingredient_id).exists():
				raise serializers.ValidationError(
					'Несуществующий ингредиент'
				)
			if ingredient['amount'] <= 0:
				raise serializers.ValidationError(
					'Количество ингредиента должно быть положительным'
				)
			ingredient_list.append(
				IngredientToRecipe(
					recipe=recipe,
					ingredient=get_object_or_404(
						Ingredient,
						id=ingredient_id
					),
					amount=ingredient.get('amount')
				)
			)
		IngredientToRecipe.objects.bulk_create(ingredient_list)

	def update(self, instance, validated_data):
		instance.tags.clear()
		instance.ingredients.clear()
		self.create_ingredients(instance, validated_data.pop('ingredients'))
		instance.tags.set(validated_data.pop('tags'))
		return super().update(instance, validated_data)

	def to_representation(self, instance):
		return ResipesReadSerializer(
			instance,
			context=self.context
		).data


class CreateUserSerializer(serializers.ModelSerializer):
	username = serializers.CharField(
		max_length=MAX_LENGTH_USERNAME
	)
	email = serializers.EmailField(max_length=MAX_LENGTH_EMAIL)

	def validate_username(self, username):
		if User.objects.filter(username=username):
			raise serializers.ValidationError(
				'Пользователь с таким ником уже существует'
			)
		return validate_username(username)

	def validate_email(self, email):
		if User.objects.filter(email=email):
			raise serializers.ValidationError(
				'Пользователь с такой почтой уже существует'
			)
		return email

	def create(self, validated_data):
		password = validated_data.pop('password')
		validated_data['password'] = make_password(password)
		user = User.objects.create(**validated_data)
		return user

	class Meta:
		model = User
		fields = (
			'id', 'username', 'email', 'first_name', 'last_name', 'id',
			'password'
		)
		extra_kwargs = {'password': {'write_only': True}}


class FollowReadSerializer(serializers.ModelSerializer):
	recipes = serializers.SerializerMethodField()
	is_subscribed = serializers.SerializerMethodField()
	recipes_count = serializers.SerializerMethodField()

	class Meta:
		model = User
		fields = (
			'username', 'email', 'first_name', 'last_name', 'id', 'recipes',
			'is_subscribed', 'recipes_count', 'avatar'
		)

	def get_recipes(self, user):
		recipes = user.recipes.all()
		return RecipeShortReadSerializer(recipes, many=True).data

	def get_is_subscribed(self, following):
		request = self.context.get('request')
		return Follow.objects.filter(
			user=request.user, following=following
		).exists()

	def get_recipes_count(self, user):
		return Recipe.objects.filter(author=user).count()


class FollowWriteSerializer(serializers.ModelSerializer):
	class Meta:
		model = Follow
		fields = '__all__'
		validators = [
			UniqueTogetherValidator(
				queryset=Follow.objects.all(),
				fields=('user', 'following'),
				message='Вы уже подписаны на этого пользователя'
			)
		]

	def validate(self, data):
		request = self.context.get('request')
		if request.user == data['following']:
			raise serializers.ValidationError(
				'Вы не можете подписаться на самого себя'
			)
		return data

	def to_representation(self, instance):
		return FollowReadSerializer(
			instance.following, context=self.context
		).data


class FavoriteSerializer(serializers.ModelSerializer):
	class Meta:
		model = Favorite
		fields = '__all__'
		validators = [
			UniqueTogetherValidator(
				queryset=Favorite.objects.all(),
				fields=('user', 'recipe'),
				message='Рецепт уже добавлен в избранное'
			)
		]

	def to_representation(self, instance):
		return RecipeShortReadSerializer(
			instance.recipe,
			context={'request': self.context.get('request')}
		).data


class ShoppingCartSerializer(serializers.ModelSerializer):
	class Meta:
		model = ShoppingCart
		fields = '__all__'
		validators = [
			UniqueTogetherValidator(
				queryset=ShoppingCart.objects.all(),
				fields=('user', 'recipe'),
				message='Рецепт уже добавлен в список покупок'
			)
		]

	def to_representation(self, instance):
		request = self.context.get('request')
		return RecipeShortReadSerializer(
			instance.recipe,
			context={'request': request}
		).data
