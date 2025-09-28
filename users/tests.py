from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from .models import UserProfile

class UserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_user_profile_creation(self):
        """Test that user profile is created when user is created"""
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.user.username, 'testuser')

    def test_user_profile_str(self):
        """Test string representation of user profile"""
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(str(profile), "testuser's Profile")

class UserAPITest(APITestCase):
    def test_user_registration(self):
        """Test user registration API"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123'
        }
        response = self.client.post('/api/auth/register/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_user_login(self):
        """Test user login API"""
        User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post('/api/auth/login/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)