from recipes.management.load_base import LoadBase
from recipes.models import Tag


class Command(LoadBase):
    file_name = 'tags.json'
    model = Tag
    name = 'теги'
