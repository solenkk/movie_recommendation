import requests
import json
import logging
from django.conf import settings
from django.core.cache import cache
from .models import Movie

logger = logging.getLogger(__name__)

def fetch_movies_from_tmdb(endpoint, params=None):
    """
    Fetch movies from TMDb API with comprehensive error handling
    """
    if params is None:
        params = {}
    
    params['api_key'] = settings.TMDB_API_KEY
    url = f"{settings.TMDB_BASE_URL}/{endpoint}"
    
    try:
        logger.debug(f"Fetching from TMDb: {url} with params: {params}")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        logger.debug(f"Successfully fetched data from TMDb: {endpoint}")
        return data
        
    except requests.exceptions.Timeout:
        logger.error(f"TMDb API timeout: {url}")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(f"TMDb HTTP Error ({e.response.status_code}): {url}")
        logger.error(f"Response content: {e.response.text}")
        return None
    except requests.exceptions.ConnectionError:
        logger.error(f"TMDb Connection Error: Could not connect to {url}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"TMDb Request Error: {e} - URL: {url}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"TMDb JSON Parse Error: {e} - URL: {url}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in fetch_movies_from_tmdb: {e}")
        return None

def get_or_create_movie(tmdb_data):
    """
    Get movie from database or create it from TMDb data with error handling
    """
    try:
        if not tmdb_data or 'id' not in tmdb_data:
            logger.warning("Invalid TMDb data provided to get_or_create_movie")
            return None, False
        
        # Extract genre names if available
        genres = []
        if 'genres' in tmdb_data and tmdb_data['genres']:
            genres = [genre['name'] for genre in tmdb_data.get('genres', [])]
        elif 'genre_ids' in tmdb_data and tmdb_data['genre_ids']:
            genres = tmdb_data.get('genre_ids', [])
        
        # Handle possible None values for date fields
        release_date = tmdb_data.get('release_date')
        if release_date == '':
            release_date = None
        
        movie, created = Movie.objects.get_or_create(
            tmdb_id=tmdb_data['id'],
            defaults={
                'title': tmdb_data.get('title', 'Unknown Title'),
                'overview': tmdb_data.get('overview', ''),
                'release_date': release_date,
                'poster_path': tmdb_data.get('poster_path'),
                'backdrop_path': tmdb_data.get('backdrop_path'),
                'vote_average': tmdb_data.get('vote_average', 0.0),
                'vote_count': tmdb_data.get('vote_count', 0),
                'genres': genres
            }
        )
        
        if created:
            logger.info(f"Created new movie: {movie.title} (ID: {movie.tmdb_id})")
        else:
            logger.debug(f"Found existing movie: {movie.title} (ID: {movie.tmdb_id})")
            
        return movie, created
        
    except KeyError as e:
        logger.error(f"Missing key in TMDb data: {e} - Data: {tmdb_data}")
        return None, False
    except ValueError as e:
        logger.error(f"Data conversion error: {e} - Data: {tmdb_data}")
        return None, False
    except Exception as e:
        logger.error(f"Unexpected error in get_or_create_movie: {e} - Data: {tmdb_data}")
        return None, False

def get_movie_details(movie_id):
    """Get detailed information about a specific movie"""
    logger.debug(f"Fetching details for movie ID: {movie_id}")
    return fetch_movies_from_tmdb(f'movie/{movie_id}')

def get_movie_credits(movie_id):
    """Get cast and crew information for a movie"""
    logger.debug(f"Fetching credits for movie ID: {movie_id}")
    return fetch_movies_from_tmdb(f'movie/{movie_id}/credits')

def get_popular_movies():
    """Get popular movies from TMDb"""
    logger.debug("Fetching popular movies from TMDb")
    return fetch_movies_from_tmdb('movie/popular')

def get_top_rated_movies():
    """Get top rated movies from TMDb"""
    logger.debug("Fetching top rated movies from TMDb")
    return fetch_movies_from_tmdb('movie/top_rated')

def get_upcoming_movies():
    """Get upcoming movies from TMDb"""
    logger.debug("Fetching upcoming movies from TMDb")
    return fetch_movies_from_tmdb('movie/upcoming')

def get_movies_by_genre(genre_id):
    """Get movies by genre ID"""
    logger.debug(f"Fetching movies for genre ID: {genre_id}")
    return fetch_movies_from_tmdb('discover/movie', {'with_genres': genre_id})

def get_similar_movies(movie_id):
    """Get movies similar to the specified movie"""
    logger.debug(f"Fetching similar movies for movie ID: {movie_id}")
    return fetch_movies_from_tmdb(f'movie/{movie_id}/similar')

def search_movies_by_keyword(keyword, page=1):
    """Search movies by keyword with pagination"""
    logger.debug(f"Searching movies with keyword: {keyword}, page: {page}")
    return fetch_movies_from_tmdb('search/movie', {'query': keyword, 'page': page})

def get_movies_by_year(year):
    """Get movies released in a specific year"""
    logger.debug(f"Fetching movies from year: {year}")
    return fetch_movies_from_tmdb('discover/movie', {'year': year})

def get_now_playing_movies():
    """Get movies currently playing in theaters"""
    logger.debug("Fetching now playing movies from TMDb")
    return fetch_movies_from_tmdb('movie/now_playing')

def get_movie_recommendations(movie_id):
    """Get movie recommendations based on a movie"""
    logger.debug(f"Fetching recommendations for movie ID: {movie_id}")
    return fetch_movies_from_tmdb(f'movie/{movie_id}/recommendations')