from django.urls import path
from . import views

urlpatterns = [
    # Health and utility endpoints
    path('health/', views.health_check, name='health-check'),
    
    # Movie discovery endpoints
    path('trending/', views.get_trending_movies, name='trending-movies'),
    path('popular/', views.get_popular_movies, name='popular-movies'),
    path('top-rated/', views.get_top_rated_movies, name='top-rated-movies'),
    path('upcoming/', views.get_upcoming_movies, name='upcoming-movies'),
    
    # Search endpoint
    path('search/', views.search_movies, name='search-movies'),
    
    # Movie detail endpoints
    path('movie/<int:movie_id>/', views.get_movie_details, name='movie-details'),
    path('movie/<int:movie_id>/credits/', views.get_movie_credits_view, name='movie-credits'),
    path('movie/<int:movie_id>/similar/', views.get_similar_movies_view, name='similar-movies'),
    
    # User favorites endpoints (require authentication)
    path('favorites/', views.get_favorite_movies, name='favorite-movies'),
    path('favorites/<int:movie_id>/', views.toggle_favorite_movie, name='toggle-favorite'),
]