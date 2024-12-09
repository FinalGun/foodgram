#!-*-coding:utf-8-*-
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from recipes.models import Recipe, Tag, Ingredient

User = get_user_model()


class CommonTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='lauren', email='l@l.ru')
        token, _ = Token.objects.get_or_create(user=cls.user)

        cls.client_auth = APIClient()
        cls.client_auth.force_authenticate(user=cls.user,
                                           token=cls.user.auth_token)

        cls.client_unauth = APIClient()

        cls.tag = Tag.objects.create(name='dinner', slug='dinner')
        cls.ingredient = Ingredient.objects.create(
            name='salt',
            measurement_unit='gr',
        )
        cls.recipe = Recipe.objects.create(
            name='honey', cooking_time=22, author=cls.user)


class RecipeTestCase(CommonTestCase):

    def test_get_recipes(self):
        """Список рецептов."""
        url = reverse('api:recipes-list')

        resp = self.client_auth.get(url)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        item = resp.data.get('results')[0]
        self.assertEqual(item.get('id'), self.recipe.id)

    def test_get_recipe(self):
        """Получить рецепт."""
        url = reverse('api:recipes-detail', args=(self.recipe.id,))

        resp = self.client_auth.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data.get('id'), self.recipe.id)

    def test_create_recipe(self):
        url = reverse('api:recipes-list')
        data = {
            'name': 'Медовуха',
            'text': 'Сварить',
            'tags': [self.tag.pk],
            'author': self.user.pk,
            'cooking_time': '5',
            'ingredients': [
                {'id': self.ingredient.pk, 'amount': '0'},
            ],
        }

        resp = self.client_auth.post(url, data=data, format='json')

        print(resp.data)

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Recipe.objects.filter(pk=resp.data.get('id')).exists())

    def test_get_short_link(self):
        """Получение короткой ссылки и ее использование."""
        url = reverse('api:recipes-get-link', args=(self.recipe.pk,))

        resp = self.client_auth.get(url)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        link = resp.json().get('short-link')
        self.assertIn(self.recipe.slug, link)

    def test_go_short_link(self):
        """Проверка работы короткой ссылки."""
        url = reverse('get_recipe_by_slug', args=(self.recipe.slug,))

        resp = self.client_auth.get(url)

        redirect_url = reverse('api:recipes-detail', args=(self.recipe.pk,))
        self.assertRedirects(resp, expected_url=redirect_url)


class UsersApiTestCase(CommonTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.author = User.objects.create(username='Guido', email='g@g.ru')

    def test_list_auth(self):
        url = reverse('users-list')

        resp = self.client_auth.get(url)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_list_unauth(self):
        url = reverse('users-list')

        resp = self.client_unauth.get(url)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
