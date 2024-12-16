import os
from csv import DictReader

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Tag


class Command(BaseCommand):

    def handle(self, *args, **options):
        with open(
                os.path.join(settings.BASE_DIR, 'data/tags.csv'),
                'r',
                encoding='utf-8'
        ) as file:
            tags = [
                Tag(
                    name=row['name'], slug=row['slug']
                )
                for row in DictReader(
                    file, fieldnames=('name', 'slug',)
                )
            ]
            Tag.objects.bulk_create(tags, ignore_conflicts=True)
            print('Тэги загружены')