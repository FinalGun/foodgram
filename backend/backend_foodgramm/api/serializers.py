import base64
from collections import Counter

from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers

from recipes.models import (Favorite, Follow, Ingredient, IngredientToRecipe,
                            MIN_VALUE_AMOUNT, MIN_VALUE_COOKING_TIME, Recipe,
                            ShoppingCart, Tag, User)


class UserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, following):
        request = self.context.get('request')
        return request.user.is_authenticated and Follow.objects.filter(
                user=request.user, following=following
            ).exists()

    class Meta:
        model = User
        fields = (*DjoserUserSerializer.Meta.fields, 'is_subscribed', 'avatar')


class Base64imageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image/'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name=f'avatar.{ext}')
        return super().to_internal_value(data)


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64imageField(allow_null=True)

    class Meta:
        model = User
        fields = ('avatar',)


class IngredientsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientToRecipeReadSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True, source='ingredient.id')
    name = serializers.CharField(read_only=True, source='ingredient.name')
    measurement_unit = serializers.CharField(
        read_only=True, source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientToRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = fields


class IngredientWriteSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(
        validators=[MinValueValidator(MIN_VALUE_AMOUNT),]
    )

    class Meta:
        model = IngredientToRecipe
        fields = ('id', 'amount')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class ResipesReadSerializer(serializers.ModelSerializer):
    author = UserSerializer()
    ingredients = IngredientToRecipeReadSerializer(
        many=True, read_only=True, source='ingredient_to_recipes'
    )
    tags = TagSerializer(many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'image',
            'author',
            'ingredients',
            'name',
            'text',
            'cooking_time',
            'is_favorited',
            'is_in_shopping_cart',
        )

    @staticmethod
    def object_exists(model, request, recipe):
        return (
            request
            and request.user.is_authenticated
            and model.objects.filter(user=request.user, recipe=recipe).exists()
        )

    def get_is_favorited(self, recipe):
        return self.object_exists(
            Favorite,
            self.context.get('request'),
            recipe
        )

    def get_is_in_shopping_cart(self, recipe):
        return self.object_exists(
            ShoppingCart,
            self.context.get('request'),
            recipe
        )


class RecipeShortReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'cooking_time', 'image')


class ResipeWriteSerializer(serializers.ModelSerializer):
    ingredients = IngredientWriteSerializer(
        many=True,
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    image = Base64imageField()
    cooking_time = serializers.IntegerField(
        validators=[MinValueValidator(MIN_VALUE_COOKING_TIME),]
    )

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'name',
            'text',
            'cooking_time',
            'image',
        )

    def validate(self, data):
        self.validate_tags_ingredients(
            [ingredient['id'] for ingredient in data.get('ingredients')],
            'Продукты'
        )
        self.validate_tags_ingredients(data.get('tags'), 'Теги')
        return data

    @staticmethod
    def validate_tags_ingredients(objects, message):
        if not objects:
            raise serializers.ValidationError(f'{message} не указаны')
        if len(objects) != len(set(objects)):
            double = [
                object.id
                for object in objects if Counter(objects)[object] != 1
            ]
            raise serializers.ValidationError(
                f'{message} {set(double)} не должны повторяться'
            )

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        validated_data.update({'author': self.context.get('request').user})
        recipe = super().create(validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients)
        return recipe

    @staticmethod
    def create_ingredients(recipe, ingredients):
        IngredientToRecipe.objects.bulk_create(
            [
                IngredientToRecipe(
                    recipe=recipe,
                    ingredient=ingredient['id'],
                    amount=ingredient.get('amount'),
                ) for ingredient in ingredients
            ]
        )

    def update(self, instance, validated_data):
        instance.tags.clear()
        instance.ingredients.clear()
        self.create_ingredients(instance, validated_data.pop('ingredients'))
        instance.tags.set(validated_data.pop('tags'))
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return ResipesReadSerializer(instance, context=self.context).data


class FollowReadSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (*UserSerializer.Meta.fields, 'recipes', 'recipes_count',)
        read_only_fields = fields

    def get_recipes(self, user):
        request = self.context.get('request')
        return RecipeShortReadSerializer(
            user.recipes.all()[:int(request.GET.get('recipes_limit', 10))],
            many=True,
            read_only=True
        ).data

    @staticmethod
    def get_recipes_count(user):
        return user.recipes.count()
