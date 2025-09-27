from django.db import models

class Movie(models.Model):
    tmdb_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=255)
    overview = models.TextField(blank=True, null=True)
    release_date = models.DateField(blank=True, null=True)
    poster_path = models.CharField(max_length=500, blank=True, null=True)  # Increased length
    backdrop_path = models.CharField(max_length=500, blank=True, null=True)  # Increased length
    vote_average = models.FloatField(default=0.0)
    vote_count = models.IntegerField(default=0)
    genres = models.JSONField(blank=True, null=True)
    original_language = models.CharField(max_length=10, blank=True, null=True)
    popularity = models.FloatField(default=0.0)
    adult = models.BooleanField(default=False)
    video = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['tmdb_id']),
            models.Index(fields=['release_date']),
            models.Index(fields=['vote_average']),
        ]

    def __str__(self):
        return self.title

    @property
    def poster_url(self):
        if self.poster_path:
            return f"https://image.tmdb.org/t/p/w500{self.poster_path}"
        return None

    @property
    def backdrop_url(self):
        if self.backdrop_path:
            return f"https://image.tmdb.org/t/p/w1280{self.backdrop_path}"
        return None