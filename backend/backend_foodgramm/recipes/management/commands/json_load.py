import json
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import BaseCommand

from recipes.models import Ingredients, Tag

User = get_user_model()

file_model = [
    {'file_name': 'ingredients.json',
     'model': Ingredients},
    {'file_name': 'tags.json',
     'model': Tag}
]


class Command(BaseCommand):

    def load_data(self, file_name, model):
        file_path = os.path.join(settings.IMPORTING_FILES_DIR,
                                 file_name)
        with open(file_path, mode='r', encoding='utf-8') as file:
            model.objects.bulk_create(
                (model(**row) for row in json.load(file)),
                ignore_conflicts=True
            )
        print(f'Успешно загружены данные из {file_path}')

    def handle(self, *args, **kwargs):
        for args in file_model:
            self.load_data(**args)
