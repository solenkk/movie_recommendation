from rest_framework import serializers
from .models import Movie

class MovieSerializer(serializers.ModelSerializer):
    full_poster_url = serializers.ReadOnlyField()
    full_backdrop_url = serializers.ReadOnlyField()
    
    class Meta:
        model = Movie
        fields = [
            'id',
            'tmdb_id', 
            'title',
            'overview',
            'release_date',
            'poster_path',
            'backdrop_path',
            'vote_average',
            'vote_count',
            'genres',
            'created_at',
            'updated_at',
            'full_poster_url',
            'full_backdrop_url'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 
            'full_poster_url', 'full_backdrop_url'
        ]

class MovieSearchSerializer(serializers.Serializer):
    query = serializers.CharField(max_length=255, required=True)
    page = serializers.IntegerField(min_value=1, max_value=1000, default=1)

class MovieDetailSerializer(serializers.ModelSerializer):
    full_poster_url = serializers.ReadOnlyField()
    full_backdrop_url = serializers.ReadOnlyField()
    
    class Meta:
        model = Movie
        fields = [
            'id', 'tmdb_id', 'title', 'overview', 'release_date',
            'poster_path', 'backdrop_path', 'vote_average', 'vote_count',
            'genres', 'full_poster_url', 'full_backdrop_url'
        ]