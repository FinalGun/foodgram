import re

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import UniqueConstraint

MAX_LENGTH_USERNAME = 150
MAX_LENGTH_EMAIL = 254
MAX_LENGTH_FIRST_NAME = 150
MAX_LENGTH_LAST_NAME = 150
MAX_LENGTH_INGREDIENT_NAME = 128
MAX_LENGTH_TEXT = 200
MAX_LENGTH_TAG_NAME = 32
MAX_LENGTH_SLUG = 32
MIN_AMOUNT = 1
MIN_COOKING_TIME = 1
MAX_LENGTH_MEASUREMENT_UNIT = 64
USERNAME_VALIDATION_REGEX = r'[\w.@+-]'


def validate_username(username):
    forbidden_characters = re.sub(USERNAME_VALIDATION_REGEX, '', username)
    if forbidden_characters:
        raise ValidationError(
            'Имя пользователя содержит недопустимые символы: {}'.format(
               *(symbol for symbol in (set(forbidden_characters)))
            )
        )

    return username


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('first_name', 'last_name', 'username')
    username = models.CharField(
        'Логин',
        unique=True,
        validators=[validate_username],
        max_length=MAX_LENGTH_USERNAME,
    )
    email = models.EmailField(
        'Почта', max_length=MAX_LENGTH_EMAIL, unique=True
    )
    first_name = models.CharField('Имя', max_length=MAX_LENGTH_FIRST_NAME)
    last_name = models.CharField('Фамилия', max_length=MAX_LENGTH_LAST_NAME)
    avatar = models.ImageField(
        verbose_name='Аватар',
        upload_to="users",
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('email', )


class Tag(models.Model):
    name = models.CharField(
        max_length=MAX_LENGTH_TAG_NAME,
        unique=True,
        verbose_name='Тэг',
    )
    slug = models.SlugField(
        max_length=MAX_LENGTH_SLUG,
        unique=True,
        verbose_name='Слаг'
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=MAX_LENGTH_INGREDIENT_NAME, verbose_name='Название'
    )
    measurement_unit = models.CharField(
        max_length=MAX_LENGTH_MEASUREMENT_UNIT,
        verbose_name='Единица измерения',
    )

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
        ordering = ('name',)
        constraints = (
            UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_name_and_measurement_unit',
            ),
        )

    def __str__(self):
        return f'{self.name} {self.measurement_unit}'


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='recipes',
    )
    name = models.CharField(max_length=MAX_LENGTH_INGREDIENT_NAME)
    image = models.ImageField(
        upload_to='recipes',
        verbose_name='Изображение',
        blank=True,
    )
    text = models.TextField(
        max_length=MAX_LENGTH_TEXT, verbose_name='Описание'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Продукты',
        related_name='recipes',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
        related_name='recipes',
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время (мин)',
        validators=(MinValueValidator(MIN_COOKING_TIME),)
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Время создания рецепта'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-created_at',)

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='recipe_ingredients',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Продукт',
        related_name='recipe_ingredients',
    )
    amount = models.PositiveIntegerField(
        verbose_name='Мера',
        validators=(MinValueValidator(MIN_AMOUNT),),
    )

    class Meta:
        verbose_name = 'Продукт в рецепте'
        verbose_name_plural = 'Продукты в рецептах'
        ordering = ('ingredient',)


class Follow(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='follows'
    )
    following = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='authors'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('following',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following'], name='unique_user_following'
            )
        ]


class BaseModelUserRecipe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        abstract = True
        ordering = ('recipe',)
        default_related_name = '%(class)ss'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_user_recipe_%(class)ss'
            )
        ]


class Favorite(BaseModelUserRecipe):

    class Meta(BaseModelUserRecipe.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'


class ShoppingCart(BaseModelUserRecipe):

    class Meta(BaseModelUserRecipe.Meta):
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
