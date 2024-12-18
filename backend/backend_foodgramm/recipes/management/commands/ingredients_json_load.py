from recipes.management.load_base import LoadBase
from recipes.models import Ingredient


class Command(LoadBase):
    file_name = 'ingredients.json'
    model = Ingredient
    name = 'продукты'
