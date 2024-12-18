import json
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import BaseCommand

from recipes.models import Tag

User = get_user_model()


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        count = Tag.objects.count()
        file_path = os.path.join(
            settings.IMPORTING_FILES_DIR,
            'tags.json'
        )
        with open(file_path, mode='r', encoding='utf-8') as file:
            Tag.objects.bulk_create(
                (Tag(**row) for row in json.load(file)),
                ignore_conflicts=True
            )
        print(f'Успешно загружены теги из {file_path}. '
              f'Количеcтво: {Tag.objects.count() - count}')
