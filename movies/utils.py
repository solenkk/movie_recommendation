import requests
import json
import logging
from datetime import datetime
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
        response = requests.get(url, params=params, timeout=30)  # Increased timeout for production
        response.raise_for_status()
        
        data = response.json()
        logger.debug(f"Successfully fetched data from TMDb: {endpoint}")
        return data
        
    except requests.exceptions.Timeout:
        logger.error(f"TMDb API timeout: {url}")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(f"TMDb HTTP Error ({e.response.status_code}): {url}")
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
    Get movie from database or create it from TMDb data with enhanced error handling
    """
    try:
        if not tmdb_data or 'id' not in tmdb_data:
            logger.warning("Invalid TMDb data provided to get_or_create_movie")
            return None, False
        
        tmdb_id = tmdb_data['id']
        movie_title = tmdb_data.get('title') or tmdb_data.get('original_title', 'Unknown Title')
        
        # Extract all possible fields with safe defaults
        title = tmdb_data.get('title') or tmdb_data.get('original_title', 'Unknown Title')
        overview = tmdb_data.get('overview', '')
        
        # Handle release_date - could be None, empty string, or invalid format
        release_date_str = tmdb_data.get('release_date')
        release_date = None
        if release_date_str and release_date_str.strip():
            try:
                release_date = datetime.strptime(release_date_str, '%Y-%m-%d').date()
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid release date '{release_date_str}' for movie '{title}': {e}")
                release_date = None
        
        # Handle genres - could be list of objects or list of IDs
        genres = []
        if 'genres' in tmdb_data and tmdb_data['genres']:
            # Full genre objects: [{"id": 28, "name": "Action"}]
            genres = [genre['name'] for genre in tmdb_data['genres'] if isinstance(genre, dict) and 'name' in genre]
        elif 'genre_ids' in tmdb_data and tmdb_data['genre_ids']:
            # Just genre IDs: [28, 12]
            genres = tmdb_data['genre_ids']
        
        # Handle vote_average - ensure it's a float
        vote_average = tmdb_data.get('vote_average', 0.0)
        try:
            vote_average = float(vote_average) if vote_average is not None else 0.0
        except (TypeError, ValueError):
            vote_average = 0.0
        
        # Handle vote_count - ensure it's an integer
        vote_count = tmdb_data.get('vote_count', 0)
        try:
            vote_count = int(vote_count) if vote_count is not None else 0
        except (TypeError, ValueError):
            vote_count = 0
        
        # Create movie with comprehensive data handling
        movie, created = Movie.objects.get_or_create(
            tmdb_id=tmdb_id,
            defaults={
                'title': title[:255],  # Ensure it doesn't exceed max_length
                'overview': overview,
                'release_date': release_date,
                'poster_path': tmdb_data.get('poster_path'),
                'backdrop_path': tmdb_data.get('backdrop_path'),
                'vote_average': vote_average,
                'vote_count': vote_count,
                'genres': genres
            }
        )
        
        if created:
            logger.info(f"✅ Created new movie: {title} (TMDb ID: {tmdb_id})")
        else:
            logger.debug(f"✅ Found existing movie: {title} (TMDb ID: {tmdb_id})")
            
        return movie, created
        
    except KeyError as e:
        logger.error(f"❌ Missing key in TMDb data: {e} - Movie: {tmdb_data.get('title', 'Unknown')}")
        return None, False
    except ValueError as e:
        logger.error(f"❌ Data conversion error: {e} - Movie: {tmdb_data.get('title', 'Unknown')}")
        return None, False
    except Exception as e:
        logger.error(f"❌ Unexpected error in get_or_create_movie: {e} - Movie: {tmdb_data.get('title', 'Unknown')}")
        return None, False

def debug_movie_processing(tmdb_data):
    """Debug function to test movie processing"""
    logger.info(f"🔧 Debugging movie processing for: {tmdb_data.get('title', 'Unknown')}")
    
    # Test data extraction
    title = tmdb_data.get('title') or tmdb_data.get('original_title', 'Unknown Title')
    release_date = tmdb_data.get('release_date')
    genres = tmdb_data.get('genres') or tmdb_data.get('genre_ids', [])
    
    logger.info(f"📝 Extracted - Title: {title}, Release Date: {release_date}, Genres: {genres}")
    
    # Test the actual function
    return get_or_create_movie(tmdb_data)

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

def test_tmdb_connection():
    """Test TMDb API connection and movie processing"""
    logger.info("🧪 Testing TMDb API connection and movie processing...")
    
    # Test basic API connection
    test_movie = fetch_movies_from_tmdb('movie/550')  # Fight Club
    if not test_movie:
        logger.error("❌ TMDb API connection failed")
        return False
    
    logger.info(f"✅ TMDb API connected - Movie: {test_movie.get('title')}")
    
    # Test movie processing
    movie_obj, created = get_or_create_movie(test_movie)
    if movie_obj:
        logger.info(f"✅ Movie processing successful - Created: {created}")
        return True
    else:
        logger.error("❌ Movie processing failed")
        return False