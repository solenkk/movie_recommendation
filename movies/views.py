from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.core.cache import cache
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import logging

from .models import Movie
from .serializers import MovieSerializer
from .utils import fetch_movies_from_tmdb, get_or_create_movie, get_movie_credits, get_similar_movies
from users.models import UserProfile

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint for deployment monitoring"""
    return Response({
        'status': 'healthy',
        'service': 'Movie Recommendation API',
        'version': '1.0.0',
        'environment': 'development' if settings.DEBUG else 'production',
        'debug_mode': settings.DEBUG
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def get_trending_movies(request):
    """Get trending movies from TMDb with enhanced error handling"""
    cache_key = 'trending_movies'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        logger.info("Serving trending movies from cache")
        return Response(cached_data)
    
    try:
        logger.info("Fetching trending movies from TMDb API")
        data = fetch_movies_from_tmdb('trending/movie/week')
        
        if not data:
            logger.error("TMDb API returned no data")
            return Response(
                {'error': 'TMDb API returned no data', 'debug': 'API call failed completely'}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        if 'results' not in data:
            logger.error(f"TMDb API returned unexpected data structure: {list(data.keys())}")
            return Response(
                {'error': 'Unexpected data format from TMDb', 'debug': f"Keys: {list(data.keys())}"}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        if not data['results']:
            logger.warning("TMDb API returned empty results")
            return Response(
                {'error': 'No trending movies available', 'debug': 'Empty results array'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        logger.info(f"TMDb returned {len(data['results'])} movies, processing...")
        movies_data = []
        processed_count = 0
        failed_count = 0
        
        for index, movie_data in enumerate(data['results']):
            try:
                movie, created = get_or_create_movie(movie_data)
                if movie:
                    serializer = MovieSerializer(movie)
                    movies_data.append(serializer.data)
                    processed_count += 1
                else:
                    failed_count += 1
                    logger.warning(f"Failed to process movie {index}: {movie_data.get('title', 'Unknown')}")
            except Exception as e:
                failed_count += 1
                logger.error(f"Error processing movie {index}: {str(e)}")
        
        logger.info(f"Movie processing complete: {processed_count} success, {failed_count} failed")
        
        if not movies_data:
            logger.error(f"All movie processing failed. First movie sample: {data['results'][0] if data['results'] else 'No movies'}")
            return Response(
                {
                    'error': 'Movie processing failed', 
                    'debug': {
                        'total_movies': len(data['results']),
                        'processed': processed_count,
                        'failed': failed_count,
                        'sample_movie': data['results'][0] if data['results'] else None
                    }
                }, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Cache for 1 hour
        cache.set(cache_key, movies_data, timeout=3600)
        logger.info(f"Cached {len(movies_data)} trending movies successfully")
        
        return Response({
            'results': movies_data,
            'metadata': {
                'total_processed': processed_count,
                'total_failed': failed_count,
                'source': 'TMDb API',
                'cached': False
            }
        })
    
    except Exception as e:
        logger.error(f"Critical error in get_trending_movies: {str(e)}", exc_info=True)
        return Response(
            {'error': 'Internal server error', 'details': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def search_movies(request):
    """Search movies by query with enhanced error handling and pagination"""
    query = request.GET.get('q', '')
    page = request.GET.get('page', 1)
    
    if not query:
        return Response(
            {'error': 'Query parameter is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    cache_key = f'movie_search_{query}_page_{page}'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        logger.info(f"Serving search results for '{query}' page {page} from cache")
        return Response(cached_data)
    
    try:
        logger.info(f"Searching movies for query: '{query}', page: {page}")
        data = fetch_movies_from_tmdb('search/movie', {'query': query, 'page': page})
        
        if not data:
            logger.error(f"Search API returned no data for query: '{query}'")
            return Response(
                {'error': 'Search API unavailable'}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        if 'results' not in data:
            logger.error(f"Unexpected search response structure: {list(data.keys())}")
            return Response(
                {'error': 'Unexpected search response format'}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        movies_data = []
        for movie_data in data['results']:
            movie, created = get_or_create_movie(movie_data)
            if movie:
                serializer = MovieSerializer(movie)
                movies_data.append(serializer.data)
        
        response_data = {
            'results': movies_data,
            'total_results': data.get('total_results', 0),
            'total_pages': data.get('total_pages', 1),
            'current_page': int(page),
            'query': query
        }
        
        # Cache for 30 minutes
        cache.set(cache_key, response_data, timeout=1800)
        logger.info(f"Cached {len(movies_data)} search results for '{query}'")
        return Response(response_data)
    
    except Exception as e:
        logger.error(f"Error in search_movies: {str(e)}")
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def get_movie_details(request, movie_id):
    """Get detailed information about a specific movie"""
    cache_key = f'movie_details_{movie_id}'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        logger.info(f"Serving movie details for ID {movie_id} from cache")
        return Response(cached_data)
    
    try:
        logger.info(f"Fetching details for movie ID: {movie_id}")
        data = fetch_movies_from_tmdb(f'movie/{movie_id}')
        
        if not data:
            logger.error(f"Failed to fetch details for movie ID: {movie_id}")
            return Response(
                {'error': 'Movie details unavailable'}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        # Cache for 24 hours (movie details don't change often)
        cache.set(cache_key, data, timeout=86400)
        logger.info(f"Cached movie details for ID {movie_id}")
        return Response(data)
    
    except Exception as e:
        logger.error(f"Error in get_movie_details: {str(e)}")
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def get_movie_credits_view(request, movie_id):
    """Get cast and crew information for a movie"""
    cache_key = f'movie_credits_{movie_id}'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        logger.info(f"Serving movie credits for ID {movie_id} from cache")
        return Response(cached_data)
    
    try:
        data = get_movie_credits(movie_id)
        if not data:
            logger.error(f"Failed to fetch credits for movie ID: {movie_id}")
            return Response(
                {'error': 'Movie credits unavailable'}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        # Cache for 12 hours
        cache.set(cache_key, data, timeout=43200)
        logger.info(f"Cached movie credits for ID {movie_id}")
        return Response(data)
    
    except Exception as e:
        logger.error(f"Error in get_movie_credits: {str(e)}")
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def get_similar_movies_view(request, movie_id):
    """Get movies similar to the specified movie"""
    cache_key = f'similar_movies_{movie_id}'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        logger.info(f"Serving similar movies for ID {movie_id} from cache")
        return Response(cached_data)
    
    try:
        data = get_similar_movies(movie_id)
        if not data or 'results' not in data:
            logger.error(f"Failed to fetch similar movies for ID: {movie_id}")
            return Response(
                {'error': 'Similar movies unavailable'}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        movies_data = []
        for movie_data in data['results']:
            movie, created = get_or_create_movie(movie_data)
            if movie:
                serializer = MovieSerializer(movie)
                movies_data.append(serializer.data)
        
        response_data = {
            'results': movies_data,
            'total_results': data.get('total_results', 0),
            'total_pages': data.get('total_pages', 1)
        }
        
        # Cache for 6 hours
        cache.set(cache_key, response_data, timeout=21600)
        logger.info(f"Cached {len(movies_data)} similar movies for ID {movie_id}")
        return Response(response_data)
    
    except Exception as e:
        logger.error(f"Error in get_similar_movies: {str(e)}")
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def get_popular_movies(request):
    """Get popular movies from TMDb"""
    cache_key = 'popular_movies'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        logger.info("Serving popular movies from cache")
        return Response(cached_data)
    
    try:
        data = fetch_movies_from_tmdb('movie/popular')
        if data and 'results' in data:
            movies_data = []
            for movie_data in data['results']:
                movie, created = get_or_create_movie(movie_data)
                if movie:
                    serializer = MovieSerializer(movie)
                    movies_data.append(serializer.data)
            
            response_data = {
                'results': movies_data,
                'total_results': data.get('total_results', 0),
                'total_pages': data.get('total_pages', 1)
            }
            
            cache.set(cache_key, response_data, timeout=3600)
            logger.info(f"Cached {len(movies_data)} popular movies")
            return Response(response_data)
        
        return Response({'error': 'Failed to fetch popular movies'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    except Exception as e:
        logger.error(f"Error in get_popular_movies: {str(e)}")
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def get_top_rated_movies(request):
    """Get top rated movies from TMDb"""
    cache_key = 'top_rated_movies'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        logger.info("Serving top rated movies from cache")
        return Response(cached_data)
    
    try:
        data = fetch_movies_from_tmdb('movie/top_rated')
        if data and 'results' in data:
            movies_data = []
            for movie_data in data['results']:
                movie, created = get_or_create_movie(movie_data)
                if movie:
                    serializer = MovieSerializer(movie)
                    movies_data.append(serializer.data)
            
            response_data = {
                'results': movies_data,
                'total_results': data.get('total_results', 0),
                'total_pages': data.get('total_pages', 1)
            }
            
            cache.set(cache_key, response_data, timeout=3600)
            logger.info(f"Cached {len(movies_data)} top rated movies")
            return Response(response_data)
        
        return Response({'error': 'Failed to fetch top rated movies'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    except Exception as e:
        logger.error(f"Error in get_top_rated_movies: {str(e)}")
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def get_upcoming_movies(request):
    """Get upcoming movies from TMDb"""
    cache_key = 'upcoming_movies'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        logger.info("Serving upcoming movies from cache")
        return Response(cached_data)
    
    try:
        data = fetch_movies_from_tmdb('movie/upcoming')
        if data and 'results' in data:
            movies_data = []
            for movie_data in data['results']:
                movie, created = get_or_create_movie(movie_data)
                if movie:
                    serializer = MovieSerializer(movie)
                    movies_data.append(serializer.data)
            
            response_data = {
                'results': movies_data,
                'total_results': data.get('total_results', 0),
                'total_pages': data.get('total_pages', 1)
            }
            
            cache.set(cache_key, response_data, timeout=3600)
            logger.info(f"Cached {len(movies_data)} upcoming movies")
            return Response(response_data)
        
        return Response({'error': 'Failed to fetch upcoming movies'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    except Exception as e:
        logger.error(f"Error in get_upcoming_movies: {str(e)}")
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_favorite_movie(request, movie_id):
    """Add or remove movie from user's favorites"""
    try:
        movie = Movie.objects.get(tmdb_id=movie_id)
        user_profile = UserProfile.objects.get(user=request.user)
        
        if movie in user_profile.favorite_movies.all():
            user_profile.favorite_movies.remove(movie)
            action = 'removed'
            logger.info(f"User {request.user.username} removed movie {movie.title} from favorites")
        else:
            user_profile.favorite_movies.add(movie)
            action = 'added'
            logger.info(f"User {request.user.username} added movie {movie.title} to favorites")
        
        return Response({'status': f'Movie {action} to favorites'})
    
    except Movie.DoesNotExist:
        logger.warning(f"Movie with tmdb_id {movie_id} not found")
        return Response(
            {'error': 'Movie not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except UserProfile.DoesNotExist:
        logger.error(f"User profile not found for user {request.user.username}")
        return Response(
            {'error': 'User profile not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error in toggle_favorite_movie: {str(e)}")
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_favorite_movies(request):
    """Get user's favorite movies"""
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        favorite_movies = user_profile.favorite_movies.all()
        serializer = MovieSerializer(favorite_movies, many=True)
        logger.info(f"Retrieved {len(favorite_movies)} favorite movies for user {request.user.username}")
        return Response({
            'results': serializer.data,
            'total_count': favorite_movies.count()
        })
    
    except UserProfile.DoesNotExist:
        logger.error(f"User profile not found for user {request.user.username}")
        return Response(
            {'error': 'User profile not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error in get_favorite_movies: {str(e)}")
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def debug_tmdb_connection(request):
    """Debug endpoint to test TMDb API connection"""
    try:
        # Test basic movie endpoint
        test_data = fetch_movies_from_tmdb('movie/550')  # Fight Club
        basic_test = bool(test_data and test_data.get('title'))
        
        # Test trending endpoint
        trending_data = fetch_movies_from_tmdb('trending/movie/week')
        trending_test = bool(trending_data and 'results' in trending_data and trending_data['results'])
        
        return Response({
            'tmdb_connection': {
                'basic_test': 'SUCCESS' if basic_test else 'FAILED',
                'trending_test': 'SUCCESS' if trending_test else 'FAILED',
                'sample_movie': test_data.get('title') if basic_test else None,
                'trending_count': len(trending_data['results']) if trending_test else 0
            },
            'database': {
                'total_movies': Movie.objects.count(),
                'sample_movie': str(Movie.objects.first()) if Movie.objects.exists() else 'No movies'
            },
            'environment': {
                'debug': settings.DEBUG,
                'tmdb_api_key_set': bool(settings.TMDB_API_KEY),
                'cache_backend': settings.CACHES['default']['BACKEND']
            }
        })
    
    except Exception as e:
        return Response({'error': f'Debug failed: {str(e)}'}, status=500)