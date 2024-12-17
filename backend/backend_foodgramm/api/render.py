from datetime import date

workpiece_ingredients = '\n{index}.{name} - {amount}, {measurement_unit}'
workpiece_recipes = '\n{index}.{name}'


def render_shopping_list(ingredients, recipes):
    return [
        f'Список покупок. {date.today()}',
        '\nПродукты:',
        ''.join(workpiece_ingredients.format(
            index=index,
            name=ingredient['ingredient__name'].capitalize(),
            amount=ingredient['ingredient_amount'],
            measurement_unit=ingredient['ingredient__measurement_unit']
        ) for index, ingredient in enumerate(ingredients, start=1)),
        '\nРецепты:',
        ''.join(workpiece_recipes.format(
            index=index, name=recipe.recipe.name
        ) for index, recipe in enumerate(recipes, start=1))
    ]
