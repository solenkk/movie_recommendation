# Movie Recommendation Backend

A Django REST API for movie recommendations with TMDb integration.

## Features

- User authentication and profile management
- Trending movie recommendations
- Movie search functionality
- Favorite movies tracking
- Redis caching for performance

## API Endpoints

- `GET /api/movies/trending/` - Get trending movies
- `GET /api/movies/search/?q=query` - Search movies
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Set environment variables in `.env` file
3. Run migrations: `python manage.py migrate`
4. Start server: `python manage.py runserver`

## Deployment

Deploy using Docker:
```bash
docker build -t movie-api .
docker run -p 8000:8000 movie-api
