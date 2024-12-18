import json
import os

from django.conf import settings
from django.core.management import BaseCommand


class LoadBase(BaseCommand):

    def handle(self, *args, **kwargs):
        file_path = os.path.join(settings.IMPORTING_FILES_DIR, self.file_name)
        with open(file_path, mode='r', encoding='utf-8') as file:
            new_objects = self.model.objects.bulk_create(
                (self.model(**row) for row in json.load(file)),
                ignore_conflicts=True,
            )
        print(
            f'Успешно загружены {self.name} из {file_path}. '
            f'Количеcтво новых: {len(new_objects)}'
        )
