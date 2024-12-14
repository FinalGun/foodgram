from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404

from recipes.models import Recipe


def redirect_to_recipe(request, recipe_id):
	get_object_or_404(Recipe, id=recipe_id)
	return HttpResponseRedirect(
		f'/recipes/{recipe_id}'
	)
