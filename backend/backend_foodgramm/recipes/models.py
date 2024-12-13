import re

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

MAX_LENGTH_USERNAME = 150
MAX_LENGTH_EMAIL = 150
MAX_LENGTH_FIRST_NAME = 150
MAX_LENGTH_LAST_NAME = 150
USERNAME_VALIDATION_REGEX = r'[\w.@+-]'


def validate_username(username):
	if username == settings.CURRENT_USER_IDENTIFIER:
		raise ValidationError(
			f'Нельзя использовать имя {settings.CURRENT_USER_IDENTIFIER}'
		)
	forbidden_characters = re.sub(USERNAME_VALIDATION_REGEX, '', username)
	if forbidden_characters:
		raise ValidationError(
			f'Имя пользователя содержит недопустимые символы: '
			f'{"".join(set(forbidden_characters))}.'
		)

	return username


class User(AbstractUser):
	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = ('first_name', 'last_name', 'username')
	username = models.CharField(
		'Логин',
		unique=True, validators=[validate_username],
		max_length=MAX_LENGTH_USERNAME
	)
	email = models.EmailField(
		'Почта', max_length=MAX_LENGTH_EMAIL, unique=True
	)
	first_name = models.CharField(
		'Имя', max_length=MAX_LENGTH_FIRST_NAME
	)
	last_name = models.CharField(
		'Фамилия', max_length=MAX_LENGTH_LAST_NAME
	)
	avatar = models.ImageField(
		verbose_name='Аватар', upload_to='users',
		blank=True,
		null=True,
	)


class BaseModel(models.Model):
	class Meta:
		abstract = True
		default_related_name = "%(class)ss"


class Tag(models.Model):
	name = models.CharField(max_length=100, unique=True)
	slug = models.SlugField(max_length=100, unique=True)

	class Meta:
		verbose_name = 'Тег'
		verbose_name_plural = 'Теги'
		ordering = ('name',)


class Ingredient(models.Model):
	name = models.CharField(max_length=100, verbose_name='Название')
	measurement_unit = models.CharField(
		max_length=100, verbose_name='Единица измерения'
	)

	class Meta:
		verbose_name = 'Ингредиент'
		verbose_name_plural = 'Ингредиенты'
		ordering = ('name',)


class Recipe(models.Model):
	author = models.ForeignKey(
		User,
		on_delete=models.CASCADE,
		verbose_name='Автор',
		related_name='recipes'
	)
	name = models.CharField(max_length=100)
	image = models.ImageField(
		upload_to='recipes',
		verbose_name='Изображение',
		blank=True,
	)
	text = models.TextField(max_length=250, verbose_name='Описание')
	ingredients = models.ManyToManyField(
		Ingredient,
		through='IngredientToRecipe',
		verbose_name='Ингредиенты',
	)
	tags = models.ManyToManyField(
		Tag,
		verbose_name='Теги',
	)
	cooking_time = models.PositiveIntegerField(
		verbose_name='Время приготовления',
	)

	class Meta:
		verbose_name = 'Рецепт'
		verbose_name_plural = 'Рецепты'
		ordering = ('name',)


class IngredientToRecipe(models.Model):
	recipe = models.ForeignKey(
		Recipe,
		on_delete=models.CASCADE,
		related_name='ingredient_to_recipes',
	)
	ingredient = models.ForeignKey(
		Ingredient,
		on_delete=models.CASCADE,
		related_name='ingredient_to_recipes',
	)
	amount = models.PositiveIntegerField(
		verbose_name='Количество ингредиентов',
		validators=(MinValueValidator(1),)
	)


class Follow(BaseModel):
	user = models.ForeignKey(
		User, on_delete=models.CASCADE, related_name='follower'
	)
	following = models.ForeignKey(
		User, on_delete=models.CASCADE, related_name='following'
	)

	class Meta:
		verbose_name = 'Подписка'
		verbose_name_plural = 'Подписки'
		ordering = ('following',)
		constraints = [
			models.UniqueConstraint(
				fields=['user', 'following'],
				name='unique_user_following'
			)
		]


class Favorite(BaseModel):
	user = models.ForeignKey(
		User,
		on_delete=models.CASCADE, verbose_name='Пользователь',
		related_name='favorites'
	)
	recipe = models.ForeignKey(
		Recipe,
		on_delete=models.CASCADE, verbose_name='Рецепт',
		related_name='favorites'
	)

	class Meta:
		verbose_name = 'Избранное'
		verbose_name_plural = 'Избранное'
		ordering = ('recipe',)
		constraints = [
			models.UniqueConstraint(
				fields=['user', 'recipe'],
				name='unique_user_recipe'
			)
		]


class ShoppingCart(models.Model):
	user = models.ForeignKey(
		User,
		on_delete=models.CASCADE,
		related_name='shoppingCart',
		verbose_name='Пользователь'
	)
	recipe = models.ForeignKey(
		Recipe,
		on_delete=models.CASCADE,
		related_name='shoppingCart',
		verbose_name='Рецепт'
	)

	class Meta:
		ordering = ('recipe',)
		constraints = [
			models.UniqueConstraint(
				fields=['user', 'recipe'],
				name='unique_user_recipe_cart'
			)
		]
		verbose_name = 'Список покупок'
		verbose_name_plural = 'Списки покупок'
