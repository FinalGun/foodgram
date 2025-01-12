from django.shortcuts import redirect
from rest_framework.serializers import ValidationError

from recipes.models import Recipe


def redirect_to_recipe(request, recipe_id):
    if Recipe.objects.filter(id=recipe_id).exists():
        return redirect(f'/recipes/{recipe_id}')
    raise ValidationError(f'Рецепта с id={recipe_id} не существует.')
