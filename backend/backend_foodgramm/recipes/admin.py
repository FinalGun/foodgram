from django.contrib import admin
from django.contrib.admin import display
from django.utils.safestring import mark_safe

from .models import (Favorite, Ingredient, RecipeIngredient, Recipe,
                     ShoppingCart, Tag, User)

COOKING_TIME_UPPER = 60
COOKING_TIME_LOWER = 30


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
    list_display = ('id', 'username', 'email', 'last_name')
    search_fields = ('id', 'username', 'email', 'last_name')


class RecipeIngredientAdmin(admin.StackedInline):
    model = RecipeIngredient
    fields = ('recipe', 'ingredient', 'amount')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'cooking_time',
        'author',
        'get_tags',
        'in_favorites',
        'get_ingredients',
        'get_image'
    )
    list_filter = ('author', 'tags', CookingTimeFilter)
    search_fields = ('name', 'author', 'tags',)
    inlines = (RecipeIngredientAdmin,)

    @display(description='Количество в избранном')
    def in_favorites(self, recipe):
        return recipe.favorites.count()


    @display(description='Продукты')
    def get_ingredients(self, recipe):
        return mark_safe('<br>'.join(
            f'{recipe_ingredient.ingredient} - {recipe_ingredient.amount}'
            f'{recipe_ingredient.ingredient.measurement_unit}'
            for recipe_ingredient in recipe.recipe_ingredient.all()
        ))

    @display(description='Изображение')
    def get_image(self, recipe):
        return mark_safe(f'<img src={recipe.image.url} width="75" height="55"')

    @display(description='Теги')
    def get_tags(self, recipe):
        return mark_safe('<br>'.join(f'{tag}' for tag in
                         recipe.tags.filter(recipes=recipe)))


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'name', 'measurement_unit', 'in_recipes'
    )
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit',)

    @display(description='Количество использований')
    def in_recipes(self, ingredient):
        return ingredient.recipes.count()


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'in_recipes')
    search_fields = ('name', 'slug')

    @display(description='Количество использований')
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
