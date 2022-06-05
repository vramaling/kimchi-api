"""Tests for ingredients API"""
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from core.models import (
    Ingredient,
    Recipe,
)
from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')


def detail_url(ingredient_id):
    """Create and return ingredient detail URL"""
    return reverse('recipe:ingredient-detail', args=[ingredient_id])


def create_user(email='user@example.com', password='pass12345'):
    """Create and return user"""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicIngredientsAPITest(TestCase):
    """Test unauthorized API requests"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrieving ingredients"""
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsAPITest(TestCase):
    """Test authenticated API requests"""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        """Test retrieving a list of ingredients"""
        Ingredient.objects.create(user=self.user, name='Paneer')
        Ingredient.objects.create(user=self.user, name='Yoghurt')

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """Test list ingred limited to authorized users"""
        user2 = create_user(email='testuser@example.com')
        Ingredient.objects.create(user=user2, name='Pepper')
        ingredient = Ingredient.objects.create(
            user=self.user,
            name='Coriander'
        )

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)
        self.assertEqual(res.data[0]['id'], ingredient.id)

    def test_update_ingredient(self):
        """Test updating ingredient"""
        ingredient = Ingredient.objects.create(
            user=self.user,
            name='Avocado'
        )

        payload = {'name': 'Tomato'}
        url = detail_url(ingredient.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload['name'])

    def test_delete_ingredient(self):
        """Test deleting ingredient"""
        ingredient = Ingredient.objects.create(
            user=self.user,
            name='Pork'
        )
        url = detail_url(ingredient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        ingredients = Ingredient.objects.filter(user=self.user)
        self.assertFalse(ingredients.exists())

    def test_filter_ingred_assigned_to_recipes(self):
        """Test listing ingredients that are assigned to recipes"""
        ingred1 = Ingredient.objects.create(user=self.user, name='Banana')
        ingred2 = Ingredient.objects.create(user=self.user, name='Yoghurt')
        recipe = Recipe.objects.create(
            title='Fruit Salad',
            time_minutes=10,
            price=Decimal('10.40'),
            user=self.user,
        )
        recipe.ingredients.add(ingred1)
        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        s1 = IngredientSerializer(ingred1)
        s2 = IngredientSerializer(ingred2)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_ingred_unique(self):
        """Test filtered ingredients return unique list"""
        ingred = Ingredient.objects.create(user=self.user, name='Lentils')
        Ingredient.objects.create(user=self.user, name='Chili')
        recipe1 = Recipe.objects.create(
            title='Bread with Lentils',
            time_minutes=75,
            price=Decimal('14.55'),
            user=self.user,
        )
        recipe2 = Recipe.objects.create(
            title='Lentil Curry',
            time_minutes=60,
            price=Decimal('15.45'),
            user=self.user,
        )
        recipe1.ingredients.add(ingred)
        recipe2.ingredients.add(ingred)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})
        self.assertEqual(len(res.data), 1)
