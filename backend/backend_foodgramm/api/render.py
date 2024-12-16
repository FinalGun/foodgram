from datetime import date


def render_shopping_list(ingredients, recipes):
    return ''.join([
        f'Список покупок. {date.today()}',
        '\nПродукты:',
        ''.join([(
            f'\n{list(ingredients).index(ingredient) + 1}'
            f'.{ingredient["ingredient__name"].capitalize()}'
            f' - {ingredient["ingredient_amount"]},'
            f' {ingredient["ingredient__measurement_unit"]}'
        ) for ingredient in ingredients]),
        '\nРецепты:',
        ''.join([
            f'\n{list(recipes).index(recipe) + 1}'
            f'.{recipe.recipe.name.capitalize()}'
            for recipe in recipes])
    ])
