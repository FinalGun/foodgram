import json
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import BaseCommand

from recipes.models import Ingredient

User = get_user_model()


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        count = Ingredient.objects.count()
        file_path = os.path.join(settings.IMPORTING_FILES_DIR,
                                 'ingredients.json')
        with open(file_path, mode='r', encoding='utf-8') as file:
            Ingredient.objects.bulk_create(
                (Ingredient(**row) for row in json.load(file)),
                ignore_conflicts=True
            )
        print(f'Успешно загружены продукты из {file_path}. '
              f'Количеcтво новых: {Ingredient.objects.count() - count}')
