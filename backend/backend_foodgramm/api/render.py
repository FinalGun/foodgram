from datetime import date

WORKPIECE_INGREDIENTS = ' {index}.{name} - {amount}, {measurement_unit}'
WORKPIECE_RECIPES = ' {index}.{name}'


def render_shopping_list(ingredients, recipes):
    return '\n'.join((
        f'Список покупок. {date.today()}',
        'Продукты:',
        *(WORKPIECE_INGREDIENTS.format(
            index=index,
            name=ingredient['ingredient__name'].capitalize(),
            amount=ingredient['ingredient_amount'],
            measurement_unit=ingredient['ingredient__measurement_unit']
        ) for index, ingredient in enumerate(ingredients, start=1)),
        'Рецепты:',
        *(WORKPIECE_RECIPES.format(
            index=index, name=recipe.recipe.name
        ) for index, recipe in enumerate(recipes, start=1))
    ))
