from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response

from recipes.models import Recipe


def add_or_remove_favorite_or_shopping_cart(
    model, recipe_id, serializer_class, request
):
    obj = get_object_or_404(Recipe, pk=recipe_id)
    if request.method == 'POST':
        serializer = serializer_class(
            data={'user': request.user.id, 'recipe': obj.id},
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    if not model.objects.filter(user=request.user, recipe=obj).exists():
        return Response(
            {'error': 'Рецепт отсутствует в списке'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    model.objects.filter(user=request.user, recipe=obj).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
