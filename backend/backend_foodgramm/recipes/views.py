from django.shortcuts import redirect
from rest_framework.response import Response
from rest_framework import status

from recipes.models import Recipe


def redirect_to_recipe(request, recipe_id):
    if Recipe.objects.filter(id=recipe_id).exists():
        return redirect(f'/recipes/{recipe_id}')
    return Response(status=status.HTTP_404_NOT_FOUND)
