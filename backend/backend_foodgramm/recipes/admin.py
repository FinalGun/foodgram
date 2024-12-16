from django.contrib import admin
from django.contrib.admin import display
from django.utils.safestring import mark_safe

from .models import (Favorite, Ingredient, IngredientToRecipe, Recipe,
                     ShoppingCart, Tag, User)


class CookingTimeFilter(admin.SimpleListFilter):
    title = 'Фильтрация по времени готовки'
    parameter_name = 'cooking_time'

    def lookups(self, request, model_admin):
        return [
            ('short', 'Меньше 30 минут'),
            ('medium', 'Между 30 и 60 минутами'),
            ('long', 'Дольше часа'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'short':
            return queryset.filter(cooking_time__lt=30)
        if self.value() == 'medium':
            return queryset.filter(cooking_time__gte=30, cooking_time__lt=60)
        if self.value() == 'long':
            return queryset.filter(cooking_time__gte=60)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'last_name')
    search_fields = ('id', 'username', 'email', 'last_name')


class RecipeIngredientAdmin(admin.StackedInline):
    model = IngredientToRecipe
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
            for recipe_ingredient in recipe.ingredient_to_recipes.all()
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
    list_display = ('pk', 'name', 'measurement_unit', 'in_recipes')
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit',)

    @display(description='Количество использований')
    def in_recipes(self, ingredient):
        return ingredient.recipes.count()


@admin.register(IngredientToRecipe)
class IngredientToRecipeAdmin(admin.ModelAdmin):
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
