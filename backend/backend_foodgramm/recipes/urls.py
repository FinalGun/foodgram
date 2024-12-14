from django.urls import path
from recipes.views import redirect_to_recipe

urlpatterns = [
    path('<int:recipe_id>', redirect_to_recipe),
]
