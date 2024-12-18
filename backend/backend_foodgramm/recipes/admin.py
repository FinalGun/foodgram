from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.admin import display
from django.utils.safestring import mark_safe

from .models import (
    Favorite, Ingredient, RecipeIngredient, Recipe,
    ShoppingCart, Tag, User
)

COOKING_TIME_UPPER = 60
COOKING_TIME_LOWER = 30

admin.site.unregister(Group)


class UserFilter(admin.SimpleListFilter):
    title = 'Фильтрация рецептам, подпискам и подписчикам'
    parameter_name = 'user'

    def lookups(self, request, model_admin):
        return [
            ('recipes', 'Есть рецепты'),
            ('authors', 'Есть подписчики'),
            ('follows', 'Есть подписки'),
        ]

    def queryset(self, request, queryset):
        value = self.value()
        if not value:
            return queryset
        if value == 'recipes':
            return queryset.filter(recipes__gt=0)
        if value == 'authors':
            return queryset.filter(authors__gt=0)
        return queryset.filter(follows__gt=0)


class CookingTimeFilter(admin.SimpleListFilter):
    title = 'Фильтрация по времени готовки'
    parameter_name = 'cooking_time'

    def lookups(self, request, model_admin):
        return [
            (f'0:{COOKING_TIME_LOWER}', f'Меньше {COOKING_TIME_LOWER} минут'),
            (f'{COOKING_TIME_LOWER}:{COOKING_TIME_UPPER}',
             f'Между {COOKING_TIME_LOWER} и {COOKING_TIME_UPPER} минутами'),
            (f'{COOKING_TIME_UPPER}:{10**10}',
             f'Дольше {COOKING_TIME_UPPER} минут'),
        ]

    def queryset(self, request, queryset):
        value = self.value()
        if not value:
            return queryset
        lower, upper = value.split(':')
        return queryset.filter(cooking_time__range=(int(lower), int(upper)))


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'username', 'full_name', 'email', 'avatar_display',
        'recipes_count', 'subscriptions_count', 'subscribers_count'
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = (
        'is_staff', 'is_active', UserFilter
    )

    @admin.display(description='Имя Фамилия')
    def full_name(self, user):
        return f'{user.first_name} {user.last_name}'

    @admin.display(description='Аватар')
    def avatar_display(self, user):
        if not user.avatar:
            return 'Нет аватара'
        return mark_safe(
            f'<img src="{user.avatar.url}" '
            f'style="max-width: 75px; max-height: 55px;" />'
        )

    @admin.display(description='Рецепты')
    def recipes_count(self, user):
        return user.recipes.count()

    @admin.display(description='Подписки')
    def subscriptions_count(self, user):
        return user.follows.count()

    @admin.display(description='Подписчики')
    def subscribers_count(self, user):
        return user.authors.count()


class RecipeIngredientAdmin(admin.StackedInline):
    model = RecipeIngredient
    fields = ('recipe', 'ingredient', 'amount')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'cooking_time',
        'get_author',
        'get_tags',
        'in_favorites',
        'get_ingredients',
        'get_image'
    )
    list_filter = ('author', 'tags', CookingTimeFilter)
    search_fields = ('name', 'get_author', 'tags',)
    inlines = (RecipeIngredientAdmin,)

    @display(description='Автор')
    def get_author(self, recipe):
        return recipe.author.username

    @display(description='В избранном')
    def in_favorites(self, recipe):
        return recipe.favorites.count()

    @display(description='Продукты')
    def get_ingredients(self, recipe):
        return mark_safe('<br>'.join(
            f'{recipe_ingredient.ingredient} - {recipe_ingredient.amount}'
            f'{recipe_ingredient.ingredient.measurement_unit}'
            for recipe_ingredient in recipe.recipe_ingredients.all()
        ))

    @display(description='Изображение')
    def get_image(self, recipe):
        return mark_safe(f'<img src={recipe.image.url} width="75" height="55"')

    @display(description='Теги')
    def get_tags(self, recipe):
        return mark_safe('<br>'.join(f'{tag}' for tag in
                         recipe.tags.all()))


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'name', 'measurement_unit', 'in_recipes'
    )
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit',)

    @display(description='Использований')
    def in_recipes(self, ingredient):
        return ingredient.recipes.count()


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'in_recipes')
    search_fields = ('name', 'slug')

    @display(description='Использований')
    def in_recipes(self, tag):
        return tag.recipes.count()


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user', 'recipe')
