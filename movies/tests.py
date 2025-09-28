from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Movie

class MovieModelTest(TestCase):
    def setUp(self):
        self.movie = Movie.objects.create(
            tmdb_id=123,
            title="Test Movie",
            overview="Test overview",
            vote_average=8.5,
            vote_count=1000
        )

    def test_movie_creation(self):
        self.assertEqual(self.movie.title, "Test Movie")
        self.assertEqual(self.movie.vote_average, 8.5)
        self.assertEqual(self.movie.vote_count, 1000)

    def test_movie_str_representation(self):
        self.assertEqual(str(self.movie), "Test Movie")

    def test_full_poster_url(self):
        self.movie.poster_path = "/test.jpg"
        self.assertEqual(
            self.movie.full_poster_url,
            "https://image.tmdb.org/t/p/w500/test.jpg"
        )

    def test_full_backdrop_url(self):
        self.movie.backdrop_path = "/backdrop.jpg"
        self.assertEqual(
            self.movie.full_backdrop_url,
            "https://image.tmdb.org/t/p/w1280/backdrop.jpg"
        )

class MovieAPITest(APITestCase):
    def test_health_endpoint(self):
        response = self.client.get('/api/movies/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'healthy')

    def test_trending_movies_endpoint(self):
        response = self.client.get('/api/movies/trending/')
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE])

    def test_search_movies_without_query(self):
        response = self.client.get('/api/movies/search/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_search_movies_with_query(self):
        response = self.client.get('/api/movies/search/?q=test')
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE])